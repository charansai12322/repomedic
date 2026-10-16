"""Tests for scanner health contract and audit status state transitions (Workstream 4)."""

import pytest
from repomedic.models.health import (
    AuditStatus,
    ScanHealthSummary,
    ScannerHealth,
    ScannerStatus,
)


def test_complete_audit_all_required_scanners_pass():
    """When all required scanners complete, audit_status is 'complete' and partial_audit is False."""
    scanners = {
        "custom_rules": ScannerHealth(status=ScannerStatus.COMPLETED, required=True, duration_ms=100),
        "python_ast": ScannerHealth(status=ScannerStatus.COMPLETED, required=True, duration_ms=150),
        "osv": ScannerHealth(status=ScannerStatus.COMPLETED, required=True, duration_ms=300),
    }
    summary = ScanHealthSummary.compute_audit_status(
        scanners=scanners,
        start_time="2026-10-14T10:00:00Z",
        finish_time="2026-10-14T10:00:01Z",
        total_duration_ms=1000
    )
    assert summary.audit_status == AuditStatus.COMPLETE
    assert summary.partial_audit is False
    assert len(summary.degraded_reasons) == 0


def test_partial_audit_one_required_scanner_fails():
    """When a required scanner fails, audit_status is 'partial' and partial_audit is True."""
    scanners = {
        "custom_rules": ScannerHealth(status=ScannerStatus.COMPLETED, required=True, duration_ms=100),
        "python_ast": ScannerHealth(status=ScannerStatus.COMPLETED, required=True, duration_ms=150),
        "osv": ScannerHealth(
            status=ScannerStatus.FAILED,
            required=True,
            duration_ms=50,
            error_code="OSV_TIMEOUT",
            error_message="OSV API timed out"
        ),
    }
    summary = ScanHealthSummary.compute_audit_status(
        scanners=scanners,
        start_time="2026-10-14T10:00:00Z",
        finish_time="2026-10-14T10:00:01Z",
        total_duration_ms=1000
    )
    assert summary.audit_status == AuditStatus.PARTIAL
    assert summary.partial_audit is True
    assert any("Required scanner 'osv' failed" in r for r in summary.degraded_reasons)


def test_failed_audit_all_required_scanners_fail():
    """When all required scanners fail, audit_status is 'failed' and partial_audit is True."""
    scanners = {
        "custom_rules": ScannerHealth(status=ScannerStatus.FAILED, required=True, duration_ms=50),
        "python_ast": ScannerHealth(status=ScannerStatus.FAILED, required=True, duration_ms=50),
    }
    summary = ScanHealthSummary.compute_audit_status(
        scanners=scanners,
        start_time="2026-10-14T10:00:00Z",
        finish_time="2026-10-14T10:00:01Z",
        total_duration_ms=100
    )
    assert summary.audit_status == AuditStatus.FAILED
    assert summary.partial_audit is True


def test_optional_scanner_fails_audit_remains_complete():
    """When an optional scanner fails or is unavailable, the audit remains complete but notes degraded status."""
    scanners = {
        "custom_rules": ScannerHealth(status=ScannerStatus.COMPLETED, required=True, duration_ms=100),
        "python_ast": ScannerHealth(status=ScannerStatus.COMPLETED, required=True, duration_ms=150),
        "semgrep": ScannerHealth(
            status=ScannerStatus.UNAVAILABLE,
            required=False,
            duration_ms=0,
            error_code="SEMGREP_NOT_INSTALLED"
        ),
        "ai_triage": ScannerHealth(
            status=ScannerStatus.SKIPPED,
            required=False,
            duration_ms=0
        )
    }
    summary = ScanHealthSummary.compute_audit_status(
        scanners=scanners,
        start_time="2026-10-14T10:00:00Z",
        finish_time="2026-10-14T10:00:01Z",
        total_duration_ms=250
    )
    assert summary.audit_status == AuditStatus.COMPLETE
    assert summary.partial_audit is False
    assert any("semgrep" in r for r in summary.degraded_reasons)


def test_empty_findings_vs_failed_scanner():
    """Clean scan (zero findings) must have status completed, distinguishing it from failed status."""
    clean_scanner = ScannerHealth(status=ScannerStatus.COMPLETED, required=True, duration_ms=80, finding_count=0)
    failed_scanner = ScannerHealth(status=ScannerStatus.FAILED, required=True, duration_ms=20, error_code="CRASH")

    assert clean_scanner.status == ScannerStatus.COMPLETED
    assert clean_scanner.finding_count == 0

    assert failed_scanner.status == ScannerStatus.FAILED
    assert failed_scanner.error_code == "CRASH"
