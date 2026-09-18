from __future__ import annotations

import subprocess
from pathlib import Path

from app.sandbox.security import ensure_within_base


class GitTools:
    def __init__(self, workspace_root: str, allow_host_git: bool = False) -> None:
        self.workspace_root = workspace_root
        self.allow_host_git = allow_host_git

    def _run(self, workspace_path: str, *args: str) -> subprocess.CompletedProcess[str]:
        if not self.allow_host_git:
            raise RuntimeError(
                "Host git execution is disabled for untrusted workflows."
            )
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
        workspace = ensure_within_base(self.workspace_root, workspace_path)
        validated_paths = []
        for path in paths:
            validated_paths.append(
                str(
                    ensure_within_base(workspace, Path(workspace) / path).relative_to(
                        workspace
                    )
                )
            )
        return self._run(workspace_path, "add", *validated_paths).stdout

    def commit(self, workspace_path: str, message: str) -> str:
        result = self._run(workspace_path, "commit", "-m", message)
        return "\n".join(
            part for part in [result.stdout.strip(), result.stderr.strip()] if part
        )
