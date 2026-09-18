# CodeNex AI

From Idea to Working Code — With AI

## Overview

CodeNex AI is an agentic coding assistant for the NVIDIA x Nebius Global AI Hackathon. This repository provides the backend foundation for Track 1 and focuses on a modular FastAPI service that can plan, generate, test, and debug code inside an isolated sandbox.

## Problem

Developers often have requirements but still need to translate them into plans, code, tests, and execution workflows. Doing that manually slows iteration and makes it harder to build reliable automation.

## Solution

CodeNex Backend provides a clean backend foundation with API endpoints, WebSocket events, database persistence, pluggable model providers, an agent orchestration loop, and a Docker-based sandbox boundary for untrusted generated code.

## Features

- FastAPI backend with async endpoints and WebSocket support
- SQLite + SQLAlchemy persistence for projects, sessions, events, and test results
- Planner, Coder, Tester, Debugger, and Orchestrator foundation classes
- Nemotron model provider abstraction with a mock provider for local development
- Docker sandbox abstraction for controlled execution
- Safe file, terminal, test, and Git tooling primitives
- Structured error responses
- Environment-driven configuration and CORS

## Architecture

The frontend lives in a separate `codenex-frontend` repository and talks to this backend over REST and WebSocket. The backend coordinates planning, coding, testing, and debugging while keeping NVIDIA Nemotron access behind a model-provider abstraction.

See `docs/architecture.md`.

## Agent Workflow

The current foundation implements the orchestration path:

Planner → Coder → Sandbox → Tester → Debugger → Coder

with a bounded retry loop.

See `docs/agent-workflow.md`.

## NVIDIA Nemotron Integration

CodeNex uses NVIDIA Nemotron through Nebius Token Factory as the intelligence layer for coding agents. Agent code does not call Nebius directly; the backend routes those requests through `NemotronProvider`, and local development falls back to `MockModelProvider` when credentials are not configured.

## Nebius Token Factory Integration

Configure the following environment variables to enable the real provider:

- `NEBIUS_API_KEY`
- `NEBIUS_BASE_URL`
- `NEMOTRON_MODEL`

See `docs/nebius-integration.md`.

## Sandbox

Generated code is not executed directly on the backend host. The backend uses a dedicated sandbox abstraction that is designed to invoke a separate Docker image with restricted networking, timeouts, and workspace scoping.

## Security

This foundation includes protections against path traversal, unsafe workspace access, unrestricted task dispatch, infinite agent retries, and accidental secret exposure in configuration.

See `docs/security.md`.

## API

Implemented foundation endpoints:

- `GET /health`
- `POST /api/projects`
- `GET /api/projects`
- `GET /api/projects/{project_id}`
- `DELETE /api/projects/{project_id}`
- `POST /api/agent/run`
- `GET /api/agent/{session_id}`
- `POST /api/sandbox/run`
- `POST /api/tests/run`
- `GET /api/tests/{session_id}`

## WebSocket

- `GET /ws/agent/{session_id}` upgrades to a WebSocket connection and streams session events.

## Tech Stack

- Python 3.11+
- FastAPI
- Pydantic v2
- SQLAlchemy
- SQLite
- HTTPX
- pytest
- Docker
- python-dotenv

## Repository Structure

```text
codenex-backend/
├── app/
├── docs/
├── sandbox/
├── scripts/
└── tests/
```

## Environment Variables

Copy `.env.example` to `.env` and set values as needed.

Key variables:

- `APP_ENV`
- `DEBUG`
- `DATABASE_URL`
- `CORS_ORIGINS`
- `WORKSPACE_ROOT`
- `SANDBOX_IMAGE`
- `SANDBOX_TIMEOUT`
- `MAX_AGENT_RETRIES`
- `NEBIUS_API_KEY`
- `NEBIUS_BASE_URL`
- `NEMOTRON_MODEL`

## Local Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

or run:

```bash
./scripts/setup.sh
```

## Running the Backend

```bash
uvicorn app.main:app --reload
```

or run:

```bash
./scripts/dev.sh
```

## Running Tests

```bash
pytest -q
```

or run:

```bash
./scripts/test.sh
```

## Example Request

```bash
curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -d '{"name":"student-api","description":"FastAPI CRUD API","project_type":"fastapi"}'
```

## Example Agent Workflow

1. Create a project
2. Start an agent session with a requirement
3. Receive planning/coding/testing/debugging events over WebSocket
4. Inspect session state and persisted test results

## Frontend Integration

The frontend should call only this backend over REST and WebSocket. It must not directly call NVIDIA Nemotron or Nebius endpoints.

## Hackathon Track

Coding and Agentic Engineering Track

## Future Improvements

- Expand real Nemotron prompt design and schema enforcement
- Add richer sandbox resource controls and artifact capture
- Persist generated files and execution bundles per session
- Support more project templates and language runtimes

## License

MIT License. See `LICENSE`.
