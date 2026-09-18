from __future__ import annotations

from app.models.schemas import SandboxResult
from app.sandbox.executor import DockerSandboxExecutor


class SandboxRunner:
    def __init__(self, executor: DockerSandboxExecutor) -> None:
        self.executor = executor

    def run_task(self, workspace_path: str, task: str) -> SandboxResult:
        return self.executor.run(workspace_path=workspace_path, task=task)

    def run_tests(self, workspace_path: str) -> SandboxResult:
        return self.run_task(workspace_path=workspace_path, task="pytest")
