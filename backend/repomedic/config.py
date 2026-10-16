"""Configuration settings for RepoMedic loaded from environment variables and .env files."""

import os
from typing import List, Optional, Union
from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with strong typing and secure defaults."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Runtime Environment
    REPOMEDIC_ENV: str = Field(
        default="development",
        validation_alias=AliasChoices("REPOMEDIC_ENV", "REPMEDIC_ENV"),
        description="Environment mode: development, staging, production"
    )
    REPOMEDIC_HOST: str = Field(
        default="127.0.0.1",
        validation_alias=AliasChoices("HOST", "REPOMEDIC_HOST", "REPMEDIC_HOST"),
        description="Host interface to bind HTTP server"
    )
    REPOMEDIC_PORT: int = Field(
        default=8000,
        validation_alias=AliasChoices("PORT", "REPOMEDIC_PORT", "REPMEDIC_PORT"),
        description="Port to bind HTTP server"
    )

    # API Security
    REPOMEDIC_API_KEY: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("REPOMEDIC_API_KEY", "REPMEDIC_API_KEY"),
        description="API key required for scan submission in production"
    )
    REPOMEDIC_CORS_ORIGINS: Union[str, List[str]] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"],
        validation_alias=AliasChoices("REPOMEDIC_CORS_ORIGINS", "REPMEDIC_CORS_ORIGINS"),
        description="Allowed CORS origins"
    )

    # Groq Cloud AI Inference
    GROQ_API_KEY: Optional[str] = Field(default=None, description="Groq Cloud API key")
    GROQ_MODEL: Optional[str] = Field(default=None, description="Explicit override for Groq model identifier")
    GROQ_TIMEOUT_SECONDS: float = Field(default=30.0, description="Timeout for Groq inference requests")
    GROQ_DISCOVERY_CACHE_TTL_SECONDS: int = Field(default=3600, description="Model discovery cache duration in seconds")
    GROQ_MODEL_PREFERENCES: Union[str, List[str]] = Field(
        default_factory=lambda: [
            "openai/gpt-oss-20b",
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
        ],
        description="Ordered priority list for automated Groq model discovery"
    )

    # Concurrency and Resource Safety Limits
    REPOMEDIC_MAX_CONCURRENT_SCANS: int = Field(
        default=2,
        ge=1,
        le=10,
        validation_alias=AliasChoices("REPOMEDIC_MAX_CONCURRENT_SCANS", "REPMEDIC_MAX_CONCURRENT_SCANS"),
        description="Max concurrent repository scans"
    )
    REPOMEDIC_MAX_QUEUE_CAPACITY: int = Field(
        default=20,
        ge=1,
        le=100,
        validation_alias=AliasChoices("REPOMEDIC_MAX_QUEUE_CAPACITY", "REPMEDIC_MAX_QUEUE_CAPACITY"),
        description="Max pending jobs in scan queue"
    )
    REPOMEDIC_SCAN_TIMEOUT_SECONDS: int = Field(
        default=300,
        ge=30,
        le=900,
        validation_alias=AliasChoices("REPOMEDIC_SCAN_TIMEOUT_SECONDS", "REPMEDIC_SCAN_TIMEOUT_SECONDS"),
        description="Max duration for an entire scan"
    )
    REPOMEDIC_MAX_REPO_MB: int = Field(
        default=250,
        ge=1,
        le=1000,
        validation_alias=AliasChoices("REPOMEDIC_MAX_REPO_MB", "REPMEDIC_MAX_REPO_MB"),
        description="Max cloned repository size in MB"
    )
    REPOMEDIC_MAX_REPO_FILES: int = Field(
        default=5000,
        ge=10,
        le=50000,
        validation_alias=AliasChoices("REPOMEDIC_MAX_REPO_FILES", "REPMEDIC_MAX_REPO_FILES"),
        description="Max file count inspected per scan"
    )
    REPOMEDIC_MAX_TEXT_FILE_BYTES: int = Field(
        default=400_000,
        ge=10_000,
        le=5_000_000,
        validation_alias=AliasChoices("REPOMEDIC_MAX_TEXT_FILE_BYTES", "REPMEDIC_MAX_TEXT_FILE_BYTES"),
        description="Max file size in bytes"
    )
    REPOMEDIC_MAX_AI_FINDINGS: int = Field(default=20, ge=1, le=50, description="Max findings dispatched to AI triage")
    REPOMEDIC_MAX_PER_RULE_FOR_AI: int = Field(default=3, ge=1, le=10, description="Max findings per rule key sent to AI")

    # Scanner Requirement Policies
    REPOMEDIC_SEMGREP_REQUIRED: bool = Field(default=False, description="If true, missing Semgrep marks audit as partial/failed")
    REPOMEDIC_OSV_REQUIRED: bool = Field(default=True, description="If true, OSV scan failure marks audit as partial/failed")
    REPOMEDIC_CUSTOM_RULES_REQUIRED: bool = Field(default=True, description="If true, custom rules failure marks audit as failed")
    REPOMEDIC_PYTHON_AST_REQUIRED: bool = Field(default=True, description="If true, Python AST failure marks audit as failed")
    REPOMEDIC_AI_TRIAGE_REQUIRED: bool = Field(default=False, description="If true, AI triage failure marks audit as partial")

    # Git History Scanner
    REPMEDIC_ENABLE_GIT_HISTORY: bool = Field(
        default=False,
        validation_alias=AliasChoices("REPMEDIC_ENABLE_GIT_HISTORY", "REPOMEDIC_ENABLE_GIT_HISTORY"),
        description="Enable read-only git history secret scanning"
    )
    REPMEDIC_MAX_HISTORY_COMMITS: int = Field(
        default=50,
        ge=1,
        le=500,
        validation_alias=AliasChoices("REPMEDIC_MAX_HISTORY_COMMITS", "REPOMEDIC_MAX_HISTORY_COMMITS"),
        description="Max commits inspected during git history scan"
    )
    REPMEDIC_GIT_HISTORY_REQUIRED: bool = Field(
        default=False,
        validation_alias=AliasChoices("REPMEDIC_GIT_HISTORY_REQUIRED", "REPOMEDIC_GIT_HISTORY_REQUIRED"),
        description="If true, git history failure marks audit as partial"
    )

    @field_validator("REPOMEDIC_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if value is None:
            return ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"]
        if isinstance(value, str):
            trimmed = value.strip()
            if not trimmed:
                return ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"]
            # Strip outer quotes if enclosed in single or double quotes
            if (trimmed.startswith("'") and trimmed.endswith("'")) or (trimmed.startswith('"') and trimmed.endswith('"')):
                trimmed = trimmed[1:-1].strip()
            if trimmed.startswith("[") and trimmed.endswith("]"):
                try:
                    import json
                    parsed = json.loads(trimmed)
                    if isinstance(parsed, list):
                        return [str(x).strip().strip("'\"") for x in parsed if str(x).strip().strip("'\"")]
                except Exception:
                    pass
                try:
                    import ast
                    parsed = ast.literal_eval(trimmed)
                    if isinstance(parsed, (list, tuple)):
                        return [str(x).strip().strip("'\"") for x in parsed if str(x).strip().strip("'\"")]
                except Exception:
                    inner = trimmed[1:-1].strip()
                    return [x.strip().strip("'\"") for x in inner.split(",") if x.strip().strip("'\"")]
            return [x.strip().strip("'\"") for x in trimmed.split(",") if x.strip().strip("'\"")]
        if isinstance(value, (list, tuple, set)):
            return [str(x).strip().strip("'\"") for x in value if str(x).strip().strip("'\"")]
        return [str(value).strip().strip("'\"")]

    @field_validator("GROQ_MODEL_PREFERENCES", mode="before")
    @classmethod
    def parse_groq_preferences(cls, value):
        if value is None:
            return [
                "openai/gpt-oss-20b",
                "llama-3.3-70b-versatile",
                "llama-3.1-8b-instant",
                "mixtral-8x7b-32768",
            ]
        if isinstance(value, str):
            trimmed = value.strip()
            if not trimmed:
                return [
                    "openai/gpt-oss-20b",
                    "llama-3.3-70b-versatile",
                    "llama-3.1-8b-instant",
                    "mixtral-8x7b-32768",
                ]
            if (trimmed.startswith("'") and trimmed.endswith("'")) or (trimmed.startswith('"') and trimmed.endswith('"')):
                trimmed = trimmed[1:-1].strip()
            if trimmed.startswith("[") and trimmed.endswith("]"):
                try:
                    import json
                    parsed = json.loads(trimmed)
                    if isinstance(parsed, list):
                        return [str(x).strip().strip("'\"") for x in parsed if str(x).strip().strip("'\"")]
                except Exception:
                    pass
                try:
                    import ast
                    parsed = ast.literal_eval(trimmed)
                    if isinstance(parsed, (list, tuple)):
                        return [str(x).strip().strip("'\"") for x in parsed if str(x).strip().strip("'\"")]
                except Exception:
                    inner = trimmed[1:-1].strip()
                    return [x.strip().strip("'\"") for x in inner.split(",") if x.strip().strip("'\"")]
            return [x.strip().strip("'\"") for x in trimmed.split(",") if x.strip().strip("'\"")]
        if isinstance(value, (list, tuple, set)):
            return [str(x).strip().strip("'\"") for x in value if str(x).strip().strip("'\"")]
        return [str(value).strip().strip("'\"")]

    @property
    def is_production(self) -> bool:
        return self.REPOMEDIC_ENV.lower() in ("production", "prod")


# Singleton instance
settings = Settings()
