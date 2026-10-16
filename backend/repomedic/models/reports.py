"""Report and AI triage models for RepoMedic."""

from typing import Dict, List
from pydantic import BaseModel, Field, computed_field, field_validator
from repomedic.models.findings import Finding
from repomedic.models.health import AuditStatus, ScanHealthSummary


class AIDiagnosis(BaseModel):
    """Structured AI triage diagnosis tied to a validated scanner finding ID."""

    finding_id: str = Field(description="Must match an existing finding ID emitted by a deterministic scanner")
    title: str = Field(description="Short explanatory title of the triaged risk")
    why_it_matters: str = Field(description="Realistic security impact assessment in 1-2 sentences")
    fix: str = Field(description="Concrete remediation advice in 1-3 sentences")
    priority: int = Field(default=3, ge=1, le=5, description="Triage priority: 1 (fix first) to 5 (fix later)")
    likely_false_positive: bool = Field(default=False, description="Flag indicating AI assesses this finding as a likely false positive")

    @field_validator("priority", mode="before")
    @classmethod
    def clamp_priority(cls, v) -> int:
        try:
            return max(1, min(5, int(v)))
        except (TypeError, ValueError):
            return 3


class AITriageResult(BaseModel):
    """Aggregate AI triage interpretation and citation validity metrics."""

    executive_summary: str = Field(description="Concise high-level summary of the most urgent security themes")
    diagnoses: List[AIDiagnosis] = Field(default_factory=list, description="List of validated, prioritized diagnoses")
    limitations: List[str] = Field(default_factory=list, description="Caveats regarding static analysis, redactions, and AI bounds")
    citation_validity_percent: float = Field(default=100.0, ge=0.0, le=100.0, description="Percentage of AI-cited IDs verified in evidence")
    model: str = Field(default="none", description="Exact model name used for triage (or 'none (offline)')")
    mode: str = Field(default="deterministic_only", description="'groq' if LLM was invoked, otherwise 'deterministic_only'")
    duration_ms: int = Field(default=0, ge=0, description="Inference latency in milliseconds")


class SecurityScore(BaseModel):
    """Deterministic, explainable security score and letter grade."""

    score: int = Field(ge=0, le=100, description="Security score from 0 (worst) to 100 (best)")
    grade: str = Field(description="Letter grade: A, B, C, D, or F")
    penalty: int = Field(ge=0, description="Accumulated penalty points before exponential decay")
    severity_counts: Dict[str, int] = Field(default_factory=dict, description="Finding counts categorized by severity")


class ScanEvidenceSummary(BaseModel):
    """Summary of repository files inspected and list of normalized findings."""

    files_scanned: int = Field(ge=0, description="Total number of text candidate files inspected")
    scan_truncated: bool = Field(default=False, description="True if repo file count exceeded safety ceiling")
    large_files_skipped: int = Field(default=0, ge=0, description="Number of text files skipped due to size limits")
    findings: List[Finding] = Field(default_factory=list, description="Canonical normalized findings")


class ScanReport(BaseModel):
    """Root scan result contract returned by the scanner orchestrator and API."""

    target: str = Field(description="Scanned repository URL or label")
    scan_health: ScanHealthSummary = Field(description="Scanner health states and audit completeness guarantee")
    score: SecurityScore = Field(description="Deterministic security score and grade")
    evidence: ScanEvidenceSummary = Field(description="Normalized findings and file stats")
    ai_triage: AITriageResult = Field(description="AI triage analysis, citation validity, and executive summary")
    security_boundary: str = Field(
        default="Static analysis only. Repository code is never installed, imported, or executed.",
        description="Explicit guarantee of execution boundary"
    )

    @computed_field
    def partial_audit(self) -> bool:
        """Convenience accessor matching the scan_health contract."""
        return self.scan_health.partial_audit

    @computed_field
    def audit_status(self) -> AuditStatus:
        """Convenience accessor matching the scan_health contract."""
        return self.scan_health.audit_status

