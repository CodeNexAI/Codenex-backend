# CodeNex Sandbox

This container executes generated project code in isolation from the backend
process. It is intentionally separate so untrusted code is never run directly
on the backend host.

The backend runs only an allow-listed test task in Docker. Each invocation:

- mounts only the assigned project workspace at `/workspace`
- disables networking
- drops Linux capabilities and prevents privilege escalation
- limits CPU, memory, process count, and wall-clock execution time
- uses a read-only root filesystem with a bounded temporary filesystem
- runs as a non-root user and removes the container after completion

The workspace mount remains writable so tests can create their own temporary
files. Docker daemon security remains part of the deployment trust boundary;
run the backend only in an environment where its Docker access is controlled.
