from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from fastapi import WebSocket
from sqlalchemy.orm import Session, selectinload

from app.database.models import AgentEvent as AgentEventModel
from app.database.models import AgentSession, TestResult as TestResultModel
from app.models.schemas import AgentEvent, AgentSessionResponse, TestResult


class EventManager:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[session_id].add(websocket)

    def disconnect(self, session_id: str, websocket: WebSocket) -> None:
        if session_id in self._connections:
            self._connections[session_id].discard(websocket)
            if not self._connections[session_id]:
                self._connections.pop(session_id, None)

    async def broadcast(self, session_id: str, payload: dict[str, Any]) -> None:
        for websocket in list(self._connections.get(session_id, set())):
            try:
                await websocket.send_json(payload)
            except Exception:
                self.disconnect(session_id, websocket)


class SessionService:
    def __init__(self, db: Session, event_manager: EventManager) -> None:
        self.db = db
        self.event_manager = event_manager

    def create_session(self, project_id: str, status: str = "started") -> AgentSession:
        session = AgentSession(project_id=project_id, status=status)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session(self, session_id: str) -> AgentSession | None:
        return (
            self.db.query(AgentSession)
            .options(selectinload(AgentSession.events))
            .filter(AgentSession.id == session_id)
            .first()
        )

    async def add_event(
        self,
        session_id: str,
        stage: str,
        status: str,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> AgentEventModel:
        event = AgentEventModel(
            session_id=session_id,
            stage=stage,
            status=status,
            message=message,
            event_metadata=metadata,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        await self.event_manager.broadcast(session_id, self._event_schema(event).model_dump(mode="json"))
        return event

    def update_session(self, session_id: str, status: str, retry_count: int | None = None, completed: bool = False) -> AgentSession:
        session = self.db.get(AgentSession, session_id)
        if session is None:
            raise ValueError("Session not found")
        session.status = status
        if retry_count is not None:
            session.retry_count = retry_count
        if completed:
            session.completed_at = datetime.now(timezone.utc)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def save_test_result(self, session_id: str, result: TestResult) -> TestResultModel:
        record = TestResultModel(
            session_id=session_id,
            status=result.status,
            total=result.total,
            passed=result.passed,
            failed=result.failed,
            skipped=result.skipped,
            duration=result.duration,
            stdout=result.stdout,
            stderr=result.stderr,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def latest_test_result(self, session_id: str) -> TestResultModel | None:
        return (
            self.db.query(TestResultModel)
            .filter(TestResultModel.session_id == session_id)
            .order_by(TestResultModel.created_at.desc())
            .first()
        )

    def to_response(self, session: AgentSession) -> AgentSessionResponse:
        return AgentSessionResponse(
            id=session.id,
            project_id=session.project_id,
            status=session.status,
            retry_count=session.retry_count,
            started_at=session.started_at,
            completed_at=session.completed_at,
            events=[self._event_schema(event) for event in sorted(session.events, key=lambda item: item.timestamp)],
        )

    def _event_schema(self, event: AgentEventModel) -> AgentEvent:
        return AgentEvent(
            id=event.id,
            session_id=event.session_id,
            stage=event.stage,
            status=event.status,
            message=event.message,
            metadata=event.event_metadata,
            timestamp=event.timestamp,
        )
