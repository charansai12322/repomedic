"""FastAPI application factory and middleware configuration."""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from repomedic import __version__
from repomedic.api.routes_benchmarks import router as benchmark_router
from repomedic.api.routes_health import router as health_router
from repomedic.api.routes_jobs import router as jobs_router
from repomedic.api.routes_scans import router as scans_router
from repomedic.config import settings
from repomedic.exceptions import (
    AuthenticationError,
    InvalidTargetError,
    JobNotFoundError,
    QueueFullError,
    RepoMedicError,
    ResourceLimitExceededError,
    ValidationError,
)
from repomedic.logging_config import configure_logging, get_logger

logger = get_logger("api.app")


def create_app() -> FastAPI:
    """Creates and configures a production-ready FastAPI application."""
    configure_logging()

    app = FastAPI(
        title="RepoMedic API",
        description="AI-Assisted Static Security Triage Engine for Code Repositories",
        version=__version__,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
    )

    # CORS configuration with strict explicit origins (no wildcard in production)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.REPOMEDIC_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # Global Exception Handlers that protect against stack trace leakage
    @app.exception_handler(InvalidTargetError)
    async def invalid_target_handler(request: Request, exc: InvalidTargetError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "INVALID_TARGET_URL", "message": exc.message}
        )

    @app.exception_handler(ResourceLimitExceededError)
    async def limit_exceeded_handler(request: Request, exc: ResourceLimitExceededError):
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={"error": "RESOURCE_LIMIT_EXCEEDED", "message": exc.message}
        )

    @app.exception_handler(QueueFullError)
    async def queue_full_handler(request: Request, exc: QueueFullError):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"error": "QUEUE_FULL", "message": exc.message}
        )

    @app.exception_handler(JobNotFoundError)
    async def job_not_found_handler(request: Request, exc: JobNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": "JOB_NOT_FOUND", "message": exc.message}
        )

    @app.exception_handler(AuthenticationError)
    async def auth_error_handler(request: Request, exc: AuthenticationError):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "AUTHENTICATION_FAILED", "message": exc.message}
        )

    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": "VALIDATION_ERROR", "message": exc.message}
        )

    @app.exception_handler(RepoMedicError)
    async def repomedic_base_handler(request: Request, exc: RepoMedicError):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": exc.error_code, "message": exc.message}
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled server error on {request.method} {request.url.path}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "An internal error occurred while processing the request."
            }
        )

    # Mount Route Modules (both unversioned and versioned /api/v1 prefixes)
    for pfx in ("", "/api/v1"):
        app.include_router(health_router, prefix=pfx)
        app.include_router(scans_router, prefix=pfx)
        app.include_router(jobs_router, prefix=pfx)
        app.include_router(benchmark_router, prefix=pfx)

    return app


# Default app instance
app = create_app()
