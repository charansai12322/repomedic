"""Job models for asynchronous scan task management."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from repomedic.models.reports import ScanReport


class JobState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class ScanRequest(BaseModel):
    """Payload submitted to POST /scan."""

    repo_url: str = Field(
        min_length=1,
        max_length=512,
        description="Public GitHub repository URL (e.g. https://github.com/owner/repo)"
    )
    enable_git_history: bool = Field(
        default=False,
        description="Optional: Scan recent git commits for removed or historical secrets"
    )
    enable_ai: bool = Field(
        default=True,
        description="Optional: Enable or disable AI-assisted triage and explanation"
    )
    max_history_commits: Optional[int] = Field(
        default=None,
        ge=1,
        le=500,
        description="Optional: Maximum commit depth for git history scanning"
    )


class ScanJob(BaseModel):
    """Internal and external representation of an asynchronous scan job."""

    job_id: str = Field(description="Unique UUID identifying the scan job")
    target: str = Field(description="Target repository URL")
    state: JobState = Field(default=JobState.QUEUED, description="Current job state: queued, running, completed, partial, failed")
    created_at: str = Field(description="ISO-8601 UTC timestamp of job creation")
    started_at: Optional[str] = Field(default=None, description="ISO-8601 UTC timestamp when scan execution began")
    finished_at: Optional[str] = Field(default=None, description="ISO-8601 UTC timestamp when scan execution concluded")
    progress_percent: int = Field(default=0, ge=0, le=100, description="Estimated scan progress percentage")
    current_step: str = Field(default="queued", description="Description of the active pipeline stage")
    error: Optional[str] = Field(default=None, description="Safe error message if job failed")
    report: Optional[ScanReport] = Field(default=None, description="Completed scan report when finished")


class ScanJobResponse(BaseModel):
    """HTTP 202 response returned immediately upon scan submission."""

    job_id: str = Field(description="Identifier to poll at /jobs/{job_id}")
    status: JobState = Field(default=JobState.QUEUED, description="Initial state (queued)")
    message: str = Field(default="Scan job submitted successfully and queued for processing.")
