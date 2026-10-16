"""Scan job submission endpoints."""

from fastapi import APIRouter, Depends, status
from repomedic.api.dependencies import verify_api_key
from repomedic.models.jobs import ScanJobResponse, ScanRequest
from repomedic.services.job_service import job_service

router = APIRouter(tags=["Scans"])


@router.post(
    "/scan",
    response_model=ScanJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit repository for asynchronous security scan",
    dependencies=[Depends(verify_api_key)]
)
@router.post(
    "/scans",
    response_model=ScanJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit repository for asynchronous security scan (plural alias)",
    dependencies=[Depends(verify_api_key)],
    include_in_schema=False
)
async def submit_scan(request: ScanRequest) -> ScanJobResponse:
    """
    Submits a public GitHub repository for asynchronous security auditing.
    Immediately returns an HTTP 202 Accepted status with a job_id for polling.
    """
    return await job_service.submit_job(
        repo_url=request.repo_url,
        enable_git_history=request.enable_git_history,
        enable_ai=request.enable_ai,
        max_history_commits=request.max_history_commits,
    )
