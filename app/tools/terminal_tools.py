from __future__ import annotations

from app.models.schemas import SandboxResult
from app.sandbox.runner import SandboxRunner


class TerminalTools:
    def __init__(self, runner: SandboxRunner) -> None:
        self.runner = runner

    def execute(self, workspace_path: str, task: str) -> SandboxResult:
        return self.runner.run_task(workspace_path=workspace_path, task=task)
