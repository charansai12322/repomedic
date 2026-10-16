"""Tests for secret redaction, token masking, and line truncation (Fixes AUDIT-006)."""

from repomedic.core.sanitization import (
    is_placeholder,
    sanitize,
    truncate_line_safely,
)


def test_redacts_aws_access_key():
    line = 'AWS_KEY = "AKIAIOSFODNN7EXAMPLE"'
    redacted = sanitize(line)
    assert "AKIAIOSFODNN7EXAMPLE" not in redacted
    assert "[REDACTED]" in redacted


def test_redacts_github_tokens():
    classic = 'token = "ghp_123456789012345678901234567890123456"'
    fine_grained = 'pat = "github_pat_' + 'A' * 82 + '"'
    assert "[REDACTED]" in sanitize(classic)
    assert "[REDACTED]" in sanitize(fine_grained)


def test_redacts_groq_and_openai_keys():
    groq_key = 'GROQ = "gsk_1234567890123456789012"'
    openai_key = 'OAI = "sk-proj-1234567890123456789012"'
    assert "[REDACTED]" in sanitize(groq_key)
    assert "[REDACTED]" in sanitize(openai_key)


def test_redacts_database_connection_uri():
    """Verifies that database connection strings with embedded credentials are masked (Fixes AUDIT-006)."""
    uri = 'DATABASE_URL = "postgres://admin_user:SuperSecretPassword123!@db.internal.net:5432/production"'
    redacted = sanitize(uri)
    assert "SuperSecretPassword123!" not in redacted
    assert "[REDACTED]" in redacted


def test_redacts_private_key_blocks():
    pem = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0...\n-----END RSA PRIVATE KEY-----"
    assert "[REDACTED]" in sanitize(pem)


def test_exempts_placeholders():
    assert is_placeholder("changeme-example-value")
    assert is_placeholder("your_api_key_here")
    assert is_placeholder("os.environ.get('SECRET')")
    assert not is_placeholder("AKIAIOSFODNN7REALKEY")


def test_truncates_long_lines_rather_than_skipping():
    """Verifies that lines over 2000 chars are truncated to prevent scanner evasion (Fixes AUDIT-006)."""
    long_line = "eval(input)" + " " * 3000
    truncated = truncate_line_safely(long_line, max_chars=2000)
    assert len(truncated) == 2000
    assert truncated.startswith("eval(input)")
