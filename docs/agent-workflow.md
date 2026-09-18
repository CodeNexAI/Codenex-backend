# Agent Workflow

The current Milestone 1 workflow is:

1. Planner analyzes the requirement and produces an `ImplementationPlan`
2. Coder turns the plan into `CodeAction` items and writes files in the workspace
3. SandboxRunner executes controlled tasks in the sandbox container
4. Tester parses sandbox output into a structured test result
5. Debugger analyzes failures and returns a structured fix suggestion
6. Orchestrator applies fixes and retries until tests pass or the retry limit is reached

The orchestrator uses a maximum retry count so the backend never enters an infinite loop.
