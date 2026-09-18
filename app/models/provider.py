"""Provider-independent model interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ModelProviderError(RuntimeError):
    """Raised when a model provider cannot produce a usable response."""


class ModelProvider(ABC):
    """Contract used by CodeNex components to request model output."""

    @abstractmethod
    async def generate_response(self, prompt: str) -> str:
        """Generate a text response for a prompt."""

    @abstractmethod
    async def generate_structured_response(
        self,
        prompt: str,
        schema_name: str,
        fallback: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate an object-shaped response using a caller-provided fallback."""
