"""Configuration tests."""

import pytest

from app.config import Settings, get_settings


def test_settings_use_safe_development_defaults() -> None:
    """Non-secret configuration has local-development defaults."""
    settings = Settings()

    assert settings.app_name == "CodeNex Backend"
    assert settings.app_env == "development"
    assert settings.database_url == "sqlite:///./codenex.db"
    assert settings.cors_origins == ["http://localhost:5173"]
    assert settings.max_agent_retries == 3


def test_settings_read_environment_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    """Environment variables override development defaults."""
    monkeypatch.setenv("APP_NAME", "CodeNex Test")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv(
        "CORS_ORIGINS", "https://app.example.com, https://admin.example.com"
    )
    monkeypatch.setenv("SANDBOX_TIMEOUT", "120")

    settings = Settings()

    assert settings.app_name == "CodeNex Test"
    assert settings.app_env == "test"
    assert settings.debug is False
    assert settings.cors_origins == [
        "https://app.example.com",
        "https://admin.example.com",
    ]
    assert settings.sandbox_timeout == 120


def test_get_settings_caches_instances() -> None:
    """The application reuses one settings instance during runtime."""
    get_settings.cache_clear()

    assert get_settings() is get_settings()

    get_settings.cache_clear()
