from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from app.api.dependencies import (
    AuthenticatedDependency,
    OrchestratorDependency,
    SessionServiceDependency,
    SettingsDependency,
)
from app.models.schemas import AgentRequest, AgentRunResponse, AgentSessionResponse
from app.services.project_service import ProjectService

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post(
    "/run",
    response_model=AgentRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start an agent session",
    description=(
        "Creates a session and schedules the orchestrator in the background. "
        "Progress is available from the session endpoint and WebSocket."
    ),
    responses={
        401: {"description": "Missing or invalid bearer token."},
        404: {"description": "Project not found."},
    },
)
async def run_agent(
    payload: AgentRequest,
    background_tasks: BackgroundTasks,
    session_service: SessionServiceDependency,
    orchestrator: OrchestratorDependency,
    settings: SettingsDependency,
    _auth: AuthenticatedDependency,
) -> AgentRunResponse:
    project_service = ProjectService(session_service.db, settings)
    if project_service.get_project(payload.project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    session = session_service.create_session(payload.project_id, status="started")
    background_tasks.add_task(orchestrator.run_session, session.id, payload.requirement)
    return AgentRunResponse(session_id=session.id, status="started")


@router.get(
    "/{session_id}",
    response_model=AgentSessionResponse,
    summary="Get agent session progress",
    description="Returns persisted session state, timestamps, retry count, and events.",
    responses={
        401: {"description": "Missing or invalid bearer token."},
        404: {"description": "Session not found."},
    },
)
async def get_agent_session(
    session_id: str,
    session_service: SessionServiceDependency,
    _auth: AuthenticatedDependency,
) -> AgentSessionResponse:
    session = session_service.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session_service.to_response(session)
