from fastapi import APIRouter, HTTPException, status

from app.agents.tester import TesterAgent
from app.api.dependencies import (
    AuthenticatedDependency,
    SandboxRunnerDependency,
    SessionServiceDependency,
    SettingsDependency,
)
from app.models.schemas import TestRequest, TestResult
from app.sandbox.executor import SandboxExecutionError
from app.services.project_service import ProjectService

router = APIRouter(prefix="/api/tests", tags=["tests"])


@router.post(
    "/run",
    response_model=TestResult,
    status_code=status.HTTP_201_CREATED,
    summary="Run project tests",
    description=(
        "Creates a test session and runs the supported test task only in Docker."
    ),
    responses={
        401: {"description": "Missing or invalid bearer token."},
        404: {"description": "Project not found."},
        503: {"description": "Sandbox infrastructure is unavailable."},
    },
)
async def run_tests(
    payload: TestRequest,
    session_service: SessionServiceDependency,
    runner: SandboxRunnerDependency,
    settings: SettingsDependency,
    _auth: AuthenticatedDependency,
) -> TestResult:
    project_service = ProjectService(session_service.db, settings)
    project = project_service.get_project(payload.project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    session = session_service.create_session(project.id, status="testing")
    tester = TesterAgent(runner)
    try:
        result = await tester.run_tests(project.workspace_path, project.project_type)
        stored = session_service.save_test_result(session.id, result)
        session_service.update_session(session.id, result.status, completed=True)
        return TestResult.model_validate(stored)
    except SandboxExecutionError as exc:
        session_service.update_session(
            session.id, "failed", retry_count=0, completed=True
        )
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get(
    "/{session_id}",
    response_model=TestResult,
    summary="Get latest test result",
    responses={
        401: {"description": "Missing or invalid bearer token."},
        404: {"description": "Test result not found."},
    },
)
async def get_test_result(
    session_id: str,
    session_service: SessionServiceDependency,
    _auth: AuthenticatedDependency,
) -> TestResult:
    result = session_service.latest_test_result(session_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Test result not found")
    return TestResult.model_validate(result)
