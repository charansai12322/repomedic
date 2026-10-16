"""Read-only Git history scanner for detected secrets in historical commits."""

import hashlib
import os
import re
import subprocess
import time
from pathlib import Path
from typing import List, Optional, Tuple

from repomedic.core.sanitization import (
    SECRET_PATTERNS,
    is_placeholder,
    sanitize,
    truncate_line_safely,
)
from repomedic.logging_config import get_logger
from repomedic.models.findings import Confidence, EvidenceQuality, Finding, Severity
from repomedic.models.health import ScannerHealth, ScannerStatus
from repomedic.scanners.base import BaseScanner

logger = get_logger("git_history")

# Regex to parse hunk header: @@ -old_line,old_count +new_line,new_count @@
HUNK_HEADER_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
DIFF_FILE_RE = re.compile(r"^diff --git a/(.*?) b/(.*?)$")
COMMIT_RE = re.compile(r"^commit ([0-9a-fA-F]{7,40})")


class GitHistoryScanner(BaseScanner):
    """
    Scans recent Git commit history for secret credentials that were introduced
    in historical commits (even if later deleted in the working tree).
    Operates strictly read-only and never checks out, resets, or executes code.
    """

    def __init__(
        self,
        required: bool = False,
        enabled: bool = False,
        max_commits: int = 50,
        timeout_seconds: int = 30,
        max_output_bytes: int = 5_000_000,
    ):
        super().__init__(name="git_history", required=required)
        self.enabled = enabled
        self.max_commits = max_commits
        self.timeout_seconds = timeout_seconds
        self.max_output_bytes = max_output_bytes

    def _make_finding(
        self,
        rule_name: str,
        path: str,
        line: int,
        commit_sha: str,
        title: str,
        desc: str,
        snippet: str,
    ) -> Finding:
        rule_id = f"GIT_SECRET_{rule_name.upper()}"
        unique_key = f"{rule_id}|{path}|{commit_sha}|{line}"
        fid = hashlib.sha1(unique_key.encode("utf-8")).hexdigest()[:10]
        
        # Redact the snippet safely
        redacted_snippet = sanitize(truncate_line_safely(snippet, max_chars=1500))
        
        return Finding(
            id=f"F-{fid}",
            title=f"Historical Secret in Git Commit ({commit_sha[:8]}): {title}",
            description=(
                f"{desc} This secret was committed in historical git commit {commit_sha[:8]} "
                f"at {path}:{line}. Even if removed from the latest revision, committed secrets "
                f"remain permanently exposed in git history."
            ),
            severity=Severity.HIGH,
            confidence=Confidence.HIGH,
            source="git_history",
            evidence_quality=EvidenceQuality.DETERMINISTIC,
            rule_id=rule_id,
            file_path=path.replace("\\", "/").lstrip("/"),
            line_start=line,
            line_end=line,
            evidence=redacted_snippet,
            remediation=(
                "Immediately revoke and rotate this credential. Purge the sensitive commit from "
                "git history using tools such as git-filter-repo or BFG Repo-Cleaner, and ensure "
                "repository history is force-updated across all remotes."
            ),
            references=[f"commit:{commit_sha}", "https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository"],
        )

    def scan(self, repo_dir: Path) -> Tuple[List[Finding], ScannerHealth]:
        start_time = time.time()

        if not self.enabled:
            return [], ScannerHealth(
                name="git_history",
                status=ScannerStatus.SKIPPED,
                required=self.required,
                duration_ms=0,
                diagnostic_message="Git history scanning is disabled by default.",
            )

        # Check if repo_dir has a .git directory or is inside a work tree
        git_dir = repo_dir / ".git"
        if not git_dir.exists():
            duration_ms = int((time.time() - start_time) * 1000)
            return [], ScannerHealth(
                name="git_history",
                status=ScannerStatus.SKIPPED,
                required=self.required,
                duration_ms=duration_ms,
                diagnostic_message="Target directory is not a git repository (no .git found).",
            )

        # Safe environment without custom hooks
        safe_env = {
            **os.environ,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_TERMINAL_PROMPT": "0",
        }

        # Safe read-only git log command
        cmd = [
            "git",
            "-C",
            str(repo_dir),
            "-c",
            "core.hooksPath=/dev/null",
            "log",
            "-p",
            f"-n{self.max_commits}",
            "--diff-filter=d",
            "--unified=0",
        ]

        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                env=safe_env,
                check=False,
            )
        except subprocess.TimeoutExpired:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.warning(f"Git history scan timed out after {self.timeout_seconds}s on {repo_dir}")
            return [], ScannerHealth(
                name="git_history",
                status=ScannerStatus.FAILED,
                required=self.required,
                duration_ms=duration_ms,
                error_code="TIMEOUT",
                diagnostic_message=f"Git history scan exceeded {self.timeout_seconds}s timeout.",
            )
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Failed to execute git log: {e}")
            return [], ScannerHealth(
                name="git_history",
                status=ScannerStatus.FAILED,
                required=self.required,
                duration_ms=duration_ms,
                error_code="EXEC_ERROR",
                diagnostic_message="Failed to run git history inspection.",
            )

        if res.returncode != 0:
            duration_ms = int((time.time() - start_time) * 1000)
            err_msg = res.stderr.strip()[:200] if res.stderr else "Unknown git error"
            logger.warning(f"Git log returned non-zero code {res.returncode}: {err_msg}")
            # Could be an empty repo with no commits yet
            if "does not have any commits yet" in err_msg or "fatal: your current branch" in err_msg:
                return [], ScannerHealth(
                    name="git_history",
                    status=ScannerStatus.COMPLETED,
                    required=self.required,
                    duration_ms=duration_ms,
                    finding_count=0,
                    diagnostic_message="Git repository contains no commits yet.",
                )
            return [], ScannerHealth(
                name="git_history",
                status=ScannerStatus.FAILED,
                required=self.required,
                duration_ms=duration_ms,
                error_code=f"EXIT_{res.returncode}",
                diagnostic_message=f"Git log failed: {err_msg}",
            )

        diff_output = res.stdout
        if len(diff_output.encode("utf-8")) > self.max_output_bytes:
            diff_output = diff_output[: self.max_output_bytes]
            logger.warning(f"Git diff output exceeded {self.max_output_bytes} bytes; truncated.")

        findings: List[Finding] = []
        current_commit: Optional[str] = None
        current_file: Optional[str] = None
        current_new_line: int = 1

        for line in diff_output.splitlines():
            # Check for commit header
            commit_match = COMMIT_RE.match(line)
            if commit_match:
                current_commit = commit_match.group(1)
                continue

            # Check for diff file header
            file_match = DIFF_FILE_RE.match(line)
            if file_match:
                current_file = file_match.group(2)
                continue

            # Check for hunk header
            hunk_match = HUNK_HEADER_RE.match(line)
            if hunk_match:
                current_new_line = int(hunk_match.group(1))
                continue

            # Only analyze added lines (starts with '+' but not '+++')
            if line.startswith("+") and not line.startswith("+++"):
                added_content = line[1:]
                line_no = current_new_line
                current_new_line += 1

                if not current_commit or not current_file:
                    continue

                # Skip obvious lockfiles or minified files
                file_lower = current_file.lower()
                if file_lower.endswith((".lock", "-lock.json", ".min.js", ".min.css", ".map")):
                    continue

                # Test against secret patterns
                for pat_name, sev, pat, desc in SECRET_PATTERNS:
                    match = pat.search(added_content)
                    if match and not is_placeholder(match.group(0)):
                        findings.append(
                            self._make_finding(
                                rule_name=pat_name,
                                path=current_file,
                                line=line_no,
                                commit_sha=current_commit,
                                title=pat_name.replace("_", " ").title(),
                                desc=desc,
                                snippet=added_content,
                            )
                        )
            elif not line.startswith("-"):
                # Unchanged context line advances line counter
                current_new_line += 1

        duration_ms = int((time.time() - start_time) * 1000)
        return findings, ScannerHealth(
            name="git_history",
            status=ScannerStatus.COMPLETED,
            required=self.required,
            duration_ms=duration_ms,
            finding_count=len(findings),
        )
