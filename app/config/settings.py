"""Typed runtime configuration loaded from environment variables."""

from functools import lru_cache
from typing import Annotated

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the CodeNex backend."""

    app_name: str = "CodeNex Backend"
    app_env: str = "development"
    debug: bool = False

    database_url: SecretStr | None = None

    nebius_api_key: SecretStr | None = None
    nebius_base_url: str = "https://api.studio.nebius.ai/v1"
    nemotron_model: str = "nvidia/Nemotron-3-Nano-30B-A3B"

    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    )

    sandbox_timeout: int = Field(default=300, gt=0)
    max_agent_retries: int = Field(default=3, ge=0)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        """Parse a comma-separated list of allowed CORS origins."""
        if isinstance(value, str):
            origins = [origin.strip() for origin in value.split(",") if origin.strip()]
            if not origins:
                raise ValueError("CORS_ORIGINS must contain at least one origin")
            return origins
        return value


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings."""
    return Settings()
