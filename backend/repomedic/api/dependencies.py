import secrets
from typing import Optional
from fastapi import Header, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from repomedic.config import settings
from repomedic.logging_config import get_logger

logger = get_logger("api.dependencies")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    x_api_key: Optional[str] = Security(api_key_header),
    authorization: Optional[str] = Header(default=None)
) -> Optional[str]:
    """
    Validates API key from either 'X-API-Key' or 'Authorization: Bearer <key>'.
    In development mode without configured key, requests are permitted with a warning.
    In production mode, a valid key is strictly enforced.
    """
    configured_key = settings.REPOMEDIC_API_KEY
    provided_key = x_api_key

    # Extract from Authorization header if X-API-Key was not supplied
    if not provided_key and authorization and authorization.lower().startswith("bearer "):
        provided_key = authorization.split(" ", 1)[1].strip()

    # Development mode without required key
    if not configured_key:
        if settings.is_production:
            logger.error("Production mode active but REPOMEDIC_API_KEY is not configured!")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Server configuration error: Authentication key not set."
            )
        # Permitted in dev mode
        return None

    # Verify provided key against configured key using constant-time comparison
    if not provided_key or not secrets.compare_digest(provided_key, configured_key):
        logger.warning("Unauthorized API request received.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key. Provide a valid 'X-API-Key' header."
        )

    return provided_key
