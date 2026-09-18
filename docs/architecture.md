# Architecture

CodeNex Backend is the execution and orchestration layer for CodeNex AI.

## High-Level Flow

Frontend → authenticated REST API / WebSocket → Backend API → Orchestrator → Agents → Model Provider → Sandbox → Results

## Backend Layers

- `app/api`: HTTP and WebSocket interfaces
- `app/services`: project/session orchestration helpers and event broadcasting
- `app/agents`: planner, coder, tester, debugger, and orchestrator
- `app/models`: Pydantic schemas and model-provider abstractions
- `app/database`: SQLAlchemy models and session management
- `app/sandbox`: Docker execution boundary and task validation
- `app/tools`: safe helpers for file, terminal, test, and Git operations

## API Boundary

FastAPI publishes an OpenAPI description at `/openapi.json` and interactive
documentation at `/docs`. The health endpoint is public for deployment health
checks. Stateful REST endpoints and the session WebSocket require the configured
single-tenant bearer token. Routes delegate persistence to services and
repositories; they do not expose project workspace paths.

`/ws/agent/{session_id}` provides session-specific persisted and live agent
events. It is a progress channel, not a command-execution channel.

## Frontend Boundary

The frontend is a separate repository and communicates with this backend only through REST API and WebSocket. Model-provider calls stay inside the backend.
