from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.agents.coder import CoderAgent
from app.agents.debugger import DebuggerAgent
from app.agents.orchestrator import Orchestrator
from app.agents.planner import PlannerAgent
from app.agents.tester import TesterAgent
from app.config.settings import Settings, get_settings
from app.database.database import get_db, get_session_factory
from app.models.nemotron import build_model_provider
from app.sandbox.executor import DockerSandboxExecutor
from app.sandbox.runner import SandboxRunner
from app.services.project_service import ProjectService
from app.services.session_service import EventManager, SessionService

_event_manager = EventManager()


SettingsDependency = Annotated[Settings, Depends(get_settings)]
DatabaseDependency = Annotated[Session, Depends(get_db)]


def get_event_manager() -> EventManager:
    return _event_manager


EventManagerDependency = Annotated[EventManager, Depends(get_event_manager)]


def get_project_service(
    db: DatabaseDependency, settings: SettingsDependency
) -> ProjectService:
    return ProjectService(db, settings)


def get_session_service(db: DatabaseDependency) -> SessionService:
    return SessionService(db, _event_manager)


def get_sandbox_runner(settings: SettingsDependency) -> SandboxRunner:
    executor = DockerSandboxExecutor(
        image=settings.sandbox_image,
        timeout=settings.sandbox_timeout,
        workspace_root=settings.workspace_root,
    )
    return SandboxRunner(executor)


SandboxRunnerDependency = Annotated[SandboxRunner, Depends(get_sandbox_runner)]
SessionServiceDependency = Annotated[SessionService, Depends(get_session_service)]


def get_orchestrator(settings: SettingsDependency) -> Orchestrator:
    provider = build_model_provider(settings)
    runner = get_sandbox_runner(settings)
    return Orchestrator(
        session_factory=get_session_factory(),
        event_manager=_event_manager,
        project_service_factory=lambda db: ProjectService(db, settings),
        planner=PlannerAgent(provider),
        coder=CoderAgent(provider),
        tester=TesterAgent(runner),
        debugger=DebuggerAgent(provider),
        max_retries=settings.max_agent_retries,
    )


OrchestratorDependency = Annotated[Orchestrator, Depends(get_orchestrator)]
