"""Semgrep static analysis subprocess runner with health reporting."""

import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import List, Tuple
from repomedic.models.findings import Confidence, EvidenceQuality, Finding, Severity
from repomedic.models.health import ScannerHealth, ScannerStatus
from repomedic.scanners.base import BaseScanner


def severity_from_semgrep(val: str) -> Severity:
    v = (val or "").upper()
    if v == "ERROR":
        return Severity.HIGH
    elif v == "WARNING":
        return Severity.MEDIUM
    elif v == "INFO":
        return Severity.LOW
    return Severity.MEDIUM


class SemgrepScanner(BaseScanner):
    """External Semgrep SAST subprocess runner."""

    def __init__(self, required: bool = False, timeout_seconds: int = 180):
        super().__init__(name="semgrep", required=required)
        self.timeout_seconds = timeout_seconds

    def scan(self, repo_dir: Path) -> Tuple[List[Finding], ScannerHealth]:
        t0 = time.time()
        semgrep_bin = shutil.which("semgrep")

        if not semgrep_bin:
            return [], ScannerHealth(
                status=ScannerStatus.UNAVAILABLE,
                required=self.required,
                duration_ms=0,
                error_code="SEMGREP_NOT_INSTALLED",
                error_message="Semgrep CLI executable not found in PATH; rule packs omitted.",
                finding_count=0
            )

        env = {
            **os.environ,
            "SEMGREP_SEND_METRICS": "off",
            "SEMGREP_ENABLE_VERSION_CHECK": "0"
        }

        cmd = [
            semgrep_bin, "scan",
            "--config", "p/security-audit",
            "--config", "p/secrets",
            "--json",
            "--quiet",
            "--metrics=off",
            "--timeout", "20",
            "--max-memory", "500",
            "--exclude", "node_modules",
            "--exclude", ".git",
            str(repo_dir)
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                env=env
            )
            payload = json.loads(result.stdout)

        except subprocess.TimeoutExpired:
            duration_ms = int((time.time() - t0) * 1000)
            return [], ScannerHealth(
                status=ScannerStatus.FAILED,
                required=self.required,
                duration_ms=duration_ms,
                error_code="SEMGREP_TIMEOUT",
                error_message=f"Semgrep scan timed out after {self.timeout_seconds} seconds.",
                finding_count=0
            )
        except (json.JSONDecodeError, OSError) as e:
            duration_ms = int((time.time() - t0) * 1000)
            return [], ScannerHealth(
                status=ScannerStatus.FAILED,
                required=self.required,
                duration_ms=duration_ms,
                error_code="SEMGREP_EXEC_ERROR",
                error_message=f"Semgrep failed to return valid JSON: {str(e)[:160]}",
                finding_count=0
            )

        findings: List[Finding] = []
        raw_results = payload.get("results", [])[:100]

        for item in raw_results:
            extra = item.get("extra", {})
            check_id = item.get("check_id", "unknown")
            raw_path = item.get("path", "unknown")
            try:
                rel = str(Path(raw_path).resolve().relative_to(Path(repo_dir).resolve())).replace("\\", "/")
            except Exception:
                rel = str(raw_path).replace("\\", "/")

            line = item.get("start", {}).get("line", 1)
            msg = (extra.get("message") or "Semgrep security rule matched.").strip()
            sev = severity_from_semgrep(extra.get("severity"))

            fid = hashlib.sha1(f"semgrep:{check_id}|{rel}|{line}".encode("utf-8")).hexdigest()[:10]
            findings.append(
                Finding(
                    id=f"F-{fid}",
                    title=f"Semgrep Rule Match: {check_id.split('.')[-1]}",
                    description=msg[:300],
                    severity=sev,
                    confidence=Confidence.HIGH,
                    source="semgrep",
                    evidence_quality=EvidenceQuality.DETERMINISTIC,
                    rule_id=f"semgrep:{check_id}",
                    file_path=rel,
                    line_start=line,
                    line_end=line,
                    evidence="[Source excerpt withheld; see file and line in repository.]",
                    remediation="Remediate according to Semgrep rule guidelines.",
                    references=[f"semgrep_rule:{check_id}"]
                )
            )

        duration_ms = int((time.time() - t0) * 1000)
        return findings, ScannerHealth(
            status=ScannerStatus.COMPLETED,
            required=self.required,
            duration_ms=duration_ms,
            finding_count=len(findings)
        )
