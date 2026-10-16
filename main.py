import sys
from pathlib import Path

# Add backend directory to sys.path so root execution works seamlessly
backend_dir = Path(__file__).resolve().parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

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
