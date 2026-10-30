"""Core configuration for the PDF extraction microservice.

Uses pydantic-settings to load from environment variables following Twelve‑Factor principles.
"""

from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All defaults can be overridden via environment variables. For example:
    LOG_LEVEL=DEBUG uv run uvicorn app.main:app
    """

    # Server
    PORT: int = 80
    LOG_LEVEL: str = "INFO"

    # Concurrency control (legacy fields, kept for backward compatibility)
    CONCURRENCY_LIMIT: int = 5
    ACQUIRE_TIMEOUT: float = 0.01

    # New extraction concurrency settings (used by the /extract endpoint)
    extract_concurrency: int = Field(2, env="EXTRACT_CONCURRENCY")
    extract_queue_timeout: float = Field(20.0, env="EXTRACT_QUEUE_TIMEOUT")
    extract_max_queue: int = 8
    extract_cache_size: int = 32

    # PDF limits
    PDF_MAX_FILE_SIZE_MB: int = 50
    PDF_MAX_PAGES: int = 50

    class Config:
        env_prefix = ""
        case_sensitive = False