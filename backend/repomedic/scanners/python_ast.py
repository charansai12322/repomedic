"""Python AST-based scanner with comprehensive import alias tracking (Fixes AUDIT-002)."""

import ast
import hashlib
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from repomedic.core.sanitization import sanitize
from repomedic.models.findings import Confidence, EvidenceQuality, Finding, Severity
from repomedic.models.health import ScannerHealth, ScannerStatus
from repomedic.scanners.base import BaseScanner


SKIP_DIRS = {
    ".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build",
    "vendor", "site-packages", ".tox", ".mypy_cache"
}


class AliasResolvingVisitor(ast.NodeVisitor):
    """
    AST visitor that first builds an alias lookup table for imports,
    then inspects Call nodes with fully resolved module and function identities.
    """

    def __init__(self, rel_path: str, lines: List[str]):
        self.rel_path = rel_path
        self.lines = lines
        self.aliases: Dict[str, str] = {}
        self.findings: List[Finding] = []

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            local_name = alias.asname or alias.name
            self.aliases[local_name] = alias.name
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        for alias in node.names:
            local_name = alias.asname or alias.name
            target = f"{module}.{alias.name}" if module else alias.name
            self.aliases[local_name] = target
        self.generic_visit(node)

    def _resolve_callable(self, node: ast.AST) -> str:
        """Resolves an AST call target to its canonical imported name."""
        if isinstance(node, ast.Name):
            return self.aliases.get(node.id, node.id)
        if isinstance(node, ast.Attribute):
            base = self._resolve_callable(node.value)
            return f"{base}.{node.attr}" if base else node.attr
        return ""

    def _make_finding(self, rule_id: str, severity: Severity, lineno: int, title: str, desc: str, snippet: str = "") -> Finding:
        fid = hashlib.sha1(f"{rule_id}|{self.rel_path}|{lineno}".encode("utf-8")).hexdigest()[:10]
        return Finding(
            id=f"F-{fid}",
            title=title,
            description=desc,
            severity=severity,
            confidence=Confidence.HIGH,
            source="python_ast",
            evidence_quality=EvidenceQuality.DETERMINISTIC,
            rule_id=rule_id,
            file_path=self.rel_path,
            line_start=lineno,
            line_end=lineno,
            evidence=snippet,
            remediation="Refactor code to avoid dynamic code execution or insecure function invocations."
        )

    def visit_Call(self, node: ast.Call) -> None:
        fn = self._resolve_callable(node.func)
        lineno = getattr(node, "lineno", 1)
        snippet = sanitize(self.lines[lineno - 1]) if 0 < lineno <= len(self.lines) else ""
        kw = {k.arg: k.value for k in node.keywords if k.arg}

        if fn in ("eval", "exec"):
            self.findings.append(
                self._make_finding(
                    rule_id="py_eval_exec",
                    severity=Severity.HIGH,
                    lineno=lineno,
                    title="Dynamic Code Execution (eval/exec)",
                    desc=f"{fn}() can execute attacker-controlled code dynamically.",
                    snippet=snippet
                )
            )

        elif fn == "os.system":
            self.findings.append(
                self._make_finding(
                    rule_id="py_os_system",
                    severity=Severity.HIGH,
                    lineno=lineno,
                    title="Command Injection Vector (os.system)",
                    desc="os.system() runs a shell command; prefer subprocess with an argument list and shell=False.",
                    snippet=snippet
                )
            )

        elif fn.startswith("subprocess.") or fn in ("subprocess.run", "subprocess.Popen", "subprocess.call", "subprocess.check_call", "subprocess.check_output"):
            shell_arg = kw.get("shell")
            is_shell_true = isinstance(shell_arg, ast.Constant) and shell_arg.value is True

            if is_shell_true:
                self.findings.append(
                    self._make_finding(
                        rule_id="py_subprocess_shell",
                        severity=Severity.HIGH,
                        lineno=lineno,
                        title="Subprocess With Shell True",
                        desc="subprocess invocation with shell=True allows command injection if arguments are untrusted.",
                        snippet=snippet
                    )
                )

        elif fn in ("pickle.load", "pickle.loads", "marshal.loads", "cPickle.loads", "_pickle.loads"):
            self.findings.append(
                self._make_finding(
                    rule_id="py_unsafe_deserialization",
                    severity=Severity.HIGH,
                    lineno=lineno,
                    title="Insecure Deserialization (pickle/marshal)",
                    desc=f"{fn}() on untrusted data allows arbitrary remote code execution.",
                    snippet=snippet
                )
            )

        elif fn in ("yaml.load", "yaml.unsafe_load"):
            has_safe_loader = False
            loader = kw.get("Loader")
            if loader and isinstance(loader, (ast.Name, ast.Attribute)):
                loader_name = getattr(loader, "id", "") or getattr(loader, "attr", "")
                if "Safe" in loader_name or "CSafe" in loader_name:
                    has_safe_loader = True

            if not has_safe_loader and len(node.args) < 2:
                self.findings.append(
                    self._make_finding(
                        rule_id="py_yaml_unsafe_load",
                        severity=Severity.HIGH,
                        lineno=lineno,
                        title="Insecure YAML Deserialization (yaml.load)",
                        desc="yaml.load() without a SafeLoader allows code execution; use yaml.safe_load().",
                        snippet=snippet
                    )
                )

        elif fn in ("tempfile.mktemp",):
            self.findings.append(
                self._make_finding(
                    rule_id="py_insecure_tempfile",
                    severity=Severity.MEDIUM,
                    lineno=lineno,
                    title="Insecure Temporary File Creation (mktemp)",
                    desc="tempfile.mktemp() is vulnerable to race conditions (TOCTOU); use tempfile.mkstemp().",
                    snippet=snippet
                )
            )

        self.generic_visit(node)


class PythonASTScanner(BaseScanner):
    """AST-driven security scanner for Python source code with alias tracking."""

    def __init__(self, required: bool = True, max_file_bytes: int = 400_000):
        super().__init__(name="python_ast", required=required)
        self.max_file_bytes = max_file_bytes

    def scan(self, repo_dir: Path) -> Tuple[List[Finding], ScannerHealth]:
        t0 = time.time()
        findings: List[Finding] = []

        try:
            for root, dirs, files in os.walk(repo_dir):
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
                for name in files:
                    if not name.endswith(".py"):
                        continue
                    file_path = Path(root) / name
                    if file_path.is_symlink():
                        continue
                    if file_path.stat().st_size > self.max_file_bytes:
                        continue

                    try:
                        content = file_path.read_text(encoding="utf-8", errors="replace")
                    except OSError:
                        continue

                    rel_path = str(file_path.relative_to(repo_dir)).replace("\\", "/")
                    file_findings = self._scan_python_file(rel_path, content)
                    findings.extend(file_findings)

            duration_ms = int((time.time() - t0) * 1000)
            health = ScannerHealth(
                status=ScannerStatus.COMPLETED,
                required=self.required,
                duration_ms=duration_ms,
                finding_count=len(findings)
            )
            return findings, health

        except Exception as e:
            duration_ms = int((time.time() - t0) * 1000)
            health = ScannerHealth(
                status=ScannerStatus.FAILED,
                required=self.required,
                duration_ms=duration_ms,
                error_code="AST_SCANNER_ERROR",
                error_message=str(e)[:200],
                finding_count=len(findings)
            )
            return findings, health

    def _scan_python_file(self, rel_path: str, content: str) -> List[Finding]:
        try:
            tree = ast.parse(content)
        except (SyntaxError, ValueError, RecursionError, MemoryError):
            return []

        lines = content.splitlines()
        visitor = AliasResolvingVisitor(rel_path, lines)
        visitor.visit(tree)
        return visitor.findings
