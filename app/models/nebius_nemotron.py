"""Nebius Token Factory provider for configured NVIDIA Nemotron models."""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from app.config.settings import Settings
from app.models.provider import ModelProvider, ModelProviderError

logger = logging.getLogger(__name__)


class NebiusNemotronProvider(ModelProvider):
    """Call the documented OpenAI-compatible Nebius Token Factory API."""

    def __init__(self, settings: Settings, timeout: float = 30.0) -> None:
        if not settings.nebius_api_key or not settings.nebius_base_url:
            raise ValueError("Nebius API key and base URL must be configured.")
        if not settings.nemotron_model:
            raise ValueError("A Nemotron model must be configured.")
        self._api_key = settings.nebius_api_key
        self._base_url = settings.nebius_base_url.rstrip("/")
        self._model = settings.nemotron_model
        self._timeout = timeout

    async def generate_response(self, prompt: str) -> str:
        """Send a chat completion request and return its text content."""
        payload = {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    f"{self._base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            logger.warning("Nebius model request timed out.")
            raise ModelProviderError("Model request timed out.") from exc
        except httpx.HTTPError as exc:
            logger.warning("Nebius model request failed with an HTTP error.")
            raise ModelProviderError("Model request failed.") from exc

        return self._extract_content(response)

    async def generate_structured_response(
        self,
        prompt: str,
        schema_name: str,
        fallback: dict[str, Any],
    ) -> dict[str, Any]:
        """Request JSON text and normalize it into a structured response."""
        del fallback
        content = await self.generate_response(
            f"{prompt}\n\nReturn only a JSON object matching the {schema_name} schema."
        )
        cleaned = content.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()
        try:
            decoded = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ModelProviderError("Model returned invalid JSON.") from exc
        if not isinstance(decoded, dict):
            raise ModelProviderError("Model returned a non-object JSON response.")
        return decoded

    @staticmethod
    def _extract_content(response: httpx.Response) -> str:
        """Extract `choices[0].message.content` from a documented response."""
        try:
            payload = response.json()
            content = payload["choices"][0]["message"]["content"]
        except (IndexError, KeyError, TypeError, ValueError) as exc:
            raise ModelProviderError("Model response had an invalid format.") from exc
        if not isinstance(content, str):
            raise ModelProviderError("Model response content must be text.")
        return content
