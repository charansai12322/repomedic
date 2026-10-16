"""Scan job polling and report retrieval endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from repomedic.api.dependencies import verify_api_key
from repomedic.exceptions import JobNotFoundError
from repomedic.exports import (
    export_report_to_html,
    export_report_to_json,
    export_report_to_sarif_json,
)
from repomedic.models.jobs import JobState, ScanJob
from repomedic.models.reports import ScanReport
from repomedic.services.job_service import job_service

router = APIRouter(tags=["Jobs & Reports"], dependencies=[Depends(verify_api_key)])


@router.get(
    "/jobs",
    response_model=List[ScanJob],
    summary="List recent scan jobs",
)
async def list_jobs(limit: int = Query(20, ge=1, le=100)) -> List[ScanJob]:
    """Retrieves the most recent scan jobs for dashboard display."""
    return await job_service.list_jobs(limit=limit)


@router.get(
    "/jobs/{job_id}",
    response_model=ScanJob,
    summary="Get scan job status and progress",
)
async def get_job_status(job_id: str) -> ScanJob:
    """Polls the execution status, progress percentage, and step of an enqueued scan job."""
    try:
        return await job_service.get_job(job_id)
    except JobNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/jobs/{job_id}/cancel",
    response_model=ScanJob,
    summary="Cancel a queued scan job",
)
async def cancel_job(job_id: str) -> ScanJob:
    """Cancels a pending queued scan job."""
    try:
        return await job_service.cancel_job(job_id)
    except JobNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/jobs/{job_id}/report",
    summary="Retrieve completed security audit report (supports json, html, and sarif formats)",
)
async def get_job_report(
    job_id: str,
    format: str = Query("json", description="Export format: json, html, or sarif"),
) -> Response:
    """
    Retrieves the audit report for a completed or partial scan job.
    Supports JSON, HTML, and SARIF 2.1.0 formats with appropriate Content-Type headers.
    """
    try:
        job = await job_service.get_job(job_id)
    except JobNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    if job.state in (JobState.QUEUED, JobState.RUNNING):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Scan job is still in progress (state: {job.state.value}). Please retry when status is completed.",
        )

    if job.state == JobState.FAILED and not job.report:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Scan execution failed: {job.error or 'Unknown failure'}",
        )

    if not job.report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report data not found for the specified job.",
        )

    fmt = format.lower().strip()
    if fmt == "sarif":
        sarif_content = export_report_to_sarif_json(job.report)
        return Response(
            content=sarif_content,
            media_type="application/sarif+json",
            headers={
                "Content-Disposition": f'attachment; filename="repomedic-scan-{job_id[:8]}.sarif"'
            },
        )
    elif fmt == "html":
        html_content = export_report_to_html(job.report)
        return Response(
            content=html_content,
            media_type="text/html",
            headers={
                "Content-Disposition": f'inline; filename="repomedic-scan-{job_id[:8]}.html"'
            },
        )
    elif fmt == "json":
        json_content = export_report_to_json(job.report)
        return Response(
            content=json_content,
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="repomedic-scan-{job_id[:8]}.json"'
            },
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format '{format}'. Valid options are: json, html, sarif.",
        )
