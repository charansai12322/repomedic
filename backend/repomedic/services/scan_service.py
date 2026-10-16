"""Scan execution service with hardened repository cloning and SSRF protection."""

import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
from typing import Optional
from repomedic.config import settings
from repomedic.core.orchestrator import ScannerOrchestrator
from repomedic.exceptions import (
    InvalidTargetError,
    ResourceLimitExceededError,
    ScanError,
)
from repomedic.logging_config import get_logger
from repomedic.models.health import ScannerHealth, ScannerStatus
from repomedic.models.reports import AITriageResult, ScanReport
from repomedic.ai.triage import AITriageEngine, BASE_LIMITATIONS

logger = get_logger("services.scan")

# Strict public GitHub repository regex
GITHUB_URL_REGEX = re.compile(
    r"^https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?$"
)

# SSRF and forbidden host patterns
FORBIDDEN_HOST_PATTERNS = [
    re.compile(r"^https?://(?:localhost|127\.|0\.0\.0\.0|10\.|172\.(?:1[6-9]|2[0-9]|3[01])\.|192\.168\.|169\.254\.)", re.I),
    re.compile(r"://.*@", re.I),  # Credential stuffing in URL (e.g. https://user:pass@evil.com)
]


def validate_repository_url(url: str) -> str:
    """Validates public GitHub URL and guards against SSRF, internal IPs, and scheme spoofing."""
    clean_url = (url or "").strip()

    for pattern in FORBIDDEN_HOST_PATTERNS:
        if pattern.search(clean_url):
            raise InvalidTargetError("Access to local, private network, or credentialed URLs is strictly forbidden.")

    m = GITHUB_URL_REGEX.match(clean_url)
    if not m:
        raise InvalidTargetError("Only public 'https://github.com/<owner>/<repo>' URLs are accepted.")

    owner, repo = m.group(1), m.group(2)
    return f"https://github.com/{owner}/{repo}.git"


def safe_cleanup_dir(dir_path: Optional[Path]) -> None:
    """Safely removes a temporary directory, retrying on Windows file locks."""
    if not dir_path or not dir_path.exists():
        return

    for attempt in range(3):
        try:
            shutil.rmtree(dir_path, ignore_errors=False)
            return
        except Exception:
            time.sleep(0.1 * (attempt + 1))
            shutil.rmtree(dir_path, ignore_errors=True)


class ScanService:
    """Executes hardened repository acquisition and drives orchestrator & AI triage."""

    def __init__(
        self,
        orchestrator: Optional[ScannerOrchestrator] = None,
        ai_triage_engine: Optional[AITriageEngine] = None
    ):
        self.orchestrator = orchestrator or ScannerOrchestrator()
        self.ai_triage = ai_triage_engine or AITriageEngine(required=settings.REPOMEDIC_AI_TRIAGE_REQUIRED)

    def execute_scan(
        self,
        target: str,
        local_dir: Optional[Path] = None,
        enable_git_history: Optional[bool] = None,
        enable_ai: bool = True,
        max_history_commits: Optional[int] = None,
    ) -> ScanReport:
        """
        Executes an end-to-end repository scan.
        If local_dir is provided (e.g. for testing/benchmarks), scans the directory directly without cloning.
        """
        cloned_root: Optional[Path] = None

        try:
            if local_dir is None:
                validated_url = validate_repository_url(target)
                repo_dir, cloned_root = self._hardened_clone(
                    validated_url,
                    enable_git_history=bool(enable_git_history),
                )
            else:
                repo_dir = Path(local_dir)
                if not repo_dir.exists() or not repo_dir.is_dir():
                    raise InvalidTargetError(f"Specified local directory does not exist: {local_dir}")

            # 1. Run deterministic scanners in parallel
            orchestrator = self.orchestrator
            if enable_git_history is not None or max_history_commits is not None:
                orchestrator = ScannerOrchestrator(
                    enable_git_history=enable_git_history,
                    max_history_commits=max_history_commits,
                )

            findings, health_summary, score, evidence_summary = orchestrator.run_all_scanners(repo_dir)

            # 2. Run AI triage (if enabled)
            if enable_ai and self.ai_triage:
                triage_result, ai_health = self.ai_triage.triage(findings, target)
            else:
                triage_result = AITriageResult(
                    executive_summary=f"Deterministic scan completed. Displaying {len(findings)} findings.",
                    diagnoses=[],
                    limitations=BASE_LIMITATIONS,
                    citation_validity_percent=100.0,
                    model="none (offline)",
                    mode="deterministic_only",
                    duration_ms=0,
                )
                ai_health = ScannerHealth(
                    status=ScannerStatus.SKIPPED,
                    required=False,
                    duration_ms=0,
                    error_code=None,
                    error_message="AI triage omitted by configuration or request.",
                    finding_count=0,
                )

            # 3. Incorporate AI triage health into overall scan health summary
            health_summary.scanners["ai_triage"] = ai_health

            # Re-evaluate audit completeness with AI triage included
            updated_health_summary = health_summary.compute_audit_status(
                scanners=health_summary.scanners,
                start_time=health_summary.start_time,
                finish_time=health_summary.finish_time,
                total_duration_ms=health_summary.total_duration_ms
            )

            report = ScanReport(
                target=target,
                scan_health=updated_health_summary,
                score=score,
                evidence=evidence_summary,
                ai_triage=triage_result
            )
            return report

        finally:
            if cloned_root:
                safe_cleanup_dir(cloned_root)

    def _hardened_clone(self, url: str, enable_git_history: bool = False) -> tuple[Path, Path]:
        """
        Executes a hardened shallow Git clone:
        - Disabled git hooks (core.hooksPath=/dev/null)
        - Disabled symlinks (core.symlinks=false)
        - Disabled terminal prompts (GIT_TERMINAL_PROMPT=0)
        - Depth 1 (or bounded history for git history scanning)
        - Size enforcement <= MAX_REPO_MB
        """
        root = Path(tempfile.mkdtemp(prefix="repomedic_clone_"))
        dest = root / "repo"
        env = {
            **os.environ,
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_LFS_SKIP_SMUDGE": "1"
        }

        cmd = [
            "git",
            "-c", "core.symlinks=false",
            "-c", "core.hooksPath=/dev/null",
            "clone",
            "--single-branch",
            "--no-tags",
        ]
        if not enable_git_history:
            cmd.extend(["--depth", "1"])
        cmd.extend(["--", url, str(dest)])

        try:
            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                timeout=120,
                env=env
            )
        except subprocess.CalledProcessError as e:
            safe_cleanup_dir(root)
            err_msg = e.stderr.strip()[:200] or "Git clone failed"
            raise ScanError(f"Failed to clone repository: {err_msg}")
        except subprocess.TimeoutExpired:
            safe_cleanup_dir(root)
            raise ScanError("Repository clone timed out after 120 seconds.")

        # Remove .git directory unless git history scanning was requested
        if not enable_git_history:
            shutil.rmtree(dest / ".git", ignore_errors=True)

        # Enforce repository size ceiling
        size_bytes = sum(p.stat().st_size for p in dest.rglob("*") if p.is_file() and not p.is_symlink())
        size_mb = size_bytes / 1_000_000.0

        if size_mb > settings.REPOMEDIC_MAX_REPO_MB:
            safe_cleanup_dir(root)
            raise ResourceLimitExceededError(
                f"Repository size ({size_mb:.1f} MB) exceeds maximum allowed threshold of {settings.REPOMEDIC_MAX_REPO_MB} MB."
            )

        return dest, root
