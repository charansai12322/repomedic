"""Asynchronous job queue and task lifecycle service (Workstream 9)."""

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
import uuid
from repomedic.config import settings
from repomedic.exceptions import JobNotFoundError, QueueFullError
from repomedic.logging_config import get_logger
from repomedic.models.health import AuditStatus
from repomedic.models.jobs import JobState, ScanJob, ScanJobResponse
from repomedic.models.reports import ScanReport
from repomedic.services.scan_service import ScanService, validate_repository_url

logger = get_logger("services.job")


class JobService:
    """Manages asynchronous scan job submission, concurrency limits, and state tracking."""

    def __init__(self, scan_service: Optional[ScanService] = None):
        self.scan_service = scan_service or ScanService()
        self._jobs: Dict[str, ScanJob] = {}
        self._semaphore = asyncio.Semaphore(settings.REPOMEDIC_MAX_CONCURRENT_SCANS)
        self._lock = asyncio.Lock()

    async def submit_job(
        self,
        repo_url: str,
        local_dir: Optional[Path] = None,
        enable_git_history: bool = False,
        enable_ai: bool = True,
        max_history_commits: Optional[int] = None,
    ) -> ScanJobResponse:
        """Validates input, enforces queue capacity, and enqueues background scan job."""
        if local_dir is None:
            # Validate URL before admitting into queue (raises InvalidTargetError on failure)
            validate_repository_url(repo_url)

        async with self._lock:
            # Enforce queue capacity bounds
            pending_count = sum(1 for j in self._jobs.values() if j.state in (JobState.QUEUED, JobState.RUNNING))
            if pending_count >= settings.REPOMEDIC_MAX_QUEUE_CAPACITY:
                raise QueueFullError("The scan queue has reached maximum capacity. Please retry shortly.")

            # Periodic prune of old completed/failed jobs to avoid unbounded memory growth
            if len(self._jobs) > 100:
                terminal_keys = [
                    k for k, v in self._jobs.items()
                    if v.state in (JobState.COMPLETED, JobState.PARTIAL, JobState.FAILED)
                ]
                for old_key in terminal_keys[:50]:
                    self._jobs.pop(old_key, None)

            job_id = str(uuid.uuid4())
            now_iso = datetime.now(timezone.utc).isoformat()
            job = ScanJob(
                job_id=job_id,
                target=repo_url,
                state=JobState.QUEUED,
                created_at=now_iso,
                progress_percent=5,
                current_step="queued"
            )
            self._jobs[job_id] = job

        # Spawn asynchronous worker task
        asyncio.create_task(
            self._run_job_worker(
                job_id,
                repo_url,
                local_dir,
                enable_git_history,
                enable_ai,
                max_history_commits,
            )
        )
        logger.info(f"Scan job {job_id} queued for '{repo_url}' (git_history={enable_git_history}, ai={enable_ai})")

        return ScanJobResponse(job_id=job_id, status=JobState.QUEUED)

    async def get_job(self, job_id: str) -> ScanJob:
        """Retrieves current job status, progress, and metadata."""
        async with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                raise JobNotFoundError(job_id)
            return job.model_copy()

    async def list_jobs(self, limit: int = 20) -> List[ScanJob]:
        """Returns recent jobs in reverse chronological order for dashboard display."""
        async with self._lock:
            sorted_jobs = sorted(
                self._jobs.values(),
                key=lambda j: j.created_at,
                reverse=True
            )
            return [j.model_copy() for j in sorted_jobs[:limit]]

    async def cancel_job(self, job_id: str) -> ScanJob:
        """Cancels a queued or running job."""
        async with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                raise JobNotFoundError(job_id)
            if job.state in (JobState.QUEUED, JobState.RUNNING):
                job.state = JobState.FAILED
                job.current_step = "cancelled_by_user"
                job.error = "Scan job cancelled by user."
                job.finished_at = datetime.now(timezone.utc).isoformat()
            return job.model_copy()

    async def get_job_report(self, job_id: str) -> ScanReport:
        """Returns completed ScanReport for a job, or raises exception if not ready."""
        job = await self.get_job(job_id)
        if job.state in (JobState.QUEUED, JobState.RUNNING):
            raise JobNotFoundError(f"Job {job_id} is still in progress (state: {job.state.value}).")
        if job.state == JobState.FAILED and not job.report:
            raise JobNotFoundError(f"Job {job_id} failed: {job.error or 'Unknown error'}")
        if not job.report:
            raise JobNotFoundError(f"No report available for job {job_id}.")
        return job.report

    async def _run_job_worker(
        self,
        job_id: str,
        repo_url: str,
        local_dir: Optional[Path],
        enable_git_history: bool = False,
        enable_ai: bool = True,
        max_history_commits: Optional[int] = None,
    ) -> None:
        """Background worker executing the scan under a bounded concurrency semaphore."""
        async with self._semaphore:
            async with self._lock:
                job = self._jobs.get(job_id)
                if not job or job.current_step == "cancelled_by_user" or job.state == JobState.FAILED:
                    logger.info(f"Worker skipping cancelled job {job_id}")
                    return
                job.state = JobState.RUNNING
                job.started_at = datetime.now(timezone.utc).isoformat()
                job.progress_percent = 20
                job.current_step = "cloning_and_preparation"

            logger.info(f"Worker began executing job {job_id}")

            try:
                # Run synchronous scan service in thread pool to prevent blocking event loop
                loop = asyncio.get_running_loop()
                report = await loop.run_in_executor(
                    None,
                    lambda: self.scan_service.execute_scan(
                        target=repo_url,
                        local_dir=local_dir,
                        enable_git_history=enable_git_history,
                        enable_ai=enable_ai,
                        max_history_commits=max_history_commits,
                    ),
                )

                async with self._lock:
                    job = self._jobs.get(job_id)
                    if not job or job.current_step == "cancelled_by_user":
                        logger.info(f"Job {job_id} was cancelled while running; ignoring completed report.")
                        return

                    job.finished_at = datetime.now(timezone.utc).isoformat()
                    job.report = report
                    job.progress_percent = 100

                    # Map audit status to final job state
                    if report.scan_health.audit_status == AuditStatus.COMPLETE:
                        job.state = JobState.COMPLETED
                        job.current_step = "completed"
                    elif report.scan_health.audit_status == AuditStatus.PARTIAL:
                        job.state = JobState.PARTIAL
                        job.current_step = "completed_partial_audit"
                    else:
                        job.state = JobState.FAILED
                        job.current_step = "failed"
                        job.error = "Scan failed audit completeness requirements."

                logger.info(f"Job {job_id} finished successfully with state={job.state.value}")

            except Exception as e:
                logger.error(f"Job {job_id} encountered fatal error: {e}")
                async with self._lock:
                    job = self._jobs.get(job_id)
                    if job and job.current_step != "cancelled_by_user":
                        job.state = JobState.FAILED
                        job.finished_at = datetime.now(timezone.utc).isoformat()
                        job.error = str(e)[:250]
                        job.current_step = "execution_failed"


# Global singleton instance
job_service = JobService()
