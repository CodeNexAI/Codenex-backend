"""Single-tenant bearer-token protection for stateful API surfaces."""

from __future__ import annotations

import hmac

from fastapi import Depends, HTTPException, WebSocket, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config.settings import Settings, get_settings

bearer_scheme = HTTPBearer(auto_error=False)


def _configured_token(settings: Settings) -> str:
    """Return the configured access token or fail closed."""
    if settings.api_access_token is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API authentication is not configured.",
        )
    return settings.api_access_token.get_secret_value()


def require_api_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> None:
    """Require a valid configured bearer token without logging credentials."""
    expected_token = _configured_token(settings)
    if credentials is None or not hmac.compare_digest(
        credentials.credentials,
        expected_token,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def authorize_websocket(websocket: WebSocket) -> bool:
    """Authorize a WebSocket handshake before accepting the connection."""
    authorization = websocket.headers.get("authorization", "")
    scheme, _, token = authorization.partition(" ")
    try:
        expected_token = _configured_token(get_settings())
    except HTTPException:
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        return False
    if scheme.lower() != "bearer" or not hmac.compare_digest(token, expected_token):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return False
    return True
