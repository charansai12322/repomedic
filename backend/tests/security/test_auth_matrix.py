"""Exhaustive authentication and authorization matrix tests (Phase 3B)."""

from unittest.mock import patch
from fastapi.testclient import TestClient
import pytest
from repomedic.api.app import app
from repomedic.config import settings

TEST_KEY = "test_secret_api_key_secure_12345"


@pytest.fixture
def client():
    return TestClient(app)


def test_public_probes_accessible_without_auth_in_production(client):
    """Liveness and readiness probes must remain accessible without API keys."""
    with patch.object(settings, "REPOMEDIC_ENV", "production"):
        with patch.object(settings, "REPOMEDIC_API_KEY", TEST_KEY):
            # Unversioned
            r_health = client.get("/health")
            assert r_health.status_code == 200
            assert r_health.json()["status"] == "ok"

            r_ready = client.get("/ready")
            assert r_ready.status_code == 200

            # Versioned /api/v1
            r_health_v1 = client.get("/api/v1/health")
            assert r_health_v1.status_code == 200

            r_ready_v1 = client.get("/api/v1/ready")
            assert r_ready_v1.status_code == 200


@pytest.mark.parametrize("endpoint,method", [
    ("/diagnostics", "GET"),
    ("/scan", "POST"),
    ("/jobs", "GET"),
    ("/jobs/test-nonexistent-job-id", "GET"),
    ("/jobs/test-nonexistent-job-id/cancel", "POST"),
    ("/jobs/test-nonexistent-job-id/report", "GET"),
    ("/benchmarks/summary", "GET"),
    ("/benchmarks/latest", "GET"),
    ("/api/v1/diagnostics", "GET"),
    ("/api/v1/scan", "POST"),
    ("/api/v1/jobs", "GET"),
    ("/api/v1/jobs/test-nonexistent-job-id", "GET"),
    ("/api/v1/jobs/test-nonexistent-job-id/cancel", "POST"),
    ("/api/v1/jobs/test-nonexistent-job-id/report", "GET"),
    ("/api/v1/benchmarks/summary", "GET"),
    ("/api/v1/benchmarks/latest", "GET"),
])
def test_protected_endpoints_fail_closed_without_auth_in_production(client, endpoint, method):
    """All protected operations must reject unauthenticated requests in production."""
    with patch.object(settings, "REPOMEDIC_ENV", "production"):
        with patch.object(settings, "REPOMEDIC_API_KEY", TEST_KEY):
            if method == "GET":
                resp = client.get(endpoint)
            else:
                resp = client.post(endpoint, json={"repo_url": "https://github.com/owner/repo"})

            assert resp.status_code == 401, f"{method} {endpoint} did not reject unauthenticated request"
            assert "Invalid or missing API key" in resp.text


def test_bearer_authorization_header_accepted(client):
    """Verifies that 'Authorization: Bearer <key>' is accepted as an alternative to 'X-API-Key'."""
    with patch.object(settings, "REPOMEDIC_ENV", "production"):
        with patch.object(settings, "REPOMEDIC_API_KEY", TEST_KEY):
            headers = {"Authorization": f"Bearer {TEST_KEY}"}
            resp = client.get("/diagnostics", headers=headers)
            assert resp.status_code == 200
            assert "limits" in resp.json()


def test_tampered_key_of_identical_length_rejected(client):
    """Constant-time comparison must reject tampered keys matching length."""
    with patch.object(settings, "REPOMEDIC_ENV", "production"):
        with patch.object(settings, "REPOMEDIC_API_KEY", TEST_KEY):
            tampered = TEST_KEY[:-1] + "X"
            resp = client.get("/diagnostics", headers={"X-API-Key": tampered})
            assert resp.status_code == 401


def test_diagnostics_never_returns_secret_keys(client):
    """Diagnostics endpoint must never expose the server API key or Groq credentials."""
    with patch.object(settings, "REPOMEDIC_ENV", "production"):
        with patch.object(settings, "REPOMEDIC_API_KEY", TEST_KEY):
            resp = client.get("/diagnostics", headers={"X-API-Key": TEST_KEY})
            assert resp.status_code == 200
            body = resp.text
            assert TEST_KEY not in body
            assert "gsk_" not in body
