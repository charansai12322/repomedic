"""Structured, safe logging for RepoMedic that prevents credential leakage."""

import logging
import re
import sys
from typing import Optional


# Generic pattern to catch tokens, bearer keys, and sensitive queries in log records
SENSITIVE_LOG_PATTERNS = [
    re.compile(r"(gsk_[A-Za-z0-9]{20,})"),
    re.compile(r"(gh[pousr]_[A-Za-z0-9]{36,})"),
    re.compile(r"(github_pat_[A-Za-z0-9_]{82})"),
    re.compile(r"((?:AKIA|ASIA)[0-9A-Z]{16})"),
    re.compile(r"(sk-[A-Za-z0-9_-]{20,})"),
    re.compile(r"(AIza[0-9A-Za-z_-]{35})"),
    re.compile(r"(xox[abprs]-[A-Za-z0-9-]{10,})"),
    re.compile(r"(password|passwd|secret|api_key|token)=([^\s&]+)", re.I),
]


class RedactingFormatter(logging.Formatter):
    """Logging formatter that redacts secrets and credentials from all emitted log records."""

    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        for pattern in SENSITIVE_LOG_PATTERNS:
            msg = pattern.sub("[REDACTED_CREDENTIAL]", msg)
        return msg


def configure_logging(level: int = logging.INFO) -> None:
    """Configures root logger with RedactingFormatter and stream handler."""
    root_logger = logging.getLogger("repomedic")
    root_logger.setLevel(level)

    # Avoid adding duplicate handlers if re-configured
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = RedactingFormatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Returns a named logger under the repomedic hierarchy."""
    if not logging.getLogger("repomedic").handlers:
        configure_logging()
    return logging.getLogger(f"repomedic.{name}" if name else "repomedic")
