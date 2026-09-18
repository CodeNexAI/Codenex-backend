from __future__ import annotations

from app.models.provider import ModelProvider
from app.models.schemas import ImplementationPlan


class PlannerAgent:
    def __init__(self, provider: ModelProvider) -> None:
        self.provider = provider

    async def plan(self, requirement: str) -> ImplementationPlan:
        fallback = ImplementationPlan(
            project_type="generic",
            tasks=["Analyze requirement", "Create files", "Add tests"],
            files=["README.md"],
            dependencies=[],
        )
        payload = await self.provider.generate_structured_response(
            prompt=f"Create an implementation plan for: {requirement}",
            schema_name="implementation_plan",
            fallback=fallback.model_dump(),
        )
        return ImplementationPlan.model_validate(payload)
