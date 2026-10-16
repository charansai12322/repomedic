"""Tests for dependency manifest parsing and CVSS severity extraction (Fixes AUDIT-005, AUDIT-009)."""

import json
from pathlib import Path
from unittest.mock import patch
import requests
from repomedic.models.findings import Severity
from repomedic.models.health import ScannerStatus
from repomedic.scanners.dependencies import (
    DependencyScanner,
    extract_osv_severity,
    parse_package_lock_file,
    parse_requirements_file,
)


def test_parse_requirements_file_ranges_and_comments(temp_repo_dir: Path):
    """Verifies parsing of requirements with ranges, comments, and extras (Fixes AUDIT-005)."""
    content = """
# Production requirements
flask==2.0.1
requests>=2.25.0 # with comment
urllib3~=1.26.5; python_version >= '3.8'
cryptography[ssh]==3.4.7
"""
    req_file = temp_repo_dir / "requirements.txt"
    req_file.write_text(content, encoding="utf-8")

    parsed = parse_requirements_file(req_file, temp_repo_dir)
    names = {p["name"]: p["version"] for p in parsed}

    assert names.get("flask") == "2.0.1"
    assert names.get("requests") == "2.25.0"
    assert names.get("urllib3") == "1.26.5"
    assert names.get("cryptography") == "3.4.7"


def test_parse_package_lock_v1_and_v2(temp_repo_dir: Path):
    """Verifies that both lockfile v1 (dependencies) and v2/v3 (packages) are supported (Fixes AUDIT-005)."""
    # 1. Lockfile v1
    v1_data = {
        "name": "project",
        "version": "1.0.0",
        "lockfileVersion": 1,
        "dependencies": {
            "express": {"version": "4.17.1"},
            "lodash": {"version": "4.17.20"}
        }
    }
    v1_file = temp_repo_dir / "v1_lock.json"
    v1_file.write_text(json.dumps(v1_data), encoding="utf-8")
    parsed_v1 = parse_package_lock_file(v1_file, temp_repo_dir)
    v1_names = {p["name"]: p["version"] for p in parsed_v1}
    assert v1_names.get("express") == "4.17.1"
    assert v1_names.get("lodash") == "4.17.20"

    # 2. Lockfile v2/v3
    v2_data = {
        "name": "project",
        "version": "2.0.0",
        "lockfileVersion": 2,
        "packages": {
            "": {"name": "project", "version": "2.0.0"},
            "node_modules/axios": {"version": "0.21.1"},
            "node_modules/@scoped/pkg": {"version": "1.2.3"}
        }
    }
    v2_file = temp_repo_dir / "package-lock.json"
    v2_file.write_text(json.dumps(v2_data), encoding="utf-8")
    parsed_v2 = parse_package_lock_file(v2_file, temp_repo_dir)
    v2_names = {p["name"]: p["version"] for p in parsed_v2}
    assert v2_names.get("axios") == "0.21.1"
    assert v2_names.get("@scoped/pkg") == "1.2.3"


def test_monorepo_nested_manifest_discovery(temp_repo_dir: Path):
    """Verifies that manifests in subdirectories (monorepos) are recursively parsed (Fixes AUDIT-005)."""
    frontend_dir = temp_repo_dir / "frontend"
    frontend_dir.mkdir(parents=True)
    lock_data = {
        "packages": {
            "node_modules/react": {"version": "17.0.2"}
        }
    }
    (frontend_dir / "package-lock.json").write_text(json.dumps(lock_data), encoding="utf-8")

    scanner = DependencyScanner()
    with patch("requests.post") as mock_post:
        mock_post.return_value.json.return_value = {"results": []}
        mock_post.return_value.raise_for_status = lambda: None
        findings, health = scanner.scan(temp_repo_dir)
        # Verified that requests.post was called with react package
        called_queries = mock_post.call_args[1]["json"]["queries"]
        assert any(q["package"]["name"] == "react" for q in called_queries)


def test_cvss_severity_fallback_extraction():
    """Verifies that CVSS score is extracted when database_specific severity is absent (Fixes AUDIT-009)."""
    # 1. database_specific explicit
    assert extract_osv_severity({"database_specific": {"severity": "CRITICAL"}}) == Severity.CRITICAL
    assert extract_osv_severity({"database_specific": {"severity": "HIGH"}}) == Severity.HIGH

    # 2. CVSS vector score fallback
    cvss_crit = {"severity": [{"type": "CVSS_V3", "score": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H 9.8"}]}
    assert extract_osv_severity(cvss_crit) == Severity.CRITICAL

    cvss_high = {"severity": [{"type": "CVSS_V3", "score": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N 7.5"}]}
    assert extract_osv_severity(cvss_high) == Severity.HIGH

    cvss_med = {"severity": [{"type": "CVSS_V3", "score": "CVSS:3.1/AV:N/AC:H/PR:N/UI:R/S:U/C:L/I:L/A:N 5.0"}]}
    assert extract_osv_severity(cvss_med) == Severity.MEDIUM


def test_osv_network_failure_returns_health_failure(temp_repo_dir: Path):
    """When OSV API fails with network error, scanner records FAILED health state rather than silent empty."""
    (temp_repo_dir / "requirements.txt").write_text("flask==1.0.0\n", encoding="utf-8")
    scanner = DependencyScanner(required=True)

    with patch("requests.post", side_effect=requests.RequestException("Connection refused")):
        findings, health = scanner.scan(temp_repo_dir)
        assert health.status == ScannerStatus.FAILED
        assert health.error_code == "OSV_API_UNAVAILABLE"
        assert len(findings) == 0
