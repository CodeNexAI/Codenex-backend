"""Authentication boundary tests for stateful API and WebSocket routes."""

from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect


def test_stateful_routes_require_a_bearer_token(app_instance) -> None:
    """Requests without the configured token fail before accessing project data."""
    with TestClient(app_instance) as unauthenticated_client:
        response = unauthenticated_client.get("/api/projects")

    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Invalid or missing API credentials."


def test_websocket_requires_a_bearer_token(app_instance) -> None:
    """WebSocket connections are rejected before the handshake is accepted."""
    with TestClient(app_instance) as unauthenticated_client:
        try:
            with unauthenticated_client.websocket_connect("/ws/agent/test-session"):
                pass
        except WebSocketDisconnect as exc:
            assert exc.code == 1008
        else:
            raise AssertionError("Expected unauthenticated WebSocket rejection.")
