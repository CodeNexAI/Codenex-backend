from __future__ import annotations

import logging

from sqlalchemy.orm import sessionmaker

from app.agents.coder import CoderAgent
from app.agents.debugger import DebuggerAgent
from app.agents.planner import PlannerAgent
from app.agents.tester import TesterAgent
from app.services.project_service import ProjectService
from app.services.session_service import EventManager, SessionService
from app.tools.file_tools import FileToolError, list_files, read_file

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

    async def run_session(self, session_id: str, requirement: str) -> str:
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
                await session_service.add_event(
                    session_id, "planning", "running", "Analyzing requirements..."
                )
                plan = await self.planner.plan(requirement)
                await session_service.add_event(
                    session_id,
                    "planning",
                    "completed",
                    "Implementation plan created.",
                    {
                        "files": [
                            planned_file.model_dump() for planned_file in plan.files
                        ]
                    },
                )

                actions = await self.coder.generate_actions(
                    requirement,
                    plan,
                )
                self.coder.apply_actions(project.workspace_path, actions)
                await session_service.add_event(
                    session_id,
                    "coding",
                    "completed",
                    "Generated project files.",
                    {"actions": len(actions)},
                )

                for attempt in range(self.max_retries + 1):
                    session_service.update_session(
                        session_id, "testing", retry_count=attempt
                    )
                    result = await self.tester.run_tests(
                        project.workspace_path,
                        project.project_type,
                    )
                    session_service.save_test_result(session_id, result)
                    await session_service.add_event(
                        session_id,
                        "testing",
                        result.status,
                        f"Test run completed with status: {result.status}.",
                        {"total": result.total, "failed": result.failed},
                    )
                    if result.status == "passed":
                        session_service.update_session(
                            session_id, "completed", retry_count=attempt, completed=True
                        )
                        await session_service.add_event(
                            session_id,
                            "completed",
                            "completed",
                            "Project completed successfully.",
                        )
                        return "completed"
                    if result.exit_code == 124:
                        session_service.update_session(
                            session_id,
                            "timeout",
                            retry_count=attempt,
                            completed=True,
                        )
                        await session_service.add_event(
                            session_id,
                            "failed",
                            "timeout",
                            "Sandbox test execution timed out.",
                        )
                        return "timeout"
                    if attempt >= self.max_retries:
                        session_service.update_session(
                            session_id, "failed", retry_count=attempt, completed=True
                        )
                        await session_service.add_event(
                            session_id,
                            "completed",
                            "failed",
                            "Agent retry limit reached.",
                        )
                        return

                    await session_service.add_event(
                        session_id, "debugging", "running", "Analyzing test failures..."
                    )
                    debug_result = await self.debugger.analyze_failure(
                        requirement,
                        plan,
                        self._source_context(project.workspace_path),
                        result,
                    )
                    fix_actions = await self.coder.generate_fix_actions(
                        debug_result, plan
                    )
                    self.coder.apply_actions(project.workspace_path, fix_actions)
                    await session_service.add_event(
                        session_id,
                        "debugging",
                        "completed",
                        debug_result.fix,
                        {"actions": len(fix_actions)},
                    )
            except Exception:
                logger.exception(
                    "orchestrator_failure", extra={"session_id": session_id}
                )
                session_service.update_session(session_id, "failed", completed=True)
                await session_service.add_event(
                    session_id, "completed", "failed", "Agent execution failed."
                )
                return "failed"

    @staticmethod
    def _source_context(workspace_path: str) -> dict[str, str]:
        """Read bounded workspace files for debugging without host-file access."""
        try:
            return {
                path: read_file(workspace_path, path)
                for path in list_files(workspace_path)
            }
        except FileToolError:
            return {}
