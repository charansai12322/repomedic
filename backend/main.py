import sys
from pathlib import Path

# Add backend directory to sys.path so importing works from any working directory
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import uvicorn
from repomedic.api.app import app  # Export app so `uvicorn backend.main:app` works out of the box
from repomedic.config import settings
from repomedic.logging_config import configure_logging, get_logger

logger = get_logger("main")


def run() -> None:
    """Starts the Uvicorn ASGI server with configured host and port."""
    configure_logging()
    host = settings.REPOMEDIC_HOST
    if settings.is_production and host == "127.0.0.1":
        host = "0.0.0.0"
    logger.info(
        f"Starting RepoMedic backend on {host}:{settings.REPOMEDIC_PORT} (env: {settings.REPOMEDIC_ENV})"
    )
    uvicorn.run(
        "repomedic.api.app:app",
        host=host,
        port=settings.REPOMEDIC_PORT,
        reload=not settings.is_production,
        log_level="info",
    )


if __name__ == "__main__":
    run()
