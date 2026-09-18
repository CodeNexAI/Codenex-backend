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

Copy `.env.example` to `.env` and adjust values for local development. All
settings use the `CODENEX_` prefix and may be supplied as environment variables.

| Variable | Default | Purpose |
| --- | --- | --- |
| `CODENEX_APP_NAME` | `CodeNex Backend` | Application name used in logs |
| `CODENEX_ENVIRONMENT` | `development` | Runtime environment label |
| `CODENEX_LOG_LEVEL` | `INFO` | Application log-level setting |

Never commit `.env` files or credentials.

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
