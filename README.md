# CodeNex AI Backend

> **From Idea to Working Code — With AI**

CodeNex AI is an agentic coding assistant being built for the NVIDIA x Nebius
Global AI Hackathon. This repository contains the backend foundation for the
Coding and Agentic Engineering track.

The current milestone provides a clean FastAPI service, environment-based
configuration, health checking, developer tooling, and a container definition.
It intentionally does not implement agents, model integrations, persistence,
sandbox execution, code generation, or a frontend.

## Quick start

**Requirements:** Python 3.11 or newer.

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`. Interactive API documentation
is available at `/docs`.

```bash
curl http://127.0.0.1:8000/health
```

```json
{
  "status": "ok",
  "service": "codenex-backend"
}
```

## Configuration

Copy the template before running the service:

```bash
cp .env.example .env
```

Settings are read from `.env` for local development and can be overridden by
environment variables. `APP_NAME`, `APP_ENV`, `DEBUG`, `DATABASE_URL`,
`NEBIUS_API_KEY`, `NEBIUS_BASE_URL`, `NEMOTRON_MODEL`, `CORS_ORIGINS`,
`SANDBOX_TIMEOUT`, and `MAX_AGENT_RETRIES` are supported.

`CORS_ORIGINS` accepts a comma-separated list of origins. `NEBIUS_API_KEY` and
`DATABASE_URL` are treated as sensitive values and are never logged or exposed
by the API. The current foundation does not connect to a database or model
provider. Never commit `.env` files or credentials.

## Development

```bash
# Run tests
pytest

# Run linting
ruff check .

# Run type checks
mypy
```

Convenience scripts are available as `./scripts/dev.sh` and `./scripts/test.sh`.

## Architecture

See [docs/architecture.md](docs/architecture.md) for the current foundation
and intended product direction.

## License

This project is licensed under the [MIT License](LICENSE).
