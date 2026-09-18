from fastapi import APIRouter, HTTPException

from app.api.dependencies import (
    AuthenticatedDependency,
    DatabaseDependency,
    SandboxRunnerDependency,
    SettingsDependency,
)
from app.models.schemas import SandboxRequest, SandboxResult
from app.sandbox.executor import SandboxExecutionError
from app.sandbox.security import SandboxSecurityError
from app.services.project_service import ProjectService

router = APIRouter(prefix="/api/sandbox", tags=["sandbox"])


@router.post(
    "/run",
    response_model=SandboxResult,
    summary="Run an allow-listed sandbox task",
    description=(
        "Runs the requested supported task only inside the project's Docker sandbox."
    ),
    responses={
        400: {"description": "Unsupported task or unsafe sandbox request."},
        401: {"description": "Missing or invalid bearer token."},
        404: {"description": "Project not found."},
        503: {"description": "Sandbox infrastructure is unavailable."},
    },
)
async def run_sandbox(
    payload: SandboxRequest,
    db: DatabaseDependency,
    runner: SandboxRunnerDependency,
    settings: SettingsDependency,
    _auth: AuthenticatedDependency,
) -> SandboxResult:
    project = ProjectService(db, settings).get_project(payload.project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    try:
        return runner.run_task(project.workspace_path, payload.task)
    except SandboxSecurityError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except SandboxExecutionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
