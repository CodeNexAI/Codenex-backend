from __future__ import annotations

from app.models.schemas import TestResult
from app.sandbox.runner import SandboxRunner
from app.tools.test_tools import parse_test_result


class TesterAgent:
    """Run supported project tests exclusively through the sandbox runner."""

    def __init__(self, runner: SandboxRunner) -> None:
        self.runner = runner

    async def run_tests(
        self,
        workspace_path: str,
        project_type: str = "python",
    ) -> TestResult:
        """Run pytest for supported Python projects without host execution."""
        if project_type not in {"python", "fastapi"}:
            raise ValueError(f"Testing is not yet supported for {project_type}.")
        return parse_test_result(self.runner.run_tests(workspace_path))
