from __future__ import annotations

from app.models.schemas import TestResult
from app.sandbox.runner import SandboxRunner
from app.tools.test_tools import parse_test_result


class TesterAgent:
    def __init__(self, runner: SandboxRunner) -> None:
        self.runner = runner

    async def run_tests(self, workspace_path: str) -> TestResult:
        return parse_test_result(self.runner.run_tests(workspace_path))
