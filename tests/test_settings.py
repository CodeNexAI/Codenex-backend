"""Configuration tests."""

import pytest
from pydantic import ValidationError

from app.config import Settings, get_settings


def test_settings_use_safe_development_defaults() -> None:
    """Non-secret configuration has local-development defaults."""
    settings = Settings()

    assert settings.app_name == "CodeNex Backend"
    assert settings.app_env == "development"
    assert settings.debug is False
    assert settings.database_url.get_secret_value() == "sqlite:///./codenex.db"
    assert settings.nebius_api_key is None
    assert settings.cors_origins == [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    assert settings.sandbox_timeout == 300
    assert settings.max_agent_retries == 3


def test_settings_read_environment_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    """Environment variables override development defaults."""
    monkeypatch.setenv("APP_NAME", "CodeNex Test")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:password@localhost/codenex")
    monkeypatch.setenv("NEBIUS_API_KEY", "test-api-key")
    monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com, https://admin.example.com")
    monkeypatch.setenv("SANDBOX_TIMEOUT", "120")
    monkeypatch.setenv("MAX_AGENT_RETRIES", "5")

    settings = Settings()

    assert settings.app_name == "CodeNex Test"
    assert settings.app_env == "test"
    assert settings.debug is True
    assert settings.database_url is not None
    assert settings.database_url.get_secret_value() == (
        "postgresql://user:password@localhost/codenex"
    )
    assert settings.nebius_api_key is not None
    assert settings.nebius_api_key.get_secret_value() == "test-api-key"
    assert settings.cors_origins == [
        "https://app.example.com",
        "https://admin.example.com",
    ]
    assert settings.sandbox_timeout == 120
    assert settings.max_agent_retries == 5


def test_settings_reject_invalid_operational_limits() -> None:
    """Invalid timeout and retry limits are rejected."""
    with pytest.raises(ValidationError):
        Settings(sandbox_timeout=0)

    with pytest.raises(ValidationError):
        Settings(max_agent_retries=-1)


def test_get_settings_caches_instances() -> None:
    """The application reuses one settings instance during runtime."""
    get_settings.cache_clear()

    assert get_settings() is get_settings()

    get_settings.cache_clear()
