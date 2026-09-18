from __future__ import annotations

from pathlib import Path


class SandboxSecurityError(ValueError):
    pass


_ALLOWED_TASKS = {"pytest", "python", "list_files"}


def ensure_within_base(base_path: str | Path, target_path: str | Path) -> Path:
    base = Path(base_path).resolve()
    target = Path(target_path).resolve()
    try:
        target.relative_to(base)
    except ValueError as exc:
        raise SandboxSecurityError("Path escapes the configured workspace root.")
    return target


def validate_task(task: str) -> str:
    if task not in _ALLOWED_TASKS:
        raise SandboxSecurityError("Unsupported sandbox task.")
    return task
