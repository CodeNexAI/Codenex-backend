"""Nebius Token Factory provider tests using mocked HTTP responses."""

import asyncio

import httpx
import pytest

from app.config.settings import Settings
from app.models.nebius_nemotron import NebiusNemotronProvider
from app.models.provider import ModelProviderError


def configured_settings() -> Settings:
    """Return settings containing non-sensitive test-only provider values."""
    return Settings(
        NEBIUS_API_KEY="test-key",
        NEBIUS_BASE_URL="https://api.tokenfactory.nebius.com/v1",
        NEMOTRON_MODEL="nvidia/Nemotron-test",
    )


def test_nebius_provider_sends_documented_chat_completion_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The provider uses bearer authentication and the documented endpoint."""
    captured: dict[str, object] = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {"choices": [{"message": {"content": "Model response"}}]}

    class FakeAsyncClient:
        def __init__(self, *, timeout: float) -> None:
            captured["timeout"] = timeout

        async def __aenter__(self) -> "FakeAsyncClient":
            return self

        async def __aexit__(self, *_: object) -> None:
            return None

        async def post(self, url: str, **kwargs: object) -> FakeResponse:
            captured["url"] = url
            captured.update(kwargs)
            return FakeResponse()

    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)
    response = asyncio.run(
        NebiusNemotronProvider(configured_settings()).generate_response("Hi")
    )

    assert response == "Model response"
    assert captured["url"] == "https://api.tokenfactory.nebius.com/v1/chat/completions"
    assert captured["headers"] == {
        "Authorization": "Bearer test-key",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    assert captured["json"] == {
        "model": "nvidia/Nemotron-test",
        "messages": [{"role": "user", "content": "Hi"}],
        "temperature": 0,
    }


@pytest.mark.parametrize(
    ("response_body", "error_message"),
    [
        ({}, "invalid format"),
        ({"choices": []}, "invalid format"),
        ({"choices": [{"message": {"content": {"text": "not text"}}}]}, "must be text"),
    ],
)
def test_nebius_provider_rejects_malformed_responses(
    monkeypatch: pytest.MonkeyPatch,
    response_body: dict[str, object],
    error_message: str,
) -> None:
    """Malformed Token Factory payloads do not reach agents."""

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return response_body

    class FakeAsyncClient:
        def __init__(self, *, timeout: float) -> None:
            pass

        async def __aenter__(self) -> "FakeAsyncClient":
            return self

        async def __aexit__(self, *_: object) -> None:
            return None

        async def post(self, *_: object, **__: object) -> FakeResponse:
            return FakeResponse()

    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)

    with pytest.raises(ModelProviderError, match=error_message):
        asyncio.run(
            NebiusNemotronProvider(configured_settings()).generate_response("Hi")
        )


def test_nebius_provider_wraps_http_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    """Timeouts and HTTP failures are normalized to provider errors."""

    class FakeAsyncClient:
        def __init__(self, *, timeout: float) -> None:
            pass

        async def __aenter__(self) -> "FakeAsyncClient":
            return self

        async def __aexit__(self, *_: object) -> None:
            return None

        async def post(self, *_: object, **__: object) -> None:
            raise httpx.TimeoutException("timed out")

    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)

    with pytest.raises(ModelProviderError, match="timed out"):
        asyncio.run(
            NebiusNemotronProvider(configured_settings()).generate_response("Hi")
        )


def test_nebius_provider_parses_structured_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Structured requests decode JSON returned in message content."""

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {"choices": [{"message": {"content": '{"project_type":"fastapi"}'}}]}

    class FakeAsyncClient:
        def __init__(self, *, timeout: float) -> None:
            pass

        async def __aenter__(self) -> "FakeAsyncClient":
            return self

        async def __aexit__(self, *_: object) -> None:
            return None

        async def post(self, *_: object, **__: object) -> FakeResponse:
            return FakeResponse()

    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)
    result = asyncio.run(
        NebiusNemotronProvider(configured_settings()).generate_structured_response(
            "Plan a project",
            "implementation_plan",
            {},
        )
    )

    assert result == {"project_type": "fastapi"}
