"""Health, readiness, and safe diagnostic endpoints."""

import shutil
from typing import Any, Dict
from fastapi import APIRouter, Depends
from repomedic import __version__
from repomedic.ai.model_discovery import model_discovery
from repomedic.ai.provider import groq_provider
from repomedic.api.dependencies import verify_api_key
from repomedic.config import settings
from repomedic.services.job_service import job_service

router = APIRouter(tags=["Health & Diagnostics"])


@router.get("/health", summary="Liveness probe")
async def health_check() -> Dict[str, Any]:
    """Returns basic liveness status and version information."""
    return {
        "status": "ok",
        "service": "RepoMedic",
        "version": __version__,
        "environment": settings.REPOMEDIC_ENV
    }


@router.get("/ready", summary="Readiness probe")
async def readiness_check() -> Dict[str, Any]:
    """Evaluates whether the backend is ready to accept new scan jobs."""
    semgrep_available = bool(shutil.which("semgrep"))
    ai_available = groq_provider.is_configured

    return {
        "status": "ready",
        "service": "RepoMedic",
        "version": __version__,
        "scanners": {
            "custom_rules": "available",
            "python_ast": "available",
            "osv": "available",
            "semgrep": "available" if semgrep_available else "unavailable (optional)"
        },
        "ai_inference": {
            "mode": "groq" if ai_available else "deterministic_only",
            "configured": ai_available
        }
    }


@router.get("/diagnostics", summary="Safe diagnostic status", dependencies=[Depends(verify_api_key)])
async def diagnostics_info() -> Dict[str, Any]:
    """Returns operational parameters and discovered model info without exposing secrets."""
    return {
        "service": "RepoMedic",
        "version": __version__,
        "environment": settings.REPOMEDIC_ENV,
        "tools": {
            "semgrep_installed": bool(shutil.which("semgrep")),
            "git_installed": bool(shutil.which("git")),
        },
        "ai_discovery": model_discovery.get_diagnostics(),
        "limits": {
            "max_concurrent_scans": settings.REPOMEDIC_MAX_CONCURRENT_SCANS,
            "max_queue_capacity": settings.REPOMEDIC_MAX_QUEUE_CAPACITY,
            "scan_timeout_seconds": settings.REPOMEDIC_SCAN_TIMEOUT_SECONDS,
            "max_repo_mb": settings.REPOMEDIC_MAX_REPO_MB,
            "max_repo_files": settings.REPOMEDIC_MAX_REPO_FILES,
        },
        "scanner_policies": {
            "semgrep_required": settings.REPOMEDIC_SEMGREP_REQUIRED,
            "osv_required": settings.REPOMEDIC_OSV_REQUIRED,
            "custom_rules_required": settings.REPOMEDIC_CUSTOM_RULES_REQUIRED,
            "python_ast_required": settings.REPOMEDIC_PYTHON_AST_REQUIRED,
            "ai_triage_required": settings.REPOMEDIC_AI_TRIAGE_REQUIRED,
        }
    }
