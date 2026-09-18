"""Database model and repository tests."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import AgentEvent, AgentSession, Base, Project
from app.database.models import TestResult as AgentTestResult
from app.database.repository import Repository


def test_repository_persists_related_records() -> None:
    """ORM records receive UUIDs, timestamps, and relationships in SQLite."""
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    with session_factory() as session:
        projects = Repository(session, Project)
        agent_sessions = Repository(session, AgentSession)
        events = Repository(session, AgentEvent)
        test_results = Repository(session, AgentTestResult)

        project = projects.add(
            Project(
                name="Demo",
                description="A test project",
                project_type="python",
                workspace_path="/tmp/demo",
            )
        )
        agent_session = agent_sessions.add(
            AgentSession(project_id=project.id, status="running")
        )
        event = events.add(
            AgentEvent(
                session_id=agent_session.id,
                stage="planning",
                status="complete",
                message="Plan created",
                event_metadata={"steps": 1},
            )
        )
        result = test_results.add(
            AgentTestResult(
                session_id=agent_session.id,
                status="passed",
                total=2,
                passed=2,
                failed=0,
                skipped=0,
                duration=0.5,
                stdout="2 passed",
            )
        )

        assert project.id
        assert project.created_at is not None
        assert project.updated_at is not None
        assert agent_session.id
        assert agent_session.started_at is not None
        assert event.id
        assert event.timestamp is not None
        assert result.id
        assert result.created_at is not None
        assert projects.get(project.id) == project
        assert agent_sessions.list() == [agent_session]
        assert events.list() == [event]
        assert test_results.list() == [result]
        assert project.sessions == [agent_session]
        assert agent_session.events == [event]
        assert agent_session.test_results == [result]
        assert event.event_metadata == {"steps": 1}
