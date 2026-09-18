from __future__ import annotations

import logging

from app.models.provider import ModelProvider, ModelProviderError
from app.models.schemas import ImplementationPlan, ImplementationTask, PlannedFile

logger = logging.getLogger(__name__)


class PlannerAgent:
    def __init__(self, provider: ModelProvider) -> None:
        self.provider = provider

    async def plan(self, requirement: str) -> ImplementationPlan:
        fallback = self._fallback_plan()
        try:
            payload = await self.provider.generate_structured_response(
                prompt=(
                    "Create an implementation plan for the following software "
                    f"requirement:\n{requirement}"
                ),
                schema_name="implementation_plan",
                fallback=fallback.model_dump(),
            )
            return ImplementationPlan.model_validate(payload)
        except (ModelProviderError, ValueError):
            logger.warning("Planner received an unusable model response.")
            return fallback

    @staticmethod
    def _fallback_plan() -> ImplementationPlan:
        """Return a deterministic, non-executing plan for failed model calls."""
        return ImplementationPlan(
            project_type="generic",
            tasks=[
                ImplementationTask(
                    id="task-1",
                    description="Analyze the requirement and identify components.",
                )
            ],
            files=[
                PlannedFile(
                    path="README.md",
                    purpose="Document the planned project structure.",
                )
            ],
            dependencies=[],
            testing_strategy="Define unit tests before implementation.",
            constraints=["Do not execute code or create files during planning."],
        )
