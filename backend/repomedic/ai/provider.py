"""Groq API client provider abstraction with safe credential management."""

from typing import Optional
from groq import Groq
from repomedic.config import settings
from repomedic.logging_config import get_logger

logger = get_logger("ai.provider")


class GroqProvider:
    """Manages Groq SDK client instance and configuration state."""

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or settings.GROQ_API_KEY
        self.client: Optional[Groq] = None
        if self._api_key:
            try:
                self.client = Groq(api_key=self._api_key, timeout=settings.GROQ_TIMEOUT_SECONDS)
                logger.info("Groq client initialized successfully.")
            except Exception as e:
                logger.warning(f"Failed to initialize Groq client: {str(e)[:160]}")
                self.client = None
        else:
            logger.info("Groq API key not provided; operating in deterministic-only mode.")

    @property
    def is_configured(self) -> bool:
        return self.client is not None


# Global provider instance
groq_provider = GroqProvider()
