from __future__ import annotations

from app.models.provider import ModelProvider, ModelProviderError
from app.models.schemas import DebugResult, ImplementationPlan, TestResult


class DebuggerAgent:
    def __init__(self, provider: ModelProvider) -> None:
        self.provider = provider

    async def analyze_failure(
        self,
        requirement: str,
        plan: ImplementationPlan,
        source_files: dict[str, str],
        test_result: TestResult,
    ) -> DebugResult:
        """Analyze test failure without changing or executing project code."""
        fallback = DebugResult(
            error=test_result.stderr or test_result.stdout or "Unknown test failure",
            root_cause="Tests did not pass",
            explanation="Review the test output and relevant source files.",
            fix="Inspect the failing implementation and retry",
        )
        try:
            payload = await self.provider.generate_structured_response(
                prompt=(
                    f"Requirement: {requirement}\nPlan: {plan.model_dump_json()}\n"
                    f"Source files: {source_files}\nstdout: {test_result.stdout}\n"
                    f"stderr: {test_result.stderr}"
                ),
                schema_name="debug_result",
                fallback=fallback.model_dump(),
            )
            return DebugResult.model_validate(payload)
        except (ModelProviderError, ValueError):
            return fallback
