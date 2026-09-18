from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path

from app.models.schemas import SandboxResult
from app.sandbox.security import ensure_within_base, validate_task


class SandboxExecutionError(RuntimeError):
    pass


class DockerSandboxExecutor:
    def __init__(self, image: str, timeout: int, workspace_root: str) -> None:
        self.image = image
        self.timeout = timeout
        self.workspace_root = workspace_root

    def run(self, workspace_path: str, task: str) -> SandboxResult:
        safe_task = validate_task(task)
        workspace = ensure_within_base(self.workspace_root, workspace_path)
        if shutil.which("docker") is None:
            raise SandboxExecutionError("Docker is required for sandbox execution.")

        command_map = {"pytest": ["pytest", "-q", "-p", "no:cacheprovider"]}
        command = command_map[safe_task]
        docker_command = [
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
            "--cpus",
            "1",
            "--memory",
            "512m",
            "-v",
            f"{workspace}:/workspace:ro",
            "-w",
            "/workspace",
            self.image,
            *command,
        ]
        started = time.perf_counter()
        try:
            completed = subprocess.run(
                docker_command,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return SandboxResult(
                status="error",
                exit_code=124,
                stdout=exc.stdout or "",
                stderr=exc.stderr or "",
                duration=time.perf_counter() - started,
                error_message="Sandbox execution timed out.",
            )

        status = "passed" if completed.returncode == 0 else "failed"
        return SandboxResult(
            status=status,
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            duration=time.perf_counter() - started,
        )
