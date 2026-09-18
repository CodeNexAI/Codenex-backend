from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any

import httpx

from app.config.settings import Settings
from app.models.schemas import CodeAction, DebugResult, ImplementationPlan


class ModelProvider(ABC):
    @abstractmethod
    async def generate_structured(self, prompt: str, schema_name: str, fallback: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class MockModelProvider(ModelProvider):
    async def generate_structured(self, prompt: str, schema_name: str, fallback: dict[str, Any]) -> dict[str, Any]:
        lowered = prompt.lower()
        if schema_name == "implementation_plan":
            plan = ImplementationPlan(
                project_type="fastapi" if "fastapi" in lowered else "generic",
                tasks=[
                    "Create application foundation",
                    "Add API endpoints",
                    "Add tests",
                ],
                files=[
                    "app/main.py",
                    "app/api/routes/projects.py",
                    "tests/test_projects.py",
                ],
                dependencies=["fastapi", "pytest"],
            )
            return plan.model_dump()
        if schema_name == "code_actions":
            actions = [
                CodeAction(
                    action="create_file",
                    path="README.md",
                    content="# Generated workspace\n",
                ).model_dump()
            ]
            return {"actions": actions}
        if schema_name == "debug_result":
            debug = DebugResult(
                error="Test execution failed",
                root_cause="Mock analysis detected a failing test",
                fix="Update the generated code and rerun the tests",
            )
            return debug.model_dump()
        return fallback


class NemotronProvider(ModelProvider):
    def __init__(self, settings: Settings) -> None:
        if not (settings.nebius_api_key and settings.nebius_base_url and settings.nemotron_model):
            raise ValueError("Nebius/Nemotron configuration is incomplete.")
        self._settings = settings

    async def generate_structured(self, prompt: str, schema_name: str, fallback: dict[str, Any]) -> dict[str, Any]:
        headers = {"Authorization": "Bearer " + self._settings.nebius_api_key, "Content-Type": "application/json"}
        payload = {
            "model": self._settings.nemotron_model,
            "messages": [
                {"role": "system", "content": f"Return valid JSON for schema: {schema_name}."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self._settings.nebius_base_url, headers=headers, json=payload)
            response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return json.loads(self._normalize_content(content))

    def _normalize_content(self, content: Any) -> str:
        if isinstance(content, list):
            content = "".join(
                item.get("text", "") if isinstance(item, dict) else str(item)
                for item in content
            )
        if not isinstance(content, str):
            return json.dumps(content)
        fenced = re.match(r"```(?:json)?\s*(.*?)\s*```", content, re.DOTALL)
        return fenced.group(1) if fenced else content


def build_model_provider(settings: Settings) -> ModelProvider:
    if settings.nebius_api_key and settings.nebius_base_url and settings.nemotron_model:
        return NemotronProvider(settings)
    return MockModelProvider()
