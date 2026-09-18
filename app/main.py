from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.dependencies import get_event_manager
from app.api.routes.agent import router as agent_router
from app.api.routes.health import router as health_router
from app.api.routes.projects import router as projects_router
from app.api.routes.sandbox import router as sandbox_router
from app.api.routes.tests import router as tests_router
from app.config.settings import get_settings
from app.database.database import configure_database, create_tables, get_session_factory
from app.services.session_service import SessionService

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("codenex")


def create_app() -> FastAPI:
    settings = get_settings()
    configure_database(settings.database_url)
    create_tables()

    app = FastAPI(title="CodeNex AI Backend", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"error": {"code": "HTTP_ERROR", "message": str(exc.detail)}})

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"error": {"code": "INVALID_REQUEST", "message": "Invalid request."}})

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        if request.scope["type"] != "http":
            raise exc
        logger.exception("unhandled_exception")
        return JSONResponse(status_code=500, content={"error": {"code": "INTERNAL_ERROR", "message": "An internal error occurred."}})

    app.include_router(health_router)
    app.include_router(projects_router)
    app.include_router(agent_router)
    app.include_router(sandbox_router)
    app.include_router(tests_router)

    @app.websocket("/ws/agent/{session_id}")
    async def agent_websocket(websocket: WebSocket, session_id: str) -> None:
        event_manager = get_event_manager()
        await event_manager.connect(session_id, websocket)
        historical_events = []
        try:
            with get_session_factory()() as db:
                session_service = SessionService(db, event_manager)
                session = session_service.get_session(session_id)
                if session is not None:
                    historical_events = session_service.to_response(session).events
            for event in historical_events:
                await websocket.send_json(event.model_dump(mode="json"))
            while True:
                message = await websocket.receive()
                if message["type"] in {"websocket.disconnect", "websocket.close"}:
                    break
        except WebSocketDisconnect:
            pass
        finally:
            await event_manager.disconnect(session_id, websocket)

    return app


app = create_app()
