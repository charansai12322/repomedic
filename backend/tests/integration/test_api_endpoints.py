"""Integration tests for FastAPI endpoints and job lifecycle."""

import asyncio
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
import pytest
from repomedic.api.app import app
from repomedic.services.job_service import job_service


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "RepoMedic"
    assert "version" in data


def test_ready_endpoint(client):
    resp = client.get("/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ready"
    assert "scanners" in data
    assert "ai_inference" in data


def test_diagnostics_endpoint(client):
    resp = client.get("/diagnostics")
    assert resp.status_code == 200
    data = resp.json()
    assert "tools" in data
    assert "ai_discovery" in data
    assert "limits" in data
    assert data["limits"]["max_concurrent_scans"] >= 1


def test_invalid_repo_url_returns_400(client):
    resp = client.post("/scan", json={"repo_url": "http://localhost:8000/evil"})
    assert resp.status_code == 400
    data = resp.json()
    assert data["error"] == "INVALID_TARGET_URL"


def test_job_submission_and_lifecycle(client, temp_repo_dir: Path):
    """Submits a local directory scan via job service and polls report from API."""
    (temp_repo_dir / "main.py").write_text("import os\nos.system('whoami')", encoding="utf-8")

    with patch("shutil.which", return_value=None):
        # Directly enqueue local dir job
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        job_resp = loop.run_until_complete(
            job_service.submit_job("local://test-job-repo", local_dir=temp_repo_dir, enable_ai=False)
        )
        job_id = job_resp.job_id

        # Poll status via API
        status_resp = client.get(f"/jobs/{job_id}")
        assert status_resp.status_code == 200
        status_data = status_resp.json()
        assert status_data["job_id"] == job_id
        assert status_data["state"] in ("queued", "running", "completed")

        # Wait for worker to conclude local scan
        for _ in range(50):
            check_resp = client.get(f"/jobs/{job_id}")
            if check_resp.json()["state"] in ("completed", "partial", "failed"):
                break
            loop.run_until_complete(asyncio.sleep(0.1))

        assert check_resp.json()["state"] in ("completed", "partial")

        # Retrieve report
        report_resp = client.get(f"/jobs/{job_id}/report")
        assert report_resp.status_code == 200
        report_data = report_resp.json()
        assert report_data["target"] == "local://test-job-repo"
        assert "scan_health" in report_data
        assert "score" in report_data
        assert "evidence" in report_data
