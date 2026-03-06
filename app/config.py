"""Application configuration via Pydantic BaseSettings.

Settings are loaded from environment variables and optionally from a .env file.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Service identity ────────────────────────────────────────────────────
    service_name: str = Field(default="ascii-api", description="Service identifier")
    version: str = Field(default="0.1.0", description="Service version")

    # ── File upload limits ──────────────────────────────────────────────────
    max_file_size: int = Field(
        default=10_485_760,
        description="Maximum upload size in bytes (default: 10MB)",
    )
    max_pixels: int = Field(
        default=25_000_000,
        description="Maximum image pixels for decompression bomb protection (25MP)",
    )

    # ── ASCII conversion settings ───────────────────────────────────────────
    default_width: int = Field(
        default=100,
        ge=50,
        le=200,
        description="Default output width in characters",
    )
    max_width: int = Field(
        default=200,
        description="Maximum output width in characters",
    )
    height_factor: float = Field(
        default=0.5,
        ge=0.3,
        le=0.7,
        description="Default height factor for aspect ratio correction",
    )

    # ── Rate limiting ───────────────────────────────────────────────────────
    rate_limit: int = Field(
        default=10,
        description="Maximum requests per minute per IP",
    )

    # ── Authentication ──────────────────────────────────────────────────────
    auth_enabled: bool = Field(
        default=False,
        description="Enable API key authentication",
    )
    api_key: str | None = Field(
        default=None,
        description="API key for authentication (required if auth_enabled=True)",
    )

    # ── Logging ─────────────────────────────────────────────────────────────
    log_level: str = Field(
        default="INFO",
        description="Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL",
    )
    log_json_format: bool = Field(
        default=False,
        description="Output JSON format for Grafana Loki (vs human-readable console)",
    )

    # ── Sentry ──────────────────────────────────────────────────────────────
    sentry_dsn: str | None = Field(
        default=None,
        description="Sentry DSN for error tracking (leave empty to disable)",
    )
    sentry_environment: str = Field(
        default="development",
        description="Sentry environment name (development, staging, production)",
    )
    sentry_sample_rate: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Sentry trace sample rate (0.0 to 1.0)",
    )


def get_settings() -> Settings:
    """Return a Settings instance.

    This function is used as a FastAPI dependency so it can be overridden
    in tests without modifying global state.
    """
    return Settings()
