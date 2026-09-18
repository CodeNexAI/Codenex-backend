"""Database model and repository tests."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import (
    AgentEvent,
    AgentSession,
    Base,
    Project,
)
from app.database.models import TestResult as AgentTestResult
from app.database.repository import (
    AgentEventRepository,
    AgentSessionRepository,
    ProjectRepository,
)
from app.database.repository import TestResultRepository as AgentTestResultRepository


def test_repositories_persist_related_records() -> None:
    """Repositories persist records, generated IDs, timestamps, and relationships."""
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    with session_factory() as session:
        project = Project(
            name="Demo",
            description="A test project",
            project_type="python",
            workspace_path="/tmp/demo",
        )
        project = ProjectRepository(session).add(project)
        agent_session = AgentSession(project_id=project.id, status="running")
        agent_session = AgentSessionRepository(session).add(agent_session)
        event = AgentEvent(
            session_id=agent_session.id,
            stage="planning",
            status="complete",
            message="Plan created",
            metadata_={"steps": 1},
        )
        result = AgentTestResult(
            session_id=agent_session.id,
            status="passed",
            total=2,
            passed=2,
            failed=0,
            skipped=0,
            duration=0.5,
            stdout="2 passed",
        )
        AgentEventRepository(session).add(event)
        AgentTestResultRepository(session).add(result)
        session.commit()

        assert project.id
        assert project.created_at is not None
        assert project.updated_at is not None
        assert agent_session.id
        assert agent_session.started_at is not None
        assert event.id
        assert event.timestamp is not None
        assert result.id
        assert result.created_at is not None
        assert ProjectRepository(session).get_by_id(project.id) == project
        assert AgentSessionRepository(session).list_for_project(project.id) == [
            agent_session
        ]
        assert AgentEventRepository(session).list_for_session(agent_session.id) == [
            event
        ]
        test_result_repository = AgentTestResultRepository(session)
        assert test_result_repository.list_for_session(agent_session.id) == [result]
        assert project.agent_sessions == [agent_session]
        assert agent_session.events == [event]
        assert agent_session.test_results == [result]
        assert event.metadata_ == {"steps": 1}
