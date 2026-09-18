from __future__ import annotations

import importlib
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def app_instance(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "test.db"
    workspace_root = tmp_path / "workspaces"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("WORKSPACE_ROOT", str(workspace_root))
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173")

    from app.config.settings import get_settings

    get_settings.cache_clear()
    import app.main as main_module

    importlib.reload(main_module)
    application = main_module.create_app()
    return application


@pytest.fixture()
def client(app_instance):
    with TestClient(app_instance) as client:
        yield client
