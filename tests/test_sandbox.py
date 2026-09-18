import subprocess
from pathlib import Path

import pytest

from app.sandbox.executor import DockerSandboxExecutor, SandboxExecutionError
from app.sandbox.security import SandboxSecurityError, ensure_within_base, validate_task


def test_sandbox_security_rejects_invalid_task():
    with pytest.raises(SandboxSecurityError):
        validate_task("bash")


def test_path_traversal_prevention(tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with pytest.raises(SandboxSecurityError):
        ensure_within_base(workspace, workspace / ".." / "escape")


def test_executor_requires_docker(monkeypatch, tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    executor = DockerSandboxExecutor("sandbox:latest", 60, str(tmp_path))

    monkeypatch.setattr("shutil.which", lambda command: None)

    with pytest.raises(SandboxExecutionError):
        executor.run(str(workspace), "pytest")


def test_executor_captures_success_and_applies_isolation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    executor = DockerSandboxExecutor("sandbox:latest", 60, str(tmp_path))
    monkeypatch.setattr("shutil.which", lambda command: "/usr/bin/docker")
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args[0], returncode=0, stdout="1 passed", stderr=""
        ),
    )

    result = executor.run(str(workspace), "pytest")

    assert result.status == "passed"
    assert result.exit_code == 0


def test_executor_captures_failure_and_timeout(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    executor = DockerSandboxExecutor("sandbox:latest", 60, str(tmp_path))
    monkeypatch.setattr("shutil.which", lambda command: "/usr/bin/docker")

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args[0], returncode=1, stdout="", stderr="failure"
        ),
    )
    failed = executor.run(str(workspace), "pytest")

    def time_out(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(cmd="docker", timeout=60, output="partial")

    monkeypatch.setattr(subprocess, "run", time_out)
    timed_out = executor.run(str(workspace), "pytest")

    assert failed.status == "failed"
    assert failed.stderr == "failure"
    assert timed_out.status == "error"
    assert timed_out.exit_code == 124
