from __future__ import annotations

import logging

from sqlalchemy.orm import sessionmaker

from app.agents.coder import CoderAgent
from app.agents.debugger import DebuggerAgent
from app.agents.planner import PlannerAgent
from app.agents.tester import TesterAgent
from app.database.models import Project
from app.services.project_service import ProjectService
from app.services.session_service import EventManager, SessionService

logger = logging.getLogger(__name__)


class Orchestrator:
    def __init__(
        self,
        session_factory: sessionmaker,
        event_manager: EventManager,
        project_service_factory,
        planner: PlannerAgent,
        coder: CoderAgent,
        tester: TesterAgent,
        debugger: DebuggerAgent,
        max_retries: int = 3,
    ) -> None:
        self.session_factory = session_factory
        self.event_manager = event_manager
        self.project_service_factory = project_service_factory
        self.planner = planner
        self.coder = coder
        self.tester = tester
        self.debugger = debugger
        self.max_retries = max_retries

    async def run_session(self, session_id: str, requirement: str) -> None:
        with self.session_factory() as db:
            session_service = SessionService(db, self.event_manager)
            session = session_service.get_session(session_id)
            if session is None:
                raise ValueError("Session not found")
            project_service: ProjectService = self.project_service_factory(db)
            project = project_service.get_project(session.project_id)
            if project is None:
                raise ValueError("Project not found")

            try:
                await session_service.add_event(session_id, "planning", "running", "Analyzing requirements...")
                plan = await self.planner.plan(requirement)
                await session_service.add_event(session_id, "planning", "completed", "Implementation plan created.", {"files": plan.files})

                actions = await self.coder.generate_actions(plan)
                self.coder.apply_actions(project.workspace_path, actions)
                await session_service.add_event(session_id, "coding", "completed", "Generated project files.", {"actions": len(actions)})

                for attempt in range(self.max_retries + 1):
                    session_service.update_session(session_id, "testing", retry_count=attempt)
                    result = await self.tester.run_tests(project.workspace_path)
                    session_service.save_test_result(session_id, result)
                    await session_service.add_event(
                        session_id,
                        "testing",
                        result.status,
                        f"Test run completed with status: {result.status}.",
                        {"total": result.total, "failed": result.failed},
                    )
                    if result.status == "passed":
                        session_service.update_session(session_id, "completed", retry_count=attempt, completed=True)
                        await session_service.add_event(session_id, "completed", "completed", "Project completed successfully.")
                        return
                    if attempt >= self.max_retries:
                        session_service.update_session(session_id, "failed", retry_count=attempt, completed=True)
                        await session_service.add_event(session_id, "completed", "failed", "Agent retry limit reached.")
                        return

                    await session_service.add_event(session_id, "debugging", "running", "Analyzing test failures...")
                    debug_result = await self.debugger.analyze_failure(result)
                    fix_actions = await self.coder.generate_fix_actions(debug_result, plan)
                    self.coder.apply_actions(project.workspace_path, fix_actions)
                    await session_service.add_event(
                        session_id,
                        "debugging",
                        "completed",
                        debug_result.fix,
                        {"actions": len(fix_actions)},
                    )
            except Exception:  # pragma: no cover - defensive path
                logger.exception("orchestrator_failure", extra={"session_id": session_id})
                session_service.update_session(session_id, "failed", completed=True)
                await session_service.add_event(session_id, "completed", "failed", "Agent execution failed.")
                return
