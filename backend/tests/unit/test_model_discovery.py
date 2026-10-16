"""Tests for Groq model discovery and caching (Workstream 7)."""

from unittest.mock import MagicMock, patch
from repomedic.ai.model_discovery import ModelDiscoveryService
from repomedic.ai.provider import groq_provider


def test_model_discovery_selects_preferred_model():
    """Verifies that discovered models are matched against priority preferences."""
    discovery = ModelDiscoveryService(ttl_seconds=3600)

    mock_client = MagicMock()
    mock_model_1 = MagicMock(id="unrelated-whisper-model")
    mock_model_2 = MagicMock(id="llama-3.3-70b-versatile")
    mock_client.models.list.return_value = MagicMock(data=[mock_model_1, mock_model_2])

    with patch("repomedic.ai.model_discovery.settings.GROQ_MODEL", None):
        with patch.object(groq_provider, "client", mock_client):
            active = discovery.get_active_model()
            assert active == "llama-3.3-70b-versatile"


def test_model_discovery_caching():
    """Verifies that discovery results are cached and repeated queries do not make redundant API calls."""
    discovery = ModelDiscoveryService(ttl_seconds=3600)

    mock_client = MagicMock()
    mock_model = MagicMock(id="openai/gpt-oss-20b")
    mock_client.models.list.return_value = MagicMock(data=[mock_model])

    with patch("repomedic.ai.model_discovery.settings.GROQ_MODEL", None):
        with patch.object(groq_provider, "client", mock_client):
            first = discovery.get_active_model()
            second = discovery.get_active_model()

            assert first == "openai/gpt-oss-20b"
            assert second == "openai/gpt-oss-20b"
            assert mock_client.models.list.call_count == 1


def test_diagnostics_never_exposes_api_key():
    """Diagnostic reporting must include model metadata without credentials."""
    discovery = ModelDiscoveryService()
    diag = discovery.get_diagnostics()

    assert "api_key" not in diag
    assert "token" not in diag
    assert "active_model" in diag
    assert "provider" in diag
    assert diag["provider"] == "Groq"
