"""Tests for configuration parsing, aliases, and CORS origin flexibility."""

import os
from unittest.mock import patch
import pytest
from repomedic.config import Settings


def test_cors_origins_comma_separated(monkeypatch):
    """Verifies that comma-separated environment strings parse into a clean list."""
    monkeypatch.setenv("REPOMEDIC_CORS_ORIGINS", "https://repomedic.onrender.com, http://localhost:3000")
    s = Settings()
    assert s.REPOMEDIC_CORS_ORIGINS == ["https://repomedic.onrender.com", "http://localhost:3000"]


def test_cors_origins_json_array(monkeypatch):
    """Verifies that valid JSON array strings parse correctly."""
    monkeypatch.setenv("REPOMEDIC_CORS_ORIGINS", '["https://frontend.vercel.app", "http://localhost:3000"]')
    s = Settings()
    assert s.REPOMEDIC_CORS_ORIGINS == ["https://frontend.vercel.app", "http://localhost:3000"]


def test_cors_origins_single_quoted_json(monkeypatch):
    """Verifies that single-quoted or dotenv-style quoted JSON parses without crash."""
    monkeypatch.setenv("REPOMEDIC_CORS_ORIGINS", '\'["https://frontend.vercel.app"]\'')
    s = Settings()
    assert s.REPOMEDIC_CORS_ORIGINS == ["https://frontend.vercel.app"]


def test_cors_origins_single_url(monkeypatch):
    """Verifies single URL without commas parses to single-item list."""
    monkeypatch.setenv("REPOMEDIC_CORS_ORIGINS", "https://repomedic.onrender.com")
    s = Settings()
    assert s.REPOMEDIC_CORS_ORIGINS == ["https://repomedic.onrender.com"]


def test_cors_origins_fallback_alias(monkeypatch):
    """Verifies that REPMEDIC_CORS_ORIGINS alias is supported."""
    monkeypatch.delenv("REPOMEDIC_CORS_ORIGINS", raising=False)
    monkeypatch.setenv("REPMEDIC_CORS_ORIGINS", "https://alias-test.org")
    s = Settings()
    assert s.REPOMEDIC_CORS_ORIGINS == ["https://alias-test.org"]


def test_groq_model_preferences_comma_separated(monkeypatch):
    """Verifies GROQ_MODEL_PREFERENCES parses comma-separated string."""
    monkeypatch.setenv("GROQ_MODEL_PREFERENCES", "llama-3.3-70b-versatile, llama-3.1-8b-instant")
    s = Settings()
    assert s.GROQ_MODEL_PREFERENCES == ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]


def test_cors_origins_python_literal_list(monkeypatch):
    """Verifies that single-quoted Python list syntax parses cleanly."""
    monkeypatch.setenv("REPOMEDIC_CORS_ORIGINS", "['https://repomedic.onrender.com', 'http://localhost:3000']")
    s = Settings()
    assert s.REPOMEDIC_CORS_ORIGINS == ["https://repomedic.onrender.com", "http://localhost:3000"]


def test_cors_origins_unquoted_bracket_list(monkeypatch):
    """Verifies that unquoted bracket lists parse without crash."""
    monkeypatch.setenv("REPOMEDIC_CORS_ORIGINS", "[https://repomedic.onrender.com, http://localhost:3000]")
    s = Settings()
    assert s.REPOMEDIC_CORS_ORIGINS == ["https://repomedic.onrender.com", "http://localhost:3000"]


def test_cors_origins_wildcard(monkeypatch):
    """Verifies wildcard origin parsing."""
    monkeypatch.setenv("REPOMEDIC_CORS_ORIGINS", "*")
    s = Settings()
    assert s.REPOMEDIC_CORS_ORIGINS == ["*"]


def test_port_and_host_cloud_aliases(monkeypatch):
    """Verifies standard cloud PORT and HOST environment variables are recognized."""
    monkeypatch.setenv("PORT", "10000")
    monkeypatch.setenv("HOST", "0.0.0.0")
    s = Settings()
    assert s.REPOMEDIC_PORT == 10000
    assert s.REPOMEDIC_HOST == "0.0.0.0"

