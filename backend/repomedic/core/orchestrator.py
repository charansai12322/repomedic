"""Orchestrator for concurrent scanner execution, health aggregation, and deduplication."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import time
from typing import Dict, List, Optional
from repomedic.config import settings
from repomedic.core.deduplication import deduplicate_findings
from repomedic.core.scoring import compute_security_score
from repomedic.logging_config import get_logger
from repomedic.models.findings import Finding
from repomedic.models.health import ScanHealthSummary, ScannerHealth, ScannerStatus
from repomedic.models.reports import ScanEvidenceSummary, SecurityScore
from repomedic.scanners.base import BaseScanner
from repomedic.scanners.custom_rules import CustomRulesScanner
from repomedic.scanners.dependencies import DependencyScanner
from repomedic.scanners.git_history import GitHistoryScanner
from repomedic.scanners.python_ast import PythonASTScanner
from repomedic.scanners.semgrep import SemgrepScanner

logger = get_logger("orchestrator")


class ScannerOrchestrator:
    """Coordinates deterministic scanners in parallel, aggregates health states, and merges findings."""

    def __init__(
        self,
        scanners: Optional[List[BaseScanner]] = None,
        enable_git_history: Optional[bool] = None,
        max_history_commits: Optional[int] = None,
    ):
        if scanners is not None:
            self.scanners = scanners
        else:
            should_enable_git = (
                enable_git_history
                if enable_git_history is not None
                else settings.REPMEDIC_ENABLE_GIT_HISTORY
            )
            history_commits = (
                max_history_commits
                if max_history_commits is not None
                else settings.REPMEDIC_MAX_HISTORY_COMMITS
            )
            self.scanners = [
                CustomRulesScanner(
                    required=settings.REPOMEDIC_CUSTOM_RULES_REQUIRED,
                    max_file_bytes=settings.REPOMEDIC_MAX_TEXT_FILE_BYTES,
                    max_files=settings.REPOMEDIC_MAX_REPO_FILES,
                ),
                PythonASTScanner(
                    required=settings.REPOMEDIC_PYTHON_AST_REQUIRED,
                    max_file_bytes=settings.REPOMEDIC_MAX_TEXT_FILE_BYTES,
                ),
                SemgrepScanner(
                    required=settings.REPOMEDIC_SEMGREP_REQUIRED,
                ),
                DependencyScanner(
                    required=settings.REPOMEDIC_OSV_REQUIRED,
                ),
                GitHistoryScanner(
                    required=settings.REPMEDIC_GIT_HISTORY_REQUIRED,
                    enabled=should_enable_git,
                    max_commits=history_commits,
                ),
            ]

    def run_all_scanners(self, repo_dir: Path) -> tuple[List[Finding], ScanHealthSummary, SecurityScore, ScanEvidenceSummary]:
        start_utc = datetime.now(timezone.utc).isoformat()
        t0 = time.time()
        health_map: Dict[str, ScannerHealth] = {}
        all_raw_findings: List[Finding] = []

        logger.info(f"Starting deterministic scan across {len(self.scanners)} engines on '{repo_dir}'")

        # Run scanners concurrently in thread pool
        with ThreadPoolExecutor(max_workers=min(4, len(self.scanners))) as executor:
            future_to_scanner = {
                executor.submit(scanner.scan, repo_dir): scanner
                for scanner in self.scanners
            }
            for future in future_to_scanner:
                scanner = future_to_scanner[future]
                try:
                    findings, health = future.result()
                    health_map[scanner.name] = health
                    all_raw_findings.extend(findings)
                    logger.info(f"Scanner '{scanner.name}' finished with status={health.status.value}, findings={len(findings)}")
                except Exception as e:
                    logger.error(f"Scanner '{scanner.name}' raised unhandled exception: {e}")
                    health_map[scanner.name] = ScannerHealth(
                        status=ScannerStatus.FAILED,
                        required=scanner.required,
                        duration_ms=0,
                        error_code="ORCHESTRATION_EXCEPTION",
                        error_message=str(e)[:200],
                        finding_count=0
                    )

        finish_utc = datetime.now(timezone.utc).isoformat()
        total_duration_ms = int((time.time() - t0) * 1000)

        # 1. Compute aggregate health contract
        health_summary = ScanHealthSummary.compute_audit_status(
            scanners=health_map,
            start_time=start_utc,
            finish_time=finish_utc,
            total_duration_ms=total_duration_ms
        )

        # 2. Cross-scanner finding deduplication (Fixes AUDIT-003)
        deduped_findings = deduplicate_findings(all_raw_findings)

        # 3. Compute deterministic score and grade (Fixes AUDIT-004)
        score = compute_security_score(deduped_findings)

        # 4. Count files inspected
        candidate_count = sum(1 for p in repo_dir.rglob("*") if p.is_file() and not p.is_symlink())
        evidence_summary = ScanEvidenceSummary(
            files_scanned=min(candidate_count, settings.REPOMEDIC_MAX_REPO_FILES),
            scan_truncated=candidate_count > settings.REPOMEDIC_MAX_REPO_FILES,
            large_files_skipped=0,
            findings=deduped_findings
        )

        return deduped_findings, health_summary, score, evidence_summary
