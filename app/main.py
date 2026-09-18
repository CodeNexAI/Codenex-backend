"""FastAPI application entry point."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

from app.config import Settings, get_settings


class HealthResponse(BaseModel):
    """Response returned by the service health endpoint."""

    status: str
    service: str


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Configure application startup and shutdown."""
    settings = get_settings()
    logging.getLogger("codenex").info(
        "Starting %s in %s environment",
        settings.app_name,
        settings.app_env,
    )
    yield
    logging.getLogger("codenex").info("Shutting down %s", settings.app_name)


settings: Settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Backend foundation for CodeNex AI.",
    version="0.1.0",
    debug=settings.debug,
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check() -> HealthResponse:
    """Report that the API is available."""
    return HealthResponse(status="ok", service="codenex-backend")
