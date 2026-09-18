# Security

CodeNex treats generated code as untrusted.

## Security Boundaries

- Untrusted code is intended to run in a dedicated sandbox container, not on the backend host process
- Sandbox tasks are restricted to an allowlist
- Workspace paths are validated to stay inside the configured workspace root
- File tools prevent path traversal outside the active workspace
- The orchestrator enforces a bounded retry count to prevent infinite loops
- Configuration is loaded from environment variables so secrets are not hard-coded

## Execution Limits

The sandbox executor applies:

- a timeout
- disabled networking (`--network none`)
- CPU and memory limits where practical
- a controlled working directory mount

These controls provide the initial Milestone 1 security foundation and can be extended later.
# Security Model

CodeNex treats requirements, generated files, and generated code as untrusted.
Project file operations are contained within each assigned workspace, and
sandbox execution uses Docker with a task allowlist, disabled networking,
capability dropping, non-root execution, resource limits, and a controlled
workspace mount.

## API access

Stateful HTTP routes and agent WebSocket connections require a configured
`API_ACCESS_TOKEN` bearer token. This is a single trusted-tenant control,
appropriate only for a deployment where all API users are trusted operators.
It is not multi-tenant authorization: a future production identity provider
must associate projects and sessions with authenticated principals.

Never commit `API_ACCESS_TOKEN`, model credentials, or `.env` files.
