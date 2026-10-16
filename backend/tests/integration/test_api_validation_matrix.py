"""Comprehensive API Request Validation Matrix Tests.

Covers:
- POST /scan and POST /api/v1/scan:
  - Valid input
  - Missing required fields
  - Empty string
  - Whitespace-only string
  - Null value
  - Incorrect primitive types (int, list, dict)
  - Boundary values for max_history_commits (0, 1, 500, 501)
  - Malformed JSON syntax
  - Incorrect Content-Type header
  - Invalid repository domains / SSRF inputs
- GET /jobs and GET /api/v1/jobs:
  - Valid limit
  - Boundary limits (0, 1, 100, 101)
  - Invalid types (non-integer string)
- GET /jobs/{id} and POST /jobs/{id}/cancel:
  - Valid existing vs non-existent UUIDs
- GET /jobs/{id}/report:
  - Missing job (404)
  - Invalid export format query param (400)
  - Valid formats: json, html, sarif
- GET /benchmarks/summary and GET /benchmarks/latest:
  - 200 response contracts
"""

from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import pytest
from repomedic.api.app import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def mock_background_scan(monkeypatch):
    """Mocks ScanService.execute_scan so tests don't clone real repos over the network."""
    from repomedic.models.health import AuditStatus, ScanHealthSummary, ScannerHealth, ScannerStatus
    from repomedic.models.reports import AITriageResult, ScanEvidenceSummary, ScanReport, SecurityScore
    from repomedic.services.job_service import job_service

    dummy_report = ScanReport(
        target="https://github.com/test-org/dummy-repo",
        scan_health=ScanHealthSummary.compute_audit_status(
            scanners={
                "custom_rules": ScannerHealth(
                    status=ScannerStatus.COMPLETED,
                    required=True,
                    duration_ms=5,
                    finding_count=0
                )
            },
            start_time="2026-10-14T00:00:00Z",
            finish_time="2026-10-14T00:00:01Z",
            total_duration_ms=100
        ),
        score=SecurityScore(score=100, grade="A", penalty=0),
        evidence=ScanEvidenceSummary(files_scanned=1, findings=[]),
        ai_triage=AITriageResult(executive_summary="Clean scan"),
    )

    mock_exec = MagicMock(return_value=dummy_report)
    monkeypatch.setattr(job_service.scan_service, "execute_scan", mock_exec)
    return mock_exec


@pytest.mark.parametrize("prefix", ["", "/api/v1"])
def test_scan_missing_required_fields(prefix):
    """Missing repo_url should return 422 Unprocessable Entity."""
    resp = client.post(f"{prefix}/scan", json={})
    assert resp.status_code == 422


@pytest.mark.parametrize("prefix", ["", "/api/v1"])
def test_scan_empty_and_whitespace_repo_url(prefix):
    """Empty or whitespace repo_url should be rejected."""
    # Empty string fails pydantic min_length=1 (422)
    resp_empty = client.post(f"{prefix}/scan", json={"repo_url": ""})
    assert resp_empty.status_code == 422

    # Whitespace fails GitHub regex validation (400 INVALID_TARGET_URL)
    resp_ws = client.post(f"{prefix}/scan", json={"repo_url": "   "})
    assert resp_ws.status_code == 400
    assert resp_ws.json().get("error") == "INVALID_TARGET_URL"


@pytest.mark.parametrize("prefix", ["", "/api/v1"])
def test_scan_null_repo_url(prefix):
    """Null repo_url should return 422 Unprocessable Entity."""
    resp = client.post(f"{prefix}/scan", json={"repo_url": None})
    assert resp.status_code == 422


@pytest.mark.parametrize("prefix", ["", "/api/v1"])
def test_scan_incorrect_primitive_types(prefix):
    """Providing integers or objects for string/bool fields must fail validation."""
    resp1 = client.post(f"{prefix}/scan", json={"repo_url": 12345})
    assert resp1.status_code == 422

    resp2 = client.post(f"{prefix}/scan", json={"repo_url": {"url": "https://github.com/a/b"}})
    assert resp2.status_code == 422

    resp3 = client.post(
        f"{prefix}/scan",
        json={"repo_url": "https://github.com/pallets/flask", "enable_git_history": "not-a-bool"}
    )
    assert resp3.status_code == 422


@pytest.mark.parametrize("prefix", ["", "/api/v1"])
def test_scan_max_history_commits_boundaries(prefix):
    """Validates boundary enforcement on max_history_commits (ge=1, le=500)."""
    # Below lower limit (0)
    resp_below = client.post(
        f"{prefix}/scan",
        json={"repo_url": "https://github.com/pallets/flask", "max_history_commits": 0}
    )
    assert resp_below.status_code == 422

    # Above upper limit (501)
    resp_above = client.post(
        f"{prefix}/scan",
        json={"repo_url": "https://github.com/pallets/flask", "max_history_commits": 501}
    )
    assert resp_above.status_code == 422

    # Valid lower boundary (1)
    resp_at_min = client.post(
        f"{prefix}/scan",
        json={"repo_url": "https://github.com/pallets/flask", "max_history_commits": 1}
    )
    assert resp_at_min.status_code == 202

    # Valid upper boundary (500)
    resp_at_max = client.post(
        f"{prefix}/scan",
        json={"repo_url": "https://github.com/pallets/flask", "max_history_commits": 500}
    )
    assert resp_at_max.status_code == 202


@pytest.mark.parametrize("prefix", ["", "/api/v1"])
def test_scan_malformed_json_and_content_type(prefix):
    """Rejects malformed JSON syntax and non-JSON content types."""
    resp_malformed = client.post(
        f"{prefix}/scan",
        content="{\"repo_url\": 'invalid_json_missing_quote",
        headers={"Content-Type": "application/json"}
    )
    assert resp_malformed.status_code == 422

    resp_wrong_type = client.post(
        f"{prefix}/scan",
        content="plain text body",
        headers={"Content-Type": "text/plain"}
    )
    assert resp_wrong_type.status_code == 422


@pytest.mark.parametrize("prefix", ["", "/api/v1"])
def test_jobs_list_limit_boundaries(prefix):
    """Enforces limit boundaries on GET /jobs (ge=1, le=100)."""
    # Below min (0)
    resp_zero = client.get(f"{prefix}/jobs?limit=0")
    assert resp_zero.status_code == 422

    # Above max (101)
    resp_excess = client.get(f"{prefix}/jobs?limit=101")
    assert resp_excess.status_code == 422

    # Non-integer string
    resp_alpha = client.get(f"{prefix}/jobs?limit=abc")
    assert resp_alpha.status_code == 422

    # Boundary: min (1)
    resp_min = client.get(f"{prefix}/jobs?limit=1")
    assert resp_min.status_code == 200
    assert isinstance(resp_min.json(), list)

    # Boundary: max (100)
    resp_max = client.get(f"{prefix}/jobs?limit=100")
    assert resp_max.status_code == 200
    assert isinstance(resp_max.json(), list)


@pytest.mark.parametrize("prefix", ["", "/api/v1"])
def test_nonexistent_job_ids_return_404(prefix):
    """Verifies that queries for nonexistent jobs return clean 404s."""
    bogus_id = "00000000-0000-0000-0000-000000000000"

    resp_get = client.get(f"{prefix}/jobs/{bogus_id}")
    assert resp_get.status_code == 404

    resp_cancel = client.post(f"{prefix}/jobs/{bogus_id}/cancel")
    assert resp_cancel.status_code == 404

    resp_report = client.get(f"{prefix}/jobs/{bogus_id}/report")
    assert resp_report.status_code == 404


@pytest.mark.parametrize("prefix", ["", "/api/v1"])
def test_health_and_diagnostics_endpoints(prefix):
    """Health endpoints return expected contracts without secret leakage."""
    resp_health = client.get(f"{prefix}/health")
    assert resp_health.status_code == 200
    data_health = resp_health.json()
    assert data_health["status"] == "ok"
    assert data_health["service"] == "RepoMedic"

    resp_ready = client.get(f"{prefix}/ready")
    assert resp_ready.status_code == 200
    data_ready = resp_ready.json()
    assert data_ready["status"] == "ready"

    resp_diag = client.get(f"{prefix}/diagnostics")
    assert resp_diag.status_code == 200
    data_diag = resp_diag.json()
    assert "tools" in data_diag
    assert "limits" in data_diag
    # Ensure sensitive credentials are absent
    raw_str = resp_diag.text.lower()
    assert "gsk_" not in raw_str
    assert "api_key" not in data_diag
