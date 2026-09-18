from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class APIError(BaseModel):
    code: str
    message: str


class APIErrorResponse(BaseModel):
    error: APIError


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    project_type: Literal["python", "fastapi", "react", "node", "flutter"]


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    project_type: str
    status: str
    created_at: datetime
    updated_at: datetime


class AgentRequest(BaseModel):
    project_id: str = Field(min_length=1)
    requirement: str = Field(min_length=1)


class AgentRunResponse(BaseModel):
    session_id: str
    status: Literal["started"]


class AgentEvent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    stage: str
    status: str
    message: str
    metadata: dict[str, Any] | None = None
    timestamp: datetime


class AgentSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    status: str
    retry_count: int
    started_at: datetime
    completed_at: datetime | None
    events: list[AgentEvent] = Field(default_factory=list)


class SandboxRequest(BaseModel):
    project_id: str = Field(min_length=1)
    task: Literal["pytest"] = "pytest"


class SandboxResult(BaseModel):
    status: Literal["passed", "failed", "error"]
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    duration: float = 0.0
    error_message: str | None = None


class TestRequest(BaseModel):
    project_id: str = Field(min_length=1)


class TestResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str | None = None
    session_id: str | None = None
    status: Literal["passed", "failed", "error"]
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    duration: float = 0.0
    stdout: str = ""
    stderr: str = ""
    created_at: datetime | None = None


class ImplementationPlan(BaseModel):
    project_type: str
    tasks: list[ImplementationTask]
    files: list[PlannedFile]
    dependencies: list[str] = Field(default_factory=list)
    testing_strategy: str
    constraints: list[str] = Field(default_factory=list)


class ImplementationTask(BaseModel):
    id: str = Field(min_length=1)
    description: str = Field(min_length=1)


class PlannedFile(BaseModel):
    path: str = Field(min_length=1)
    purpose: str = Field(min_length=1)


class CodeAction(BaseModel):
    action: Literal["create_file", "update_file", "delete_file"]
    path: str
    content: str | None = None


class ErrorReport(BaseModel):
    error: str
    root_cause: str
    fix: str


class DebugResult(ErrorReport):
    pass
