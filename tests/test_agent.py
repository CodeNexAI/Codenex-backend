import asyncio
from pathlib import Path

from app.agents.coder import CoderAgent
from app.agents.debugger import DebuggerAgent
from app.agents.orchestrator import Orchestrator
from app.agents.planner import PlannerAgent
from app.agents.tester import TesterAgent as BackendTesterAgent
from app.api.dependencies import get_orchestrator
from app.config.settings import get_settings
from app.database.database import get_session_factory
from app.models.nemotron import MockModelProvider, NemotronProvider
from app.models import schemas
from app.services.project_service import ProjectService
from app.services.session_service import EventManager, SessionService


class FakeRunner:
    def __init__(self, result: schemas.SandboxResult) -> None:
        self.result = result

    def run_tests(self, workspace_path: str) -> schemas.SandboxResult:
        return self.result


class FailingTester:
    async def run_tests(self, workspace_path: str) -> schemas.TestResult:
        return schemas.TestResult(status="failed", total=1, passed=0, failed=1, stderr="boom")


def test_mock_model_provider_and_planner_and_debugger():
    provider = MockModelProvider()
    plan = asyncio.run(PlannerAgent(provider).plan("Create a FastAPI student API"))
    debug = asyncio.run(
        DebuggerAgent(provider).analyze_failure(
            schemas.TestResult(status="failed", total=1, failed=1, passed=0, stderr="NameError")
        )
    )

    assert plan.project_type == "fastapi"
    assert plan.files
    assert "rerun" in debug.fix.lower()


def test_nemotron_provider_normalizes_fenced_and_block_content():
    provider = NemotronProvider(
        get_settings().model_copy(
            update={
                "nebius_api_key": "key",
                "nebius_base_url": "https://example.com",
                "nemotron_model": "model",
            }
        )
    )

    assert provider._normalize_content("```json\n{\"status\": \"ok\"}\n```") == "{\"status\": \"ok\"}"
    assert provider._normalize_content([{"text": "{\"status\": \"ok\"}"}]) == "{\"status\": \"ok\"}"


def test_coder_agent_creates_files(tmp_path: Path):
    provider = MockModelProvider()
    plan = asyncio.run(PlannerAgent(provider).plan("Create a FastAPI student API"))
    actions = asyncio.run(CoderAgent(provider).generate_actions(plan))

    CoderAgent(provider).apply_actions(str(tmp_path), actions)

    assert (tmp_path / "README.md").exists()


def test_tester_agent_parses_results():
    result = schemas.SandboxResult(status="failed", exit_code=1, stdout="1 failed, 2 passed in 0.12s", stderr="", duration=0.12)
    parsed = asyncio.run(BackendTesterAgent(FakeRunner(result)).run_tests("/tmp/workspace"))

    assert parsed.total == 3
    assert parsed.failed == 1
    assert parsed.passed == 2


def test_agent_session_creation(client, app_instance):
    class FakeOrchestrator:
        event_manager = EventManager()

        async def run_session(self, session_id: str, requirement: str) -> None:
            return None

    app_instance.dependency_overrides[get_orchestrator] = lambda: FakeOrchestrator()
    project = client.post("/api/projects", json={"name": "Agent Project", "project_type": "fastapi"}).json()

    response = client.post(
        "/api/agent/run",
        json={"project_id": project["id"], "requirement": "Create a FastAPI student API"},
    )

    assert response.status_code == 202
    assert response.json()["status"] == "started"


def test_agent_websocket_endpoint(client, app_instance):
    class FakeOrchestrator:
        event_manager = EventManager()

        async def run_session(self, session_id: str, requirement: str) -> None:
            return None

    app_instance.dependency_overrides[get_orchestrator] = lambda: FakeOrchestrator()
    project = client.post("/api/projects", json={"name": "WebSocket Project", "project_type": "fastapi"}).json()
    response = client.post(
        "/api/agent/run",
        json={"project_id": project["id"], "requirement": "Create a FastAPI student API"},
    )
    session_id = response.json()["session_id"]

    with client.websocket_connect(f"/ws/agent/{session_id}"):
        pass


def test_orchestrator_retry_limit(app_instance):
    settings = get_settings()
    session_factory = get_session_factory()
    provider = MockModelProvider()
    event_manager = EventManager()

    with session_factory() as db:
        project = ProjectService(db, settings).create_project(
            payload=type("ProjectPayload", (), {"name": "Retry Project", "description": None, "project_type": "fastapi"})()
        )
        session = SessionService(db, event_manager).create_session(project.id)

    orchestrator = Orchestrator(
        session_factory=session_factory,
        event_manager=event_manager,
        project_service_factory=lambda db: ProjectService(db, settings),
        planner=PlannerAgent(provider),
        coder=CoderAgent(provider),
        tester=FailingTester(),
        debugger=DebuggerAgent(provider),
        max_retries=3,
    )

    asyncio.run(orchestrator.run_session(session.id, "Create a FastAPI student API"))

    with session_factory() as db:
        stored_session = SessionService(db, event_manager).get_session(session.id)
        assert stored_session is not None
        assert stored_session.status == "failed"
        assert stored_session.retry_count == 3
