"""Unit tests for SARIF 2.1.0 report exporter."""

import json
from repomedic.exports.sarif_export import (
    export_report_to_sarif_dict,
    export_report_to_sarif_json,
    finding_to_sarif_result,
)
from repomedic.models.findings import (
    Confidence,
    EvidenceQuality,
    Finding,
    Severity,
)
from repomedic.models.health import (
    AuditStatus,
    ScanHealthSummary,
    ScannerHealth,
    ScannerStatus,
)
from repomedic.models.reports import (
    AITriageResult,
    ScanEvidenceSummary,
    ScanReport,
    SecurityScore,
)


def _make_dummy_report(
    findings=None,
    audit_status=AuditStatus.COMPLETE,
    partial_audit=False,
) -> ScanReport:
    findings = findings or []
    scanners = {
        "custom_rules": ScannerHealth(
            name="custom_rules",
            status=ScannerStatus.COMPLETED,
            required=True,
            duration_ms=10,
            finding_count=len(findings),
        )
    }
    if partial_audit:
        scanners["osv"] = ScannerHealth(
            name="osv",
            status=ScannerStatus.FAILED,
            required=True,
            duration_ms=50,
            error_code="TIMEOUT",
        )

    health = ScanHealthSummary(
        start_time="2026-10-14T12:00:00Z",
        finish_time="2026-10-14T12:00:01Z",
        total_duration_ms=1000,
        scanners=scanners,
        audit_status=audit_status,
        partial_audit=partial_audit,
    )
    score = SecurityScore(score=85, grade="B", penalty=15)
    evidence = ScanEvidenceSummary(files_scanned=5, findings=findings)
    ai = AITriageResult(executive_summary="Audit completed.")
    return ScanReport(
        target="https://github.com/test/repo",
        scan_health=health,
        score=score,
        evidence=evidence,
        ai_triage=ai,
    )


def test_sarif_empty_findings_produces_valid_structure():
    report = _make_dummy_report(findings=[])
    sarif = export_report_to_sarif_dict(report)

    assert sarif["version"] == "2.1.0"
    assert "$schema" in sarif
    assert len(sarif["runs"]) == 1

    run = sarif["runs"][0]
    assert run["tool"]["driver"]["name"] == "RepoMedic"
    assert run["results"] == []
    assert run["invocations"][0]["executionSuccessful"] is True
    assert run["invocations"][0]["properties"]["partial_audit"] is False


def test_sarif_populated_findings_conversion():
    f = Finding(
        id="F-12345",
        title="Hardcoded AWS Key",
        description="AWS access key embedded in code.",
        severity=Severity.HIGH,
        confidence=Confidence.HIGH,
        source="custom_rules",
        evidence_quality=EvidenceQuality.DETERMINISTIC,
        rule_id="SECRET_AWS_ACCESS_KEY",
        file_path="src/config.py",
        line_start=15,
        line_end=15,
        evidence="AWS_KEY = '[REDACTED_AWS_ACCESS_KEY]'",
        remediation="Rotate key immediately.",
    )
    report = _make_dummy_report(findings=[f])
    sarif_str = export_report_to_sarif_json(report)
    sarif = json.loads(sarif_str)

    run = sarif["runs"][0]
    assert len(run["results"]) == 1
    res = run["results"][0]

    assert res["ruleId"] == "SECRET_AWS_ACCESS_KEY"
    assert res["level"] == "error"  # Severity.HIGH maps to "error"
    loc = res["locations"][0]["physicalLocation"]
    assert loc["artifactLocation"]["uri"] == "src/config.py"
    assert loc["region"]["startLine"] == 15
    assert loc["region"]["endLine"] == 15
    assert "[REDACTED_AWS_ACCESS_KEY]" in res["properties"]["sanitized_evidence"]


def test_sarif_partial_audit_marks_invocation_failed():
    report = _make_dummy_report(
        findings=[],
        audit_status=AuditStatus.PARTIAL,
        partial_audit=True,
    )
    sarif = export_report_to_sarif_dict(report)
    inv = sarif["runs"][0]["invocations"][0]

    assert inv["executionSuccessful"] is False
    assert inv["properties"]["partial_audit"] is True
    assert inv["properties"]["audit_status"] == "partial"
    assert inv["properties"]["scanners"]["osv"]["status"] == "failed"
