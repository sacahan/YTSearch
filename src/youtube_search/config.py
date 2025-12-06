"""Application configuration loaded from environment variables."""

from functools import lru_cache
from typing import Literal, Optional

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the YouTube Search API."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    youtube_base_url: AnyHttpUrl = Field(
        default="https://www.youtube.com/results",
        description="Base URL for YouTube search queries.",
    )
    youtube_timeout: int = Field(
        default=10,
        ge=1,
        le=60,
        description="HTTP timeout in seconds for YouTube requests.",
    )

    redis_host: str = Field(default="localhost", description="Redis host name or IP.")
    redis_port: int = Field(default=6379, ge=1, le=65535, description="Redis port.")
    redis_db: int = Field(default=0, ge=0, description="Redis database index.")
    redis_password: Optional[str] = Field(
        default=None,
        description="Redis authentication password (if required).",
    )
    redis_enabled: bool = Field(
        default=True,
        description="Toggle Redis cache usage for search results.",
    )
    redis_ttl_seconds: int = Field(
        default=3600,
        ge=1,
        description="Cache TTL in seconds for search results.",
    )

    api_host: str = Field(default="0.0.0.0", description="API bind host.")
    api_port: int = Field(default=8000, ge=1, le=65535, description="API bind port.")
    api_log_level: Literal["debug", "info", "warning", "error", "critical"] = Field(
        default="info",
        description="Log level for the API server.",
    )

    enable_cache: bool = Field(
        default=True,
        description="Enable in-process cache usage alongside Redis toggle.",
    )
    enable_logging: bool = Field(
        default=True,
        description="Enable structured logging output.",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()
