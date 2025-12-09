"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Find project root directory (where .env file is located)
PROJECT_ROOT = Path(__file__).parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Runtime settings for the YouTube Search API."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

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

    log_dir: str = Field(
        default="logs",
        description="Directory path for log files.",
    )
    log_file_enabled: bool = Field(
        default=True,
        description="Enable logging to file.",
    )
    log_file_max_bytes: int = Field(
        default=10485760,
        ge=1048576,
        description="Maximum log file size in bytes (default 10MB).",
    )
    log_file_backup_count: int = Field(
        default=5,
        ge=0,
        description="Number of backup log files to keep.",
    )

    # MCP Configuration - P2 Feature (Model Context Protocol Support)
    mcp_search_timeout: int = Field(
        default=15,
        ge=1,
        le=120,
        description="MCP tool call timeout in seconds (via MCP_SEARCH_TIMEOUT env var).",
    )
    mcp_search_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Number of retries for MCP tool calls (via MCP_SEARCH_RETRIES env var).",
    )
    mcp_port: int = Field(
        default=8441,
        ge=1,
        le=65535,
        description="MCP server port (for HTTP transport).",
    )

    enable_cache: bool = Field(
        default=True,
        description="Enable in-process cache usage alongside Redis toggle.",
    )
    enable_logging: bool = Field(
        default=True,
        description="Enable structured logging output.",
    )

    # Audio Download Feature (Feature 004) Configuration
    download_dir: str = Field(
        default="/tmp/youtube_audio",
        description="Directory path for storing downloaded audio files.",
    )
    download_base_url: str = Field(
        default="http://localhost:8000/downloads",
        description="Base URL for serving downloaded audio files.",
    )
    download_timeout: int = Field(
        default=300,
        ge=30,
        le=900,
        description="Download timeout in seconds (yt-dlp operation timeout).",
    )
    max_video_duration: int = Field(
        default=600,
        ge=60,
        le=3600,
        description="Maximum allowed video duration in seconds (10 minutes default).",
    )
    audio_bitrate: int = Field(
        default=128,
        ge=64,
        le=320,
        description="Audio bitrate in kbps for MP3 encoding.",
    )
    cache_ttl_hours: int = Field(
        default=24,
        ge=1,
        le=168,
        description="Cache TTL in hours for downloaded audio files.",
    )
    rate_limit_download_per_hour: int = Field(
        default=20,
        ge=1,
        le=1000,
        description="Rate limit: maximum downloads per hour per IP.",
    )
    rate_limit_static_per_minute: int = Field(
        default=60,
        ge=10,
        le=600,
        description="Rate limit: maximum static file serves per minute per IP.",
    )
    rate_limit_enabled: bool = Field(
        default=True,
        description="Enable rate limiting for download endpoints.",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()
