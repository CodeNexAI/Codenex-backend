import asyncio
from pathlib import Path

import httpx

from app.agents.coder import CoderAgent
from app.agents.debugger import DebuggerAgent
from app.agents.orchestrator import Orchestrator
from app.agents.planner import PlannerAgent
from app.agents.tester import TesterAgent as BackendTesterAgent
from app.api.dependencies import get_orchestrator, get_sandbox_runner
from app.config.settings import get_settings
from app.database.database import get_session_factory
from app.database.models import AgentSession as AgentSessionModel
from app.models import schemas
from app.models.nemotron import MockModelProvider, NemotronProvider
from app.sandbox.executor import SandboxExecutionError
from app.services.project_service import ProjectService
from app.services.session_service import EventManager, SessionService


class FakeRunner:
    def __init__(self, result: schemas.SandboxResult) -> None:
        self.result = result

    def run_tests(self, workspace_path: str) -> schemas.SandboxResult:
        return self.result


class FailingTester:
    async def run_tests(self, workspace_path: str) -> schemas.TestResult:
        return schemas.TestResult(
            status="failed", total=1, passed=0, failed=1, stderr="boom"
        )


def test_mock_model_provider_and_planner_and_debugger():
    provider = MockModelProvider()
    plan = asyncio.run(PlannerAgent(provider).plan("Create a FastAPI student API"))
    debug = asyncio.run(
        DebuggerAgent(provider).analyze_failure(
            schemas.TestResult(
                status="failed", total=1, failed=1, passed=0, stderr="NameError"
            )
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

    assert (
        provider._normalize_content('prefix\n```json\n{"status": "ok"}\n```')
        == '{"status": "ok"}'
    )
    assert (
        provider._normalize_content([{"text": '{"status": "ok"}'}])
        == '{"status": "ok"}'
    )


def test_nemotron_provider_generate_structured_handles_alternate_and_invalid_payloads(
    monkeypatch,
):
    provider = NemotronProvider(
        get_settings().model_copy(
            update={
                "nebius_api_key": "key",
                "nebius_base_url": "https://example.com",
                "nemotron_model": "model",
            }
        )
    )

    responses = [
        {
            "choices": [
                {
                    "message": {
                        "content": (
                            "```json\n"
                            '{"project_type":"fastapi","tasks":[],"files":[],"dependencies":[]}'
                            "\n```"
                        )
                    }
                }
            ]
        },
        {"choices": [{"message": {}}]},
    ]

    class FakeResponse:
        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self.payload

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            self.index = 0

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, url, headers, json):
            payload = responses.pop(0)
            return FakeResponse(payload)

    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)

    structured = asyncio.run(
        provider.generate_structured(
            "plan",
            "implementation_plan",
            {"project_type": "generic", "tasks": [], "files": [], "dependencies": []},
        )
    )
    fallback = asyncio.run(
        provider.generate_structured(
            "plan",
            "implementation_plan",
            {"project_type": "generic", "tasks": [], "files": [], "dependencies": []},
        )
    )

    assert structured["project_type"] == "fastapi"
    assert fallback["project_type"] == "generic"


def test_nemotron_provider_rejects_non_https_local_urls():
    settings = get_settings().model_copy(
        update={
            "nebius_api_key": "key",
            "nebius_base_url": "http://localhost:8080",
            "nemotron_model": "model",
        }
    )

    try:
        NemotronProvider(settings)
    except ValueError as exc:
        assert "must" in str(exc).lower()
    else:
        raise AssertionError("Expected invalid Nebius URL to be rejected")


def test_nemotron_provider_falls_back_on_http_error(monkeypatch):
    provider = NemotronProvider(
        get_settings().model_copy(
            update={
                "nebius_api_key": "key",
                "nebius_base_url": "https://example.com",
                "nemotron_model": "model",
            }
        )
    )

    class FailingAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, url, headers, json):
            raise httpx.ConnectError("boom")

    monkeypatch.setattr(httpx, "AsyncClient", FailingAsyncClient)

    fallback = asyncio.run(
        provider.generate_structured(
            "plan",
            "implementation_plan",
            {"project_type": "generic", "tasks": [], "files": [], "dependencies": []},
        )
    )

    assert fallback["project_type"] == "generic"


def test_coder_agent_creates_files(tmp_path: Path):
    provider = MockModelProvider()
    plan = asyncio.run(PlannerAgent(provider).plan("Create a FastAPI student API"))
    actions = asyncio.run(CoderAgent(provider).generate_actions(plan))

    CoderAgent(provider).apply_actions(str(tmp_path), actions)

    assert (tmp_path / "README.md").exists()


def test_tester_agent_parses_results():
    result = schemas.SandboxResult(
        status="failed",
        exit_code=1,
        stdout="1 failed, 2 passed in 0.12s",
        stderr="",
        duration=0.12,
    )
    parsed = asyncio.run(
        BackendTesterAgent(FakeRunner(result)).run_tests("/tmp/workspace")
    )

    assert parsed.total == 3
    assert parsed.failed == 1
    assert parsed.passed == 2


def test_agent_session_creation(client, app_instance):
    class FakeOrchestrator:
        event_manager = EventManager()

        async def run_session(self, session_id: str, requirement: str) -> None:
            return None

    app_instance.dependency_overrides[get_orchestrator] = lambda: FakeOrchestrator()
    project = client.post(
        "/api/projects", json={"name": "Agent Project", "project_type": "fastapi"}
    ).json()

    response = client.post(
        "/api/agent/run",
        json={
            "project_id": project["id"],
            "requirement": "Create a FastAPI student API",
        },
    )

    assert response.status_code == 202
    assert response.json()["status"] == "started"


def test_agent_websocket_endpoint(client, app_instance):
    class FakeOrchestrator:
        event_manager = EventManager()

        async def run_session(self, session_id: str, requirement: str) -> None:
            return None

    app_instance.dependency_overrides[get_orchestrator] = lambda: FakeOrchestrator()
    project = client.post(
        "/api/projects", json={"name": "WebSocket Project", "project_type": "fastapi"}
    ).json()
    response = client.post(
        "/api/agent/run",
        json={
            "project_id": project["id"],
            "requirement": "Create a FastAPI student API",
        },
    )
    session_id = response.json()["session_id"]

    with client.websocket_connect(f"/ws/agent/{session_id}"):
        pass


def test_run_tests_endpoint_persists_results(client, app_instance):
    class FakeRunner:
        def run_tests(self, workspace_path: str) -> schemas.SandboxResult:
            return schemas.SandboxResult(
                status="passed",
                exit_code=0,
                stdout="3 passed in 0.10s",
                stderr="",
                duration=0.10,
            )

    app_instance.dependency_overrides[get_sandbox_runner] = lambda: FakeRunner()
    project = client.post(
        "/api/projects", json={"name": "Test Project", "project_type": "fastapi"}
    ).json()

    response = client.post("/api/tests/run", json={"project_id": project["id"]})

    assert response.status_code == 201
    result = response.json()
    assert result["status"] == "passed"
    assert result["passed"] == 3
    assert result["session_id"]

    lookup = client.get(f"/api/tests/{result['session_id']}")
    assert lookup.status_code == 200
    assert lookup.json()["status"] == "passed"


def test_run_tests_endpoint_marks_session_failed_on_sandbox_error(client, app_instance):
    class FailingRunner:
        def run_tests(self, workspace_path: str) -> schemas.SandboxResult:
            raise SandboxExecutionError("Docker is required for sandbox execution.")

    app_instance.dependency_overrides[get_sandbox_runner] = lambda: FailingRunner()
    project = client.post(
        "/api/projects",
        json={"name": "Failing Test Project", "project_type": "fastapi"},
    ).json()

    response = client.post("/api/tests/run", json={"project_id": project["id"]})

    assert response.status_code == 503
    assert (
        response.json()["error"]["message"]
        == "Docker is required for sandbox execution."
    )

    with get_session_factory()() as db:
        session = (
            db.query(AgentSessionModel)
            .order_by(AgentSessionModel.started_at.desc())
            .first()
        )
        assert session is not None
        assert session.project_id == project["id"]
        assert session.status == "failed"
        assert session.completed_at is not None

    lookup = client.get(f"/api/tests/{session.id}")
    assert lookup.status_code == 404


def test_orchestrator_retry_limit(app_instance):
    settings = get_settings()
    session_factory = get_session_factory()
    provider = MockModelProvider()
    event_manager = EventManager()

    with session_factory() as db:
        project = ProjectService(db, settings).create_project(
            payload=type(
                "ProjectPayload",
                (),
                {
                    "name": "Retry Project",
                    "description": None,
                    "project_type": "fastapi",
                },
            )()
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
