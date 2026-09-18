"""Deterministic local-only model provider for development and tests."""

from __future__ import annotations

from typing import Any

from app.models.provider import ModelProvider


class MockModelProvider(ModelProvider):
    """Return deterministic responses without network access or API credentials."""

    async def generate_response(self, prompt: str) -> str:
        """Return a stable local response."""
        return f"Mock response: {prompt}"

    async def generate_structured_response(
        self,
        prompt: str,
        schema_name: str,
        fallback: dict[str, Any],
    ) -> dict[str, Any]:
        """Return the caller's deterministic fallback without contacting a provider."""
        del prompt, schema_name
        return fallback.copy()
