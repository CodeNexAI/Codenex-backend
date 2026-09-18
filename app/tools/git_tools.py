from __future__ import annotations

import subprocess
from pathlib import Path

from app.sandbox.security import ensure_within_base


class GitTools:
    def __init__(self, workspace_root: str) -> None:
        self.workspace_root = workspace_root

    def _run(self, workspace_path: str, *args: str) -> subprocess.CompletedProcess[str]:
        workspace = ensure_within_base(self.workspace_root, workspace_path)
        return subprocess.run(
            ["git", *args],
            cwd=Path(workspace),
            capture_output=True,
            text=True,
            check=False,
        )

    def status(self, workspace_path: str) -> str:
        return self._run(workspace_path, "status", "--short").stdout

    def diff(self, workspace_path: str) -> str:
        return self._run(workspace_path, "diff").stdout

    def init(self, workspace_path: str) -> str:
        return self._run(workspace_path, "init").stdout

    def add(self, workspace_path: str, *paths: str) -> str:
        return self._run(workspace_path, "add", *paths).stdout

    def commit(self, workspace_path: str, message: str) -> str:
        return self._run(workspace_path, "commit", "-m", message).stdout
