"""Canonical Finding schema and types for RepoMedic."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EvidenceQuality(str, Enum):
    DETERMINISTIC = "deterministic"
    AI_INTERPRETATION = "ai_interpretation"
    UNVERIFIED = "unverified"


class Finding(BaseModel):
    """Canonical, normalized representation of a security finding."""

    id: str = Field(description="Unique, stable identifier for the finding (e.g. F-a1b2c3d4)")
    title: str = Field(description="Short human-readable summary of the issue")
    description: str = Field(description="Detailed explanation of the flaw or security risk")
    severity: Severity = Field(description="Standardized severity: critical, high, medium, low, info")
    confidence: Confidence = Field(default=Confidence.HIGH, description="Assessment confidence: high, medium, low")
    source: str = Field(description="Originating scanner identifier: custom_rules, python_ast, semgrep, osv")
    evidence_quality: EvidenceQuality = Field(
        default=EvidenceQuality.DETERMINISTIC,
        description="Evidence type: deterministic scanner check vs ai_interpretation"
    )
    rule_id: str = Field(description="Exact scanner-specific rule or check identifier")
    file_path: str = Field(description="Repository-relative file path with forward slashes")
    line_start: int = Field(default=1, ge=1, description="Starting line number (1-indexed)")
    line_end: int = Field(default=1, ge=1, description="Ending line number (1-indexed)")
    evidence: str = Field(default="", description="Sanitized excerpt or dependency coordinate (secrets REDACTED)")
    remediation: str = Field(default="", description="Actionable remediation guidance")
    references: List[str] = Field(default_factory=list, description="Citations, CVE IDs, CWEs, or documentation URLs")
    corroborating_sources: List[str] = Field(
        default_factory=list,
        description="Secondary scanners that corroborated this exact finding at the same location"
    )
    fingerprint: Optional[str] = Field(default=None, description="Deduplication hash for cross-scanner matching")

    @field_validator("file_path", mode="before")
    @classmethod
    def normalize_file_path(cls, v: str) -> str:
        if not v:
            return "unknown"
        # Force forward slashes and strip leading separators
        return str(v).replace("\\", "/").lstrip("/")

    @field_validator("line_end", mode="after")
    @classmethod
    def validate_line_end(cls, v: int, info) -> int:
        start = info.data.get("line_start", 1)
        return max(v, start)
