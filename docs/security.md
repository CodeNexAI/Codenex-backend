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
