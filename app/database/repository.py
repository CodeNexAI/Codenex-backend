"""Repository abstractions for database access."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import AgentEvent, AgentSession, Project, TestResult


class ProjectRepository:
    """Persist and retrieve project records."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, project: Project) -> Project:
        """Store a project and return it with database-generated fields."""
        self.session.add(project)
        self.session.flush()
        return project

    def get_by_id(self, project_id: str) -> Project | None:
        """Return a project by ID, if it exists."""
        return self.session.get(Project, project_id)

    def list_all(self) -> list[Project]:
        """Return all projects ordered by creation time."""
        return list(self.session.scalars(select(Project).order_by(Project.created_at)))


class AgentSessionRepository:
    """Persist and retrieve agent session records."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, agent_session: AgentSession) -> AgentSession:
        """Store an agent session and return it with database-generated fields."""
        self.session.add(agent_session)
        self.session.flush()
        return agent_session

    def list_for_project(self, project_id: str) -> list[AgentSession]:
        """Return sessions belonging to one project."""
        statement = (
            select(AgentSession)
            .where(AgentSession.project_id == project_id)
            .order_by(AgentSession.started_at)
        )
        return list(self.session.scalars(statement))


class AgentEventRepository:
    """Persist and retrieve agent event records."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, event: AgentEvent) -> AgentEvent:
        """Store an agent event and return it with database-generated fields."""
        self.session.add(event)
        self.session.flush()
        return event

    def list_for_session(self, session_id: str) -> list[AgentEvent]:
        """Return events belonging to one agent session."""
        statement = (
            select(AgentEvent)
            .where(AgentEvent.session_id == session_id)
            .order_by(AgentEvent.timestamp)
        )
        return list(self.session.scalars(statement))


class TestResultRepository:
    """Persist and retrieve test-result records."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, result: TestResult) -> TestResult:
        """Store a test result and return it with database-generated fields."""
        self.session.add(result)
        self.session.flush()
        return result

    def list_for_session(self, session_id: str) -> list[TestResult]:
        """Return test results belonging to one agent session."""
        statement = (
            select(TestResult)
            .where(TestResult.session_id == session_id)
            .order_by(TestResult.created_at)
        )
        return list(self.session.scalars(statement))
