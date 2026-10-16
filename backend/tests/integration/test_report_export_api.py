"""Integration tests for report export formats, benchmark endpoints, and job listing."""

import time
from pathlib import Path
from fastapi.testclient import TestClient
import pytest
from repomedic.api.app import app
from repomedic.models.findings import Confidence, EvidenceQuality, Finding, Severity
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
from repomedic.services.job_service import job_service


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def completed_test_job(monkeypatch):
    """Sets up a completed job with a report in job_service for test retrieval."""
    health = ScanHealthSummary(
        start_time="2026-10-14T12:00:00Z",
        finish_time="2026-10-14T12:00:01Z",
        total_duration_ms=1000,
        scanners={
            "custom_rules": ScannerHealth(
                name="custom_rules",
                status=ScannerStatus.COMPLETED,
                required=True,
                duration_ms=100,
                finding_count=1,
            )
        },
        audit_status=AuditStatus.COMPLETE,
        partial_audit=False,
    )
    finding = Finding(
        id="F-export-1",
        title="Hardcoded AWS Secret",
        description="Found AWS credential in source.",
        severity=Severity.HIGH,
        confidence=Confidence.HIGH,
        source="custom_rules",
        evidence_quality=EvidenceQuality.DETERMINISTIC,
        rule_id="SECRET_AWS_ACCESS_KEY",
        file_path="src/config.py",
        line_start=5,
        line_end=5,
        evidence="[REDACTED_AWS_ACCESS_KEY]",
    )
    score = SecurityScore(score=80, grade="B", penalty=20)
    evidence = ScanEvidenceSummary(files_scanned=2, findings=[finding])
    ai = AITriageResult(executive_summary="Executive summary test.")
    report = ScanReport(
        target="https://github.com/test-org/export-test-repo",
        scan_health=health,
        score=score,
        evidence=evidence,
        ai_triage=ai,
    )

    # Directly insert into job_service._jobs
    import uuid
    from datetime import datetime, timezone
    from repomedic.models.jobs import JobState, ScanJob
    job_id = f"test-export-{uuid.uuid4().hex[:8]}"
    job = ScanJob(
        job_id=job_id,
        target="https://github.com/test-org/export-test-repo",
        state=JobState.COMPLETED,
        created_at=datetime.now(timezone.utc).isoformat(),
        finished_at=datetime.now(timezone.utc).isoformat(),
        progress_percent=100,
        current_step="completed",
        report=report,
    )
    job_service._jobs[job_id] = job
    return job_id


@pytest.mark.parametrize("prefix", ["", "/api/v1"])
def test_export_sarif_endpoint(client, completed_test_job, prefix):
    res = client.get(f"{prefix}/jobs/{completed_test_job}/report?format=sarif")
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("application/sarif+json")
    assert "attachment" in res.headers.get("content-disposition", "")
    data = res.json()
    assert data["version"] == "2.1.0"
    assert len(data["runs"][0]["results"]) == 1
    assert data["runs"][0]["results"][0]["ruleId"] == "SECRET_AWS_ACCESS_KEY"


@pytest.mark.parametrize("prefix", ["", "/api/v1"])
def test_export_html_endpoint(client, completed_test_job, prefix):
    res = client.get(f"{prefix}/jobs/{completed_test_job}/report?format=html")
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/html")
    assert "<!DOCTYPE html>" in res.text
    assert "RepoMedic Security Audit" in res.text
    assert "Hardcoded AWS Secret" in res.text


@pytest.mark.parametrize("prefix", ["", "/api/v1"])
def test_export_json_endpoint(client, completed_test_job, prefix):
    res = client.get(f"{prefix}/jobs/{completed_test_job}/report?format=json")
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("application/json")
    data = res.json()
    assert data["target"] == "https://github.com/test-org/export-test-repo"
    assert data["partial_audit"] is False
    assert data["audit_status"] == "complete"


@pytest.mark.parametrize("prefix", ["", "/api/v1"])
def test_export_unsupported_format_returns_400(client, completed_test_job, prefix):
    res = client.get(f"{prefix}/jobs/{completed_test_job}/report?format=pdf")
    assert res.status_code == 400
    assert "Unsupported format" in res.json()["detail"]


@pytest.mark.parametrize("prefix", ["", "/api/v1"])
def test_list_jobs_endpoint(client, completed_test_job, prefix):
    res = client.get(f"{prefix}/jobs?limit=10")
    assert res.status_code == 200
    jobs = res.json()
    assert isinstance(jobs, list)
    assert any(j["job_id"] == completed_test_job for j in jobs)


@pytest.mark.parametrize("prefix", ["", "/api/v1"])
def test_benchmark_endpoints(client, prefix):
    # Benchmark latest
    res = client.get(f"{prefix}/benchmarks/latest")
    assert res.status_code == 200
    data = res.json()
    assert "total_fixtures" in data
    assert data["total_fixtures"] == 16

    # Benchmark summary
    res_sum = client.get(f"{prefix}/benchmarks/summary")
    assert res_sum.status_code == 200
    sum_data = res_sum.json()
    assert sum_data["total_fixtures"] == 16
    assert "precision" in sum_data
    assert "recall" in sum_data
    assert "false_positive_rate" in sum_data
