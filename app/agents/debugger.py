from __future__ import annotations

from app.models.nemotron import ModelProvider
from app.models.schemas import DebugResult, TestResult


class DebuggerAgent:
    def __init__(self, provider: ModelProvider) -> None:
        self.provider = provider

    async def analyze_failure(self, test_result: TestResult) -> DebugResult:
        fallback = DebugResult(
            error=test_result.stderr or test_result.stdout or "Unknown test failure",
            root_cause="Tests did not pass",
            fix="Inspect the failing implementation and retry",
        )
        payload = await self.provider.generate_structured(
            prompt=(
                "Analyze test failure: "
                f"stdout={test_result.stdout}\nstderr={test_result.stderr}"
            ),
            schema_name="debug_result",
            fallback=fallback.model_dump(),
        )
        return DebugResult.model_validate(payload)
