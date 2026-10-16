"""Tests for Semgrep integration and missing tool handling."""

import json
from pathlib import Path
import subprocess
from unittest.mock import patch
from repomedic.models.findings import Severity
from repomedic.models.health import ScannerStatus
from repomedic.scanners.semgrep import SemgrepScanner, severity_from_semgrep


def test_semgrep_missing_binary_returns_unavailable_health(temp_repo_dir: Path):
    """When Semgrep binary is not in PATH, scanner reports UNAVAILABLE status gracefully."""
    scanner = SemgrepScanner(required=False)

    with patch("shutil.which", return_value=None):
        findings, health = scanner.scan(temp_repo_dir)
        assert len(findings) == 0
        assert health.status == ScannerStatus.UNAVAILABLE
        assert health.error_code == "SEMGREP_NOT_INSTALLED"


def test_semgrep_timeout_returns_failed_health(temp_repo_dir: Path):
    """When Semgrep subprocess times out, scanner reports FAILED status with error code."""
    scanner = SemgrepScanner(required=True, timeout_seconds=1)

    with patch("shutil.which", return_value="/usr/bin/semgrep"):
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="semgrep", timeout=1)):
            findings, health = scanner.scan(temp_repo_dir)
            assert len(findings) == 0
            assert health.status == ScannerStatus.FAILED
            assert health.error_code == "SEMGREP_TIMEOUT"


def test_semgrep_parses_findings_cleanly(temp_repo_dir: Path):
    """Verifies that valid JSON output from Semgrep is parsed into canonical findings."""
    scanner = SemgrepScanner(required=False)
    dummy_payload = {
        "results": [
            {
                "check_id": "python.flask.security.audit.eval-detected",
                "path": str(temp_repo_dir / "app.py"),
                "start": {"line": 10},
                "extra": {
                    "severity": "ERROR",
                    "message": "Dangerous eval() call detected."
                }
            }
        ]
    }

    class DummyProc:
        stdout = json.dumps(dummy_payload)

    with patch("shutil.which", return_value="/usr/bin/semgrep"):
        with patch("subprocess.run", return_value=DummyProc()):
            findings, health = scanner.scan(temp_repo_dir)
            assert health.status == ScannerStatus.COMPLETED
            assert len(findings) == 1
            assert findings[0].rule_id == "semgrep:python.flask.security.audit.eval-detected"
            assert findings[0].severity == Severity.HIGH
            assert findings[0].line_start == 10


def test_severity_from_semgrep_mapping():
    assert severity_from_semgrep("ERROR") == Severity.HIGH
    assert severity_from_semgrep("WARNING") == Severity.MEDIUM
    assert severity_from_semgrep("INFO") == Severity.LOW
    assert severity_from_semgrep("UNKNOWN") == Severity.MEDIUM
