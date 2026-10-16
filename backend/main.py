"""Local development entry point for RepoMedic."""

import uvicorn
from repomedic.config import settings
from repomedic.logging_config import configure_logging, get_logger

logger = get_logger("main")


def run() -> None:
    """Starts the Uvicorn ASGI server with configured host and port."""
    configure_logging()
    logger.info(
        f"Starting RepoMedic backend on {settings.REPOMEDIC_HOST}:{settings.REPOMEDIC_PORT} (env: {settings.REPOMEDIC_ENV})"
    )
    uvicorn.run(
        "repomedic.api.app:app",
        host=settings.REPOMEDIC_HOST,
        port=settings.REPOMEDIC_PORT,
        reload=not settings.is_production,
        log_level="info",
    )


if __name__ == "__main__":
    run()
