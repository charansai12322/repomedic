"""Unit tests for asynchronous job lifecycle, cancellation semantics, and parameter forwarding."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from repomedic.models.findings import EvidenceQuality, Finding, Severity
from repomedic.models.health import ScanHealthSummary, ScannerHealth, ScannerStatus
from repomedic.models.jobs import JobState, ScanJob
from repomedic.models.reports import AITriageResult, ScanEvidenceSummary, ScanReport, SecurityScore
from repomedic.services.job_service import JobService


def make_dummy_report(target="https://github.com/test/repo"):
    health_summary = ScanHealthSummary.compute_audit_status(
        scanners={
            "custom_rules": ScannerHealth(
                status=ScannerStatus.COMPLETED,
                required=True,
                duration_ms=10,
                finding_count=0
            )
        },
        start_time="2026-10-14T00:00:00Z",
        finish_time="2026-10-14T00:00:01Z",
        total_duration_ms=1000
    )
    return ScanReport(
        target=target,
        scan_health=health_summary,
        score=SecurityScore(score=100, grade="A", penalty=0, severity_counts={}),
        evidence=ScanEvidenceSummary(files_scanned=1, scan_truncated=False, large_files_skipped=0, findings=[]),
        ai_triage=AITriageResult(executive_summary="Clean scan with no vulnerabilities"),
    )


@pytest.mark.asyncio
async def test_queued_job_cancellation_skips_worker_execution():
    """Cancelling a queued job must immediately mark it failed and prevent the worker from scanning."""
    mock_scan_service = MagicMock()
    service = JobService(scan_service=mock_scan_service)

    # Acquire semaphore so worker cannot run immediately
    await service._semaphore.acquire()

    resp = await service.submit_job(
        repo_url="https://github.com/test/repo",
        local_dir=Path("."),
        enable_git_history=True,
        enable_ai=False,
    )
    job_id = resp.job_id

    # Cancel while still queued behind the acquired semaphore
    cancelled_job = await service.cancel_job(job_id)
    assert cancelled_job.state == JobState.FAILED
    assert cancelled_job.current_step == "cancelled_by_user"

    # Release semaphore so worker acquires lock and checks state
    service._semaphore.release()
    await asyncio.sleep(0.05)

    # Worker must NOT have called execute_scan
    mock_scan_service.execute_scan.assert_not_called()

    # Job state must remain FAILED and not revert to RUNNING or COMPLETED
    job = await service.get_job(job_id)
    assert job.state == JobState.FAILED
    assert job.current_step == "cancelled_by_user"


@pytest.mark.asyncio
async def test_running_job_cancellation_preserves_cancelled_state():
    """If a job is cancelled while running, worker must not overwrite state with COMPLETED."""
    mock_scan_service = MagicMock()
    mock_scan_service.execute_scan.return_value = make_dummy_report()

    service = JobService(scan_service=mock_scan_service)

    resp = await service.submit_job(
        repo_url="https://github.com/test/repo",
        local_dir=Path("."),
    )
    job_id = resp.job_id

    # Wait for worker to enter RUNNING
    for _ in range(20):
        job = await service.get_job(job_id)
        if job.state == JobState.RUNNING:
            break
        await asyncio.sleep(0.01)

    # Cancel while running
    await service.cancel_job(job_id)
    cancelled = await service.get_job(job_id)
    assert cancelled.current_step == "cancelled_by_user"
    assert cancelled.state == JobState.FAILED

    # Allow worker thread to conclude
    await asyncio.sleep(0.05)

    # State must NOT be overwritten to COMPLETED
    final_job = await service.get_job(job_id)
    assert final_job.state == JobState.FAILED
    assert final_job.current_step == "cancelled_by_user"


@pytest.mark.asyncio
async def test_parameter_forwarding_to_execute_scan():
    """Verifies that enable_ai and max_history_commits are forwarded to execute_scan."""
    mock_scan_service = MagicMock()
    mock_scan_service.execute_scan.return_value = make_dummy_report()

    service = JobService(scan_service=mock_scan_service)

    resp = await service.submit_job(
        repo_url="https://github.com/test/repo",
        local_dir=Path("."),
        enable_git_history=True,
        enable_ai=False,
        max_history_commits=42,
    )

    # Allow worker to finish
    await asyncio.sleep(0.1)

    mock_scan_service.execute_scan.assert_called_once_with(
        target="https://github.com/test/repo",
        local_dir=Path("."),
        enable_git_history=True,
        enable_ai=False,
        max_history_commits=42,
    )
