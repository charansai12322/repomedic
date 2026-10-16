"""Scanner health and audit completeness models."""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import AliasChoices, BaseModel, Field


class ScannerStatus(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"
    UNAVAILABLE = "unavailable"
    SKIPPED = "skipped"
    RUNNING = "running"


class AuditStatus(str, Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    FAILED = "failed"


class ScannerHealth(BaseModel):
    """Execution status and diagnostics for an individual scanner engine."""

    status: ScannerStatus = Field(description="Scanner state: completed, failed, unavailable, skipped, running")
    required: bool = Field(default=True, description="Whether this scanner is mandatory for a complete audit")
    duration_ms: int = Field(default=0, ge=0, description="Duration of this scanner in milliseconds")
    error_code: Optional[str] = Field(default=None, description="Sanitized machine-readable error identifier")
    error_message: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("error_message", "diagnostic_message"),
        description="Sanitized diagnostic failure description"
    )
    finding_count: int = Field(default=0, ge=0, description="Number of findings discovered by this scanner")

    @property
    def diagnostic_message(self) -> Optional[str]:
        return self.error_message


class ScanHealthSummary(BaseModel):
    """Aggregate health state, scanner results, and audit completeness guarantee."""

    scanners: Dict[str, ScannerHealth] = Field(description="Map of scanner name to individual ScannerHealth")
    audit_status: AuditStatus = Field(description="Overall audit outcome: complete, partial, failed")
    partial_audit: bool = Field(description="True if any required scanner failed, timed out, or was unavailable")
    start_time: str = Field(description="ISO-8601 UTC timestamp of scan initiation")
    finish_time: str = Field(description="ISO-8601 UTC timestamp of scan termination")
    total_duration_ms: int = Field(ge=0, description="Total elapsed wall-clock duration in milliseconds")
    degraded_reasons: List[str] = Field(default_factory=list, description="Explicit caveats explaining any degraded scanner state")

    @classmethod
    def compute_audit_status(
        cls,
        scanners: Dict[str, ScannerHealth],
        start_time: str,
        finish_time: str,
        total_duration_ms: int
    ) -> "ScanHealthSummary":
        """Calculates audit_status and partial_audit strictly based on required vs optional scanner outcomes."""
        partial = False
        all_required_failed = True
        has_any_required = False
        degraded = []

        for name, h in scanners.items():
            if h.required:
                has_any_required = True
                if h.status != ScannerStatus.COMPLETED:
                    partial = True
                    reason = f"Required scanner '{name}' {h.status.value}"
                    if h.error_code:
                        reason += f" ({h.error_code})"
                    degraded.append(reason)
                else:
                    all_required_failed = False
            else:
                if h.status != ScannerStatus.COMPLETED and h.status != ScannerStatus.SKIPPED:
                    degraded.append(f"Optional scanner '{name}' {h.status.value}")

        if not has_any_required:
            audit_status = AuditStatus.COMPLETE if not partial else AuditStatus.PARTIAL
        elif all_required_failed:
            audit_status = AuditStatus.FAILED
            partial = True
        elif partial:
            audit_status = AuditStatus.PARTIAL
        else:
            audit_status = AuditStatus.COMPLETE

        return cls(
            scanners=scanners,
            audit_status=audit_status,
            partial_audit=partial,
            start_time=start_time,
            finish_time=finish_time,
            total_duration_ms=total_duration_ms,
            degraded_reasons=degraded
        )
