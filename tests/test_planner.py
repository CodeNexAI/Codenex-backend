"""Planner agent tests."""

import asyncio
from typing import Any

from app.agents.planner import PlannerAgent
from app.models.mock_provider import MockModelProvider
from app.models.provider import ModelProvider, ModelProviderError


def test_planner_returns_deterministic_structured_fallback_with_mock() -> None:
    """Mock-backed planning validates a structured, non-executing plan."""
    plan = asyncio.run(PlannerAgent(MockModelProvider()).plan("Build a student API"))

    assert plan.project_type == "generic"
    assert plan.tasks[0].id == "task-1"
    assert plan.files[0].path == "README.md"
    assert plan.testing_strategy
    assert plan.constraints


class InvalidPlanProvider(ModelProvider):
    """Provider that returns an invalid plan payload for validation testing."""

    async def generate_response(self, prompt: str) -> str:
        return prompt

    async def generate_structured_response(
        self,
        prompt: str,
        schema_name: str,
        fallback: dict[str, Any],
    ) -> dict[str, Any]:
        del prompt, schema_name, fallback
        return {"project_type": "fastapi"}


class FailingProvider(ModelProvider):
    """Provider that simulates an upstream provider error."""

    async def generate_response(self, prompt: str) -> str:
        raise ModelProviderError(prompt)

    async def generate_structured_response(
        self,
        prompt: str,
        schema_name: str,
        fallback: dict[str, Any],
    ) -> dict[str, Any]:
        del schema_name, fallback
        raise ModelProviderError(prompt)


def test_planner_falls_back_for_invalid_or_failed_provider_responses() -> None:
    """Malformed model output and provider failures return the safe fallback."""
    invalid = asyncio.run(PlannerAgent(InvalidPlanProvider()).plan("Build an API"))
    failed = asyncio.run(PlannerAgent(FailingProvider()).plan("Build an API"))

    assert invalid.files[0].path == "README.md"
    assert failed.files[0].path == "README.md"
