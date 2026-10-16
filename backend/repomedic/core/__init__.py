"""Core analysis and orchestration modules for RepoMedic."""

from repomedic.core.deduplication import deduplicate_findings
from repomedic.core.sanitization import is_placeholder, sanitize, truncate_line_safely
from repomedic.core.scoring import compute_security_score


def __getattr__(name: str):
    if name == "ScannerOrchestrator":
        from repomedic.core.orchestrator import ScannerOrchestrator
        return ScannerOrchestrator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "sanitize",
    "is_placeholder",
    "truncate_line_safely",
    "compute_security_score",
    "deduplicate_findings",
    "ScannerOrchestrator",
]
