from fastapi import APIRouter, HTTPException, status

from app.agents.tester import TesterAgent
from app.api.dependencies import SandboxRunnerDependency, SessionServiceDependency, SettingsDependency
from app.models.schemas import TestRequest, TestResult
from app.services.project_service import ProjectService

router = APIRouter(prefix="/api/tests", tags=["tests"])


@router.post("/run", response_model=TestResult, status_code=status.HTTP_201_CREATED)
async def run_tests(
    payload: TestRequest,
    session_service: SessionServiceDependency,
    runner: SandboxRunnerDependency,
    settings: SettingsDependency,
) -> TestResult:
    project_service = ProjectService(session_service.db, settings)
    project = project_service.get_project(payload.project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    session = session_service.create_session(project.id, status="testing")
    tester = TesterAgent(runner)
    result = await tester.run_tests(project.workspace_path)
    stored = session_service.save_test_result(session.id, result)
    session_service.update_session(session.id, result.status, completed=True)
    return TestResult.model_validate(stored)


@router.get("/{session_id}", response_model=TestResult)
async def get_test_result(session_id: str, session_service: SessionServiceDependency) -> TestResult:
    result = session_service.latest_test_result(session_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Test result not found")
    return TestResult.model_validate(result)
