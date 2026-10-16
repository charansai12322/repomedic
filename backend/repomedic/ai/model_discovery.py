"""Model discovery service for Groq LLMs with caching and capability-based fallback (Workstream 7)."""

import time
from typing import Any, Dict, List, Optional
from repomedic.config import settings
from repomedic.logging_config import get_logger
from repomedic.ai.provider import groq_provider

logger = get_logger("ai.model_discovery")


class ModelDiscoveryService:
    """Discovers and caches available Groq models, selecting optimal reasoning models for triage."""

    def __init__(self, ttl_seconds: Optional[int] = None):
        self.ttl_seconds = ttl_seconds or settings.GROQ_DISCOVERY_CACHE_TTL_SECONDS
        self._cached_models: List[str] = []
        self._last_discovery_time: float = 0.0
        self._active_model: str = settings.GROQ_MODEL or "openai/gpt-oss-20b"

    def get_active_model(self) -> str:
        """Returns the active model identifier, executing discovery if needed."""
        # Explicit override takes immediate precedence
        if settings.GROQ_MODEL:
            return settings.GROQ_MODEL

        # If cache is valid, return selected model
        if self._cached_models and (time.time() - self._last_discovery_time < self.ttl_seconds):
            return self._active_model

        # Discover from provider
        discovered = self.discover_available_models()
        if not discovered:
            return self._active_model

        # Prioritize matching models against configured preference list
        for preferred in settings.GROQ_MODEL_PREFERENCES:
            if preferred in discovered:
                self._active_model = preferred
                logger.info(f"Selected preferred Groq model: {self._active_model}")
                return self._active_model

        # If none of preferred match, pick first available chat model
        self._active_model = discovered[0]
        logger.info(f"Selected fallback Groq model from discovered list: {self._active_model}")
        return self._active_model

    def discover_available_models(self) -> List[str]:
        """Queries Groq API for available models, caching results."""
        client = groq_provider.client
        if not client:
            return []

        try:
            resp = client.models.list()
            model_ids = [m.id for m in resp.data if hasattr(m, "id")]
            self._cached_models = model_ids
            self._last_discovery_time = time.time()
            logger.info(f"Discovered {len(model_ids)} models from Groq API.")
            return model_ids
        except Exception as e:
            logger.warning(f"Groq model discovery query failed: {str(e)[:160]}; using fallback: {self._active_model}")
            return self._cached_models

    def get_diagnostics(self) -> Dict[str, Any]:
        """Provides safe diagnostic status without exposing API keys or secrets."""
        cache_age = int(time.time() - self._last_discovery_time) if self._last_discovery_time > 0 else None
        return {
            "provider": "Groq",
            "is_configured": groq_provider.is_configured,
            "active_model": self.get_active_model(),
            "configured_override": settings.GROQ_MODEL,
            "preferences": settings.GROQ_MODEL_PREFERENCES,
            "cached_model_count": len(self._cached_models),
            "cache_age_seconds": cache_age,
            "cache_ttl_seconds": self.ttl_seconds
        }


# Global discovery service instance
model_discovery = ModelDiscoveryService()
