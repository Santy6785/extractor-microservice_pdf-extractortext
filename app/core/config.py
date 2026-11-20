"""Core configuration for the PDF extraction microservice.

Uses pydantic-settings to load from environment variables following Twelve‑Factor principles.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All defaults can be overridden via environment variables. For example:
    LOG_LEVEL=DEBUG uv run uvicorn app.main:app
    """

    # Server
    PORT: int = 80
    LOG_LEVEL: str = "INFO"

    # New extraction concurrency settings (used by the /extract endpoint)
    extract_concurrency: int = 2
    extract_queue_timeout: float = 20.0
    extract_max_queue: int = 8
    extract_cache_size: int = 32

    # PDF limits
    PDF_MAX_FILE_SIZE_MB: int = 50

    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)