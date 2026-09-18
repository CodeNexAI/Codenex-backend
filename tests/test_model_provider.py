"""Tests for the provider-independent local model provider."""

import asyncio

from app.models.mock_provider import MockModelProvider


def test_mock_model_provider_returns_deterministic_responses() -> None:
    """The local provider never requires network access or credentials."""
    provider = MockModelProvider()
    fallback = {"result": "fallback"}

    response = asyncio.run(provider.generate_response("Hello"))
    structured = asyncio.run(
        provider.generate_structured_response("Hello", "example", fallback)
    )

    assert response == "Mock response: Hello"
    assert structured == fallback
    assert structured is not fallback
