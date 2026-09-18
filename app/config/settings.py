"""Typed runtime configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from the local environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="CodeNex Backend", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=True, alias="DEBUG")
    database_url: str = Field(default="sqlite:///./codenex.db", alias="DATABASE_URL")
    cors_origins_raw: str = Field(
        default="http://localhost:5173",
        alias="CORS_ORIGINS",
    )
    workspace_root: str = Field(default="./workspaces", alias="WORKSPACE_ROOT")
    sandbox_image: str = Field(
        default="codenex-sandbox:latest",
        alias="SANDBOX_IMAGE",
    )
    sandbox_timeout: int = Field(default=60, alias="SANDBOX_TIMEOUT")
    max_agent_retries: int = Field(default=3, alias="MAX_AGENT_RETRIES")
    nebius_api_key: str = Field(default="", alias="NEBIUS_API_KEY")
    nebius_base_url: str = Field(
        default="https://api.tokenfactory.nebius.com/v1",
        alias="NEBIUS_BASE_URL",
    )
    nemotron_model: str = Field(default="", alias="NEMOTRON_MODEL")

    @property
    def cors_origins(self) -> list[str]:
        """Return non-empty origins parsed from the comma-separated setting."""
        return [
            item.strip() for item in self.cors_origins_raw.split(",") if item.strip()
        ]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached runtime settings."""
    return Settings()
