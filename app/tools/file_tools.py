"""Safe, workspace-scoped file operations for generated project files."""

from __future__ import annotations

from pathlib import Path

MAX_FILE_SIZE_BYTES = 1_048_576
MAX_FILES = 10_000


class FileToolError(ValueError):
    """A structured error raised for invalid workspace file operations."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


def _resolve(base_path: str, relative_path: str) -> Path:
    base = Path(base_path).resolve()
    candidate = Path(relative_path)
    if candidate.is_absolute():
        raise FileToolError("INVALID_PATH", "Absolute paths are not allowed.")
    if not relative_path or relative_path in {".", ".."}:
        raise FileToolError("INVALID_PATH", "A project-relative file path is required.")

    target = (base / candidate).resolve()
    try:
        target.relative_to(base)
    except ValueError as exc:
        raise FileToolError(
            "PATH_TRAVERSAL",
            "Path escapes the assigned project workspace.",
        ) from exc
    return target


def validate_relative_path(base_path: str, relative_path: str) -> None:
    """Validate that a project-relative path remains inside its workspace."""
    _resolve(base_path, relative_path)


def _validate_content(content: str) -> None:
    if len(content.encode("utf-8")) > MAX_FILE_SIZE_BYTES:
        raise FileToolError("FILE_TOO_LARGE", "File content exceeds the size limit.")


def create_file(base_path: str, relative_path: str, content: str) -> Path:
    """Create a UTF-8 file within the assigned workspace."""
    _validate_content(content)
    path = _resolve(base_path, relative_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def read_file(base_path: str, relative_path: str) -> str:
    """Read a bounded UTF-8 file within the assigned workspace."""
    path = _resolve(base_path, relative_path)
    if not path.is_file():
        raise FileToolError("FILE_NOT_FOUND", "Requested file does not exist.")
    if path.stat().st_size > MAX_FILE_SIZE_BYTES:
        raise FileToolError("FILE_TOO_LARGE", "File content exceeds the size limit.")
    return path.read_text(encoding="utf-8")


def update_file(base_path: str, relative_path: str, content: str) -> Path:
    """Replace a UTF-8 file within the assigned workspace."""
    _validate_content(content)
    path = _resolve(base_path, relative_path)
    if not path.is_file():
        raise FileToolError("FILE_NOT_FOUND", "Requested file does not exist.")
    path.write_text(content, encoding="utf-8")
    return path


def delete_file(base_path: str, relative_path: str) -> None:
    """Delete a file within the assigned workspace."""
    path = _resolve(base_path, relative_path)
    if not path.is_file():
        raise FileToolError("FILE_NOT_FOUND", "Requested file does not exist.")
    path.unlink()


def list_files(base_path: str) -> list[str]:
    """List bounded, workspace-relative file names without following escaped links."""
    base = Path(base_path).resolve()
    if not base.is_dir():
        raise FileToolError("WORKSPACE_NOT_FOUND", "Assigned workspace does not exist.")

    files: list[str] = []
    for path in base.rglob("*"):
        if path.is_file() and path.resolve().is_relative_to(base):
            files.append(str(path.relative_to(base)))
            if len(files) > MAX_FILES:
                raise FileToolError(
                    "TOO_MANY_FILES", "Workspace exceeds the file limit."
                )
    return sorted(files)
