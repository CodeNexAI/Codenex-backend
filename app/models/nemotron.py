from __future__ import annotations

import ipaddress
import json
import re
from abc import ABC, abstractmethod
from typing import Any
from urllib.parse import urlparse

import httpx

from app.config.settings import Settings
from app.models.schemas import CodeAction, DebugResult, ImplementationPlan


class ModelProvider(ABC):
    @abstractmethod
    async def generate_structured(
        self, prompt: str, schema_name: str, fallback: dict[str, Any]
    ) -> dict[str, Any]:
        raise NotImplementedError


class MockModelProvider(ModelProvider):
    async def generate_structured(
        self, prompt: str, schema_name: str, fallback: dict[str, Any]
    ) -> dict[str, Any]:
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
        if not (
            settings.nebius_api_key
            and settings.nebius_base_url
            and settings.nemotron_model
        ):
            raise ValueError("Nebius/Nemotron configuration is incomplete.")
        self._validate_base_url(settings.nebius_base_url)
        self._settings = settings

    async def generate_structured(
        self, prompt: str, schema_name: str, fallback: dict[str, Any]
    ) -> dict[str, Any]:
        headers = {
            "Authorization": "Bearer " + self._settings.nebius_api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._settings.nemotron_model,
            "messages": [
                {
                    "role": "system",
                    "content": f"Return valid JSON for schema: {schema_name}.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self._settings.nebius_base_url, headers=headers, json=payload
                )
                response.raise_for_status()
            body = response.json()
            choice = body.get("choices", [{}])[0]
            message = choice.get("message", {})
            content = message.get("content")
            if content is None:
                return fallback
            return json.loads(self._normalize_content(content))
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError):
            return fallback

    def _normalize_content(self, content: Any) -> str:
        if isinstance(content, list):
            content = "".join(
                item.get("text", "") if isinstance(item, dict) else str(item)
                for item in content
            )
        if not isinstance(content, str):
            return json.dumps(content)
        fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", content, re.DOTALL)
        return fenced.group(1) if fenced else content

    def _validate_base_url(self, base_url: str) -> None:
        parsed = urlparse(base_url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise ValueError("Nebius base URL must be a valid HTTPS endpoint.")
        hostname = parsed.hostname.lower()
        if hostname in {"localhost", "127.0.0.1", "::1"}:
            raise ValueError("Nebius base URL must not target a local endpoint.")
        try:
            address = ipaddress.ip_address(hostname)
        except ValueError:
            return
        if address.is_private or address.is_loopback or address.is_link_local:
            raise ValueError("Nebius base URL must not target a private endpoint.")


def build_model_provider(settings: Settings) -> ModelProvider:
    if settings.nebius_api_key and settings.nebius_base_url and settings.nemotron_model:
        return NemotronProvider(settings)
    return MockModelProvider()
