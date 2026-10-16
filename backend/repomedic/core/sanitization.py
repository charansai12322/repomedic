"""Secret redaction, token masking, and safe input sanitization."""

import re
from typing import List, Tuple


# Regex patterns for detecting and redacting secrets (rule_id, severity, regex, description)
SECRET_PATTERNS: List[Tuple[str, str, re.Pattern, str]] = [
    (
        "aws_access_key",
        "critical",
        re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
        "AWS access key ID committed to source."
    ),
    (
        "github_token",
        "critical",
        re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"),
        "GitHub token committed to source."
    ),
    (
        "github_fine_grained_pat",
        "critical",
        re.compile(r"\bgithub_pat_[A-Za-z0-9_]{82}\b"),
        "GitHub Fine-Grained Personal Access Token committed to source."
    ),
    (
        "groq_api_key",
        "critical",
        re.compile(r"\bgsk_[A-Za-z0-9]{20,}\b"),
        "Groq API key committed to source."
    ),
    (
        "openai_style_key",
        "critical",
        re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
        "API key (sk-…) committed to source."
    ),
    (
        "slack_token",
        "critical",
        re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b"),
        "Slack token committed to source."
    ),
    (
        "google_api_key",
        "high",
        re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
        "Google API key committed to source."
    ),
    (
        "private_key",
        "critical",
        re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----"),
        "Private key material committed to source."
    ),
    (
        "database_connection_uri",
        "high",
        re.compile(r"\b(?:postgres|postgresql|mysql|mongodb|redis|amqp)://[^\s:@]+:[^\s@]+@[^\s/@]+/[^\s]+"),
        "Database connection string with embedded password committed to source."
    ),
    (
        "hardcoded_secret_assignment",
        "high",
        re.compile(r"""(?i)(?:password|passwd|pwd|secret|api[_-]?key|auth[_-]?token|access[_-]?token|conn[_-]?str)\w*\s*[:=]\s*['"][^'"\s]{8,}['"]"""),
        "Hardcoded credential-like value assigned in source."
    ),
    (
        "bearer_token",
        "high",
        re.compile(r"\bBearer\s+[A-Za-z0-9._~+/-]{20,}\b"),
        "Authorization Bearer token committed to source."
    ),
]

PLACEHOLDER_PATTERN = re.compile(
    r"(?i)example|changeme|change_me|your[_-]|xxxx|<.*>|\$\{|%\(|os\.environ|getenv|dummy|placeholder|test[_-]?password"
)


def is_placeholder(value: str) -> bool:
    """Checks whether a detected match is an obvious non-secret placeholder or example."""
    return bool(PLACEHOLDER_PATTERN.search(value))


def sanitize(text: str, limit: int = 200) -> str:
    """
    Redacts secrets from a text line or snippet, replaces matches with [REDACTED],
    and bounds length to prevent prompt bloat or UI distortion.
    """
    if not text:
        return ""
    # Truncate first to prevent catastrophic processing on huge lines
    clean = text.strip()[:600]
    for _, _, pattern, _ in SECRET_PATTERNS:
        clean = pattern.sub("[REDACTED]", clean)
    return clean[:limit]


def truncate_line_safely(line: str, max_chars: int = 2000) -> str:
    """
    Truncates exceptionally long lines (e.g. minified JS or padded evasion attempts)
    rather than skipping them entirely.
    """
    if len(line) > max_chars:
        return line[:max_chars]
    return line
