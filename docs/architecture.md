# Architecture

CodeNex Backend is the execution and orchestration layer for CodeNex AI.

## High-Level Flow

Frontend → REST API / WebSocket → Backend API → Orchestrator → Agents → Model Provider → Sandbox → Results

## Backend Layers

- `app/api`: HTTP and WebSocket interfaces
- `app/services`: project/session orchestration helpers and event broadcasting
- `app/agents`: planner, coder, tester, debugger, and orchestrator
- `app/models`: Pydantic schemas and model-provider abstractions
- `app/database`: SQLAlchemy models and session management
- `app/sandbox`: Docker execution boundary and task validation
- `app/tools`: safe helpers for file, terminal, test, and Git operations

## Frontend Boundary

The frontend is a separate repository and communicates with this backend only through REST API and WebSocket. Model-provider calls stay inside the backend.
