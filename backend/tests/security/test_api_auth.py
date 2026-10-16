"""Tests for API authentication enforcement."""

from fastapi.testclient import TestClient
import pytest
from repomedic.api.app import create_app
from repomedic.config import settings


@pytest.fixture
def client_with_auth(monkeypatch):
    monkeypatch.setattr(settings, "REPOMEDIC_ENV", "production")
    monkeypatch.setattr(settings, "REPOMEDIC_API_KEY", "super-secret-test-key")
    app = create_app()
    return TestClient(app)


def test_production_request_without_key_rejected(client_with_auth):
    """In production mode, unauthenticated scan requests must return 401."""
    resp = client_with_auth.post("/scan", json={"repo_url": "https://github.com/owner/repo"})
    assert resp.status_code == 401
    assert "Invalid or missing API key" in resp.json()["detail"]


def test_production_request_with_invalid_key_rejected(client_with_auth):
    """In production mode, requests with incorrect API key return 401."""
    headers = {"X-API-Key": "wrong-key"}
    resp = client_with_auth.post("/scan", json={"repo_url": "https://github.com/owner/repo"}, headers=headers)
    assert resp.status_code == 401


def test_production_request_with_valid_key_accepted(client_with_auth):
    """In production mode, requests with correct API key are accepted with 202."""
    headers = {"X-API-Key": "super-secret-test-key"}
    resp = client_with_auth.post("/scan", json={"repo_url": "https://github.com/owner/repo"}, headers=headers)
    assert resp.status_code == 202
    assert "job_id" in resp.json()
