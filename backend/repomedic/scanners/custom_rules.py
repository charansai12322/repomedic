"""Custom pattern-based text scanner for secrets and risky code patterns."""

import hashlib
import os
import re
import time
from pathlib import Path
from typing import List, Tuple
from repomedic.core.sanitization import (
    SECRET_PATTERNS,
    is_placeholder,
    sanitize,
    truncate_line_safely,
)
from repomedic.models.findings import Confidence, EvidenceQuality, Finding, Severity
from repomedic.models.health import ScannerHealth, ScannerStatus
from repomedic.scanners.base import BaseScanner


SKIP_DIRS = {
    ".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build",
    "vendor", "site-packages", ".tox", ".mypy_cache", "target", ".next", "coverage"
}

TEXT_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".json", ".yml", ".yaml", ".toml", ".ini",
    ".cfg", ".env", ".sh", ".bash", ".rb", ".go", ".java", ".php", ".cs", ".rs",
    ".tf", ".txt", ".md", ".html", ".xml", ".properties", ".gradle", ".sql", ".conf",
    ".pem", ".key", ".crt", ".cert"
}

TEXT_NAMES = {"dockerfile", "makefile", ".env", ".npmrc", ".pypirc"}
IGNORED_FILENAMES = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock"}


def ext(*suffixes):
    return lambda p: p.lower().endswith(tuple(suffixes))


def named(*names):
    return lambda p: Path(p).name.lower() in names or Path(p).name.lower().startswith("dockerfile")


IS_PY = ext(".py")
IS_JS = ext(".js", ".jsx", ".ts", ".tsx")
IS_SHELLISH = lambda p: ext(".sh", ".bash", ".yml", ".yaml")(p) or named("makefile")(p)
IS_WORKFLOW = lambda p: p.startswith(".github/workflows/") and ext(".yml", ".yaml")(p)

CODE_PATTERNS = [
    ("weak_hash", Severity.MEDIUM, re.compile(r"\bhashlib\.(?:md5|sha1)\("), "MD5/SHA-1 is cryptographically weak; avoid for security purposes.", IS_PY),
    ("tls_verification_off", Severity.HIGH, re.compile(r"verify\s*=\s*False"), "TLS certificate verification disabled.", IS_PY),
    ("debug_mode_enabled", Severity.MEDIUM, re.compile(r"\.run\([^)]*debug\s*=\s*True"), "Framework debug mode enabled; can expose an interactive console.", IS_PY),
    ("sql_string_building", Severity.HIGH, re.compile(r"""\.execute(?:many)?\(\s*(?:f["']|["'][^"']*["']\s*(?:%|\+|\.format))"""), "SQL built with string formatting; use parameterized queries.", IS_PY),
    ("js_eval", Severity.HIGH, re.compile(r"\beval\s*\("), "eval() on dynamic input enables code injection.", IS_JS),
    ("unsafe_html_sink", Severity.MEDIUM, re.compile(r"\.innerHTML\s*=|dangerouslySetInnerHTML"), "Raw HTML sink; XSS risk if data is untrusted.", IS_JS),
    ("curl_pipe_shell", Severity.HIGH, re.compile(r"\b(?:curl|wget)\b[^|\n]*\|\s*(?:sudo\s+)?(?:ba|z)?sh\b"), "Remote script piped directly into a shell.", lambda p: IS_SHELLISH(p) or named()(p)),
    ("chmod_777", Severity.MEDIUM, re.compile(r"chmod\s+(?:-R\s+)?777"), "World-writable permissions.", lambda p: IS_SHELLISH(p) or named()(p)),
    ("bind_all_interfaces", Severity.LOW, re.compile(r"0\.0\.0\.0"), "Service bound to all network interfaces.", lambda p: IS_PY(p) or IS_JS(p)),
    ("gha_pull_request_target", Severity.HIGH, re.compile(r"\bpull_request_target\b"), "pull_request_target runs with secrets on untrusted PRs; a classic CI takeover vector.", IS_WORKFLOW),
    ("gha_unpinned_action", Severity.LOW, re.compile(r"uses:\s*[\w.-]+/[\w./-]+@(?![0-9a-f]{40}\b)\S+"), "Third-party action not pinned to a commit SHA (supply-chain risk).", IS_WORKFLOW),
]


class CustomRulesScanner(BaseScanner):
    """Deterministic regex scanner covering secrets and unsafe code patterns across multi-language files."""

    def __init__(self, required: bool = True, max_file_bytes: int = 400_000, max_files: int = 5000):
        super().__init__(name="custom_rules", required=required)
        self.max_file_bytes = max_file_bytes
        self.max_files = max_files

    def _make_finding(self, rule_id: str, severity: Severity, path: str, line: int, title: str, desc: str, snippet: str = "") -> Finding:
        fid = hashlib.sha1(f"{rule_id}|{path}|{line}".encode("utf-8")).hexdigest()[:10]
        return Finding(
            id=f"F-{fid}",
            title=title,
            description=desc,
            severity=severity,
            confidence=Confidence.HIGH,
            source="custom_rules",
            evidence_quality=EvidenceQuality.DETERMINISTIC,
            rule_id=rule_id,
            file_path=path,
            line_start=line,
            line_end=line,
            evidence=snippet,
            remediation="Review and remediate the flagged pattern according to project security guidelines."
        )

    def scan(self, repo_dir: Path) -> Tuple[List[Finding], ScannerHealth]:
        t0 = time.time()
        findings: List[Finding] = []
        files_count = 0

        try:
            for root, dirs, files in os.walk(repo_dir):
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
                for name in files:
                    file_path = Path(root) / name
                    if file_path.is_symlink():
                        continue
                    if not self._is_candidate(file_path):
                        continue
                    if file_path.stat().st_size > self.max_file_bytes:
                        continue

                    files_count += 1
                    if files_count > self.max_files:
                        break

                    try:
                        content = file_path.read_text(encoding="utf-8", errors="replace")
                    except OSError:
                        continue

                    rel_path = str(file_path.relative_to(repo_dir)).replace("\\", "/")
                    file_findings = self._scan_content(rel_path, content)
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
                error_code="CUSTOM_RULES_ERROR",
                error_message=str(e)[:200],
                finding_count=len(findings)
            )
            return findings, health

    def _is_candidate(self, p: Path) -> bool:
        name_lower = p.name.lower()
        if name_lower in IGNORED_FILENAMES:
            return False
        return (p.suffix.lower() in TEXT_EXTENSIONS or name_lower in TEXT_NAMES or name_lower.startswith("dockerfile"))

    def _scan_content(self, rel_path: str, content: str) -> List[Finding]:
        findings: List[Finding] = []
        name = Path(rel_path).name.lower()
        lines = content.splitlines()
        is_docs = rel_path.lower().endswith(".md")

        for lineno, raw_line in enumerate(lines, 1):
            line = truncate_line_safely(raw_line)

            # 1. Secret patterns
            for rule, sev, pat, msg in SECRET_PATTERNS:
                m = pat.search(line)
                if not m:
                    continue
                matched_val = m.group(0)
                if rule in ("hardcoded_secret_assignment", "bearer_token") and is_placeholder(matched_val):
                    continue

                sev_enum = Severity(sev)
                title = f"Hardcoded Secret ({rule.replace('_', ' ').title()})"
                findings.append(
                    self._make_finding(
                        rule_id=f"secret:{rule}",
                        severity=sev_enum,
                        path=rel_path,
                        line=lineno,
                        title=title,
                        desc=msg,
                        snippet=sanitize(line)
                    )
                )

            # Skip code patterns in documentation markdown
            if is_docs:
                continue

            # 2. Code patterns
            for rule, sev, pat, msg, scope in CODE_PATTERNS:
                if scope(rel_path) and pat.search(line):
                    title = f"Risky Code Pattern ({rule.replace('_', ' ').title()})"
                    findings.append(
                        self._make_finding(
                            rule_id=rule,
                            severity=sev,
                            path=rel_path,
                            line=lineno,
                            title=title,
                            desc=msg,
                            snippet=sanitize(line)
                        )
                    )

        # 3. Dockerfile specific checks
        if name.startswith("dockerfile"):
            has_user = any(re.match(r"\s*USER\s+(?!root\b)\S+", l, re.I) for l in lines)
            if not has_user:
                findings.append(
                    self._make_finding(
                        rule_id="docker_runs_as_root",
                        severity=Severity.MEDIUM,
                        path=rel_path,
                        line=1,
                        title="Docker Container Runs As Root",
                        desc="Container runs as root (no non-root USER instruction specified).",
                        snippet="USER root / (missing USER instruction)"
                    )
                )
            for i, l in enumerate(lines, 1):
                if re.match(r"\s*FROM\s+\S+:latest\b", l, re.I):
                    findings.append(
                        self._make_finding(
                            rule_id="docker_latest_tag",
                            severity=Severity.LOW,
                            path=rel_path,
                            line=i,
                            title="Docker Base Image Uses Mutable Latest Tag",
                            desc="Base image uses the mutable :latest tag.",
                            snippet=sanitize(l)
                        )
                    )

        return findings
