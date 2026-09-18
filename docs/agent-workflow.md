# Agent Workflow

The current Milestone 1 workflow is:

1. Planner analyzes the requirement and produces an `ImplementationPlan`
2. Coder turns the plan into `CodeAction` items and writes files in the workspace
3. SandboxRunner executes controlled tasks in the sandbox container
4. Tester parses sandbox output into a structured test result
5. Debugger analyzes failures and returns a structured fix suggestion
6. Orchestrator applies fixes and retries until tests pass or the retry limit is reached

The orchestrator uses a maximum retry count so the backend never enters an infinite loop.

## Session progress API

`POST /api/agent/run` creates an agent session and schedules this workflow in a
background task, returning `202 Accepted` immediately. `GET /api/agent/{session_id}`
returns the persisted session status, retry count, timestamps, and event
history. The authenticated `/ws/agent/{session_id}` endpoint replays persisted
events and streams live, session-specific progress.

Events use the `planning`, `coding`, `testing`, `debugging`, `completed`, and
`failed` stages. Each has a status, message, timestamp, and optional metadata;
events must not include credentials or host filesystem details.
