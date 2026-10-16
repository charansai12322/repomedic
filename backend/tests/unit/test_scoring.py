"""Tests for deterministic security scoring and per-package OSV capping (Fixes AUDIT-004)."""

from repomedic.core.scoring import compute_security_score
from repomedic.models.findings import Confidence, EvidenceQuality, Finding, Severity


def test_empty_findings_scores_100_grade_a():
    """A clean repository with zero findings receives a score of 100 and Grade A."""
    score = compute_security_score([])
    assert score.score == 100
    assert score.grade == "A"
    assert score.penalty == 0


def test_critical_finding_caps_grade_at_c():
    """Any critical finding clamps the maximum score at 69 (Grade C or lower)."""
    crit_finding = Finding(
        id="F-crit",
        title="AWS Key Committed",
        description="Access key",
        severity=Severity.CRITICAL,
        confidence=Confidence.HIGH,
        source="custom_rules",
        rule_id="secret:aws_access_key",
        file_path="config.py",
        line_start=1,
        line_end=1
    )
    score = compute_security_score([crit_finding])
    assert score.score <= 69
    assert score.grade in ("C", "D", "F")


def test_osv_per_package_capping_different_packages(temp_repo_dir):
    """
    Verifies that multiple vulnerabilities across DIFFERENT packages are capped PER PACKAGE,
    not globally collapsed to 5 total penalties (Fixes AUDIT-004).
    """
    # 5 CVEs in flask
    flask_findings = [
        Finding(
            id=f"F-flask-{i}",
            title="Flask CVE",
            description="desc",
            severity=Severity.HIGH,
            confidence=Confidence.HIGH,
            source="osv",
            rule_id=f"osv:GHSA-flask-{i}:flask",
            file_path="requirements.txt",
            line_start=1,
            line_end=1
        )
        for i in range(5)
    ]

    # 5 CVEs in requests
    requests_findings = [
        Finding(
            id=f"F-req-{i}",
            title="Requests CVE",
            description="desc",
            severity=Severity.HIGH,
            confidence=Confidence.HIGH,
            source="osv",
            rule_id=f"osv:GHSA-req-{i}:requests",
            file_path="requirements.txt",
            line_start=1,
            line_end=1
        )
        for i in range(5)
    ]

    score_flask_only = compute_security_score(flask_findings)
    score_both = compute_security_score(flask_findings + requests_findings)

    # 5 High findings = 5 * 8 = 40 penalty
    assert score_flask_only.penalty == 40

    # 5 High findings in flask + 5 High findings in requests = 40 + 40 = 80 penalty
    # (In the broken Phase 1 implementation, penalty remained 40 because both collapsed to "osv")
    assert score_both.penalty == 80, f"Expected penalty 80 across 2 packages, got {score_both.penalty}"
    assert score_both.score < score_flask_only.score


def test_osv_capping_single_package_exceeding_limit():
    """Verifies that more than 5 CVEs in the SAME package are capped at 5 penalties."""
    single_pkg_10_cves = [
        Finding(
            id=f"F-pkg-{i}",
            title="Package CVE",
            description="desc",
            severity=Severity.HIGH,
            confidence=Confidence.HIGH,
            source="osv",
            rule_id=f"osv:GHSA-test-{i}:vulnerable_package",
            file_path="requirements.txt",
            line_start=1,
            line_end=1
        )
        for i in range(10)
    ]

    score = compute_security_score(single_pkg_10_cves)
    # Capped at 5 * 8 = 40 penalty
    assert score.penalty == 40
