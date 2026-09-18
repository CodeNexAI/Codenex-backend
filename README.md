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
- Provider-independent model interface with a deterministic local mock provider
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

## Model providers

`ModelProvider` is independent of FastAPI and defines text and structured
response operations. `NebiusNemotronProvider` uses the documented
OpenAI-compatible Nebius Token Factory chat-completions API when
`NEBIUS_API_KEY`, `NEBIUS_BASE_URL`, and `NEMOTRON_MODEL` are configured.
`MockModelProvider` remains deterministic and network-free for local
development and tests. See [Nebius integration](docs/nebius-integration.md) for
configuration and separate integration-test instructions.

## API authentication

Set a strong `API_ACCESS_TOKEN` in `.env`. Stateful project, agent, test, and
sandbox APIs plus the agent WebSocket require it as a bearer token. This is a
single trusted-tenant foundation control; see [Security model](docs/security.md)
for its scope and production considerations.

## Sandbox

Generated code is not executed directly on the backend host. The backend uses a dedicated sandbox abstraction that is designed to invoke a separate Docker image with restricted networking, timeouts, and workspace scoping.

## Security

This foundation includes protections against path traversal, unsafe workspace access, unrestricted task dispatch, infinite agent retries, and accidental secret exposure in configuration.

See `docs/security.md`.

## API

Interactive OpenAPI documentation is available at `/docs`; OpenAPI JSON is
available at `/openapi.json`.

`GET /health` returns `{"status":"ok","service":"codenex-backend"}` and does
not require authentication. Every `/api/*` endpoint requires
`Authorization: Bearer <API_ACCESS_TOKEN>`. Missing or invalid credentials
return `401`; missing token configuration returns `503`.

| Endpoint | Purpose | Success | Additional errors |
| --- | --- | --- | --- |
| `POST /api/projects` | Create a project record from `name`, optional `description`, and supported `project_type`. | `201 ProjectResponse` | `422` validation |
| `GET /api/projects` | List project records. | `200 ProjectResponse[]` | — |
| `GET /api/projects/{project_id}` | Retrieve one project. | `200 ProjectResponse` | `404` not found |
| `DELETE /api/projects/{project_id}` | Remove a project and its assigned workspace. | `204` | `404` not found |
| `POST /api/agent/run` | Schedule a requirement workflow in the background. | `202 {session_id, status:"started"}` | `404` project not found, `422` validation |
| `GET /api/agent/{session_id}` | Read session status, retry count, timestamps, and persisted events. | `200 AgentSessionResponse` | `404` not found |
| `POST /api/sandbox/run` | Run the supported `task` (currently `pytest`) in Docker. | `200 SandboxResult` | `400` unsafe/unsupported task, `404` project, `503` sandbox |
| `POST /api/tests/run` | Run allow-listed `test_command` (currently `pytest`) in Docker and persist the result. | `201 TestResult` | `404` project, `503` sandbox |
| `GET /api/tests/{session_id}` | Retrieve the latest persisted test result. | `200 TestResult` | `404` not found |

## WebSocket

`/ws/agent/{session_id}` upgrades an authenticated bearer-token connection and
streams only that session's persisted and live events. Event payloads include
`session_id`, `stage`, `status`, `message`, timestamp, and optional metadata.
Connections missing a valid token close with policy-violation code `1008`.
The endpoint never exposes workspace paths, credentials, or arbitrary command
execution.

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
├── tests/
└── pyproject.toml
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
