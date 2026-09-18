from __future__ import annotations

from pathlib import Path

from app.sandbox.security import ensure_within_base


def _resolve(base_path: str, relative_path: str) -> Path:
    base = Path(base_path).resolve()
    target = (base / relative_path).resolve()
    ensure_within_base(base, target)
    return target


def create_file(base_path: str, relative_path: str, content: str) -> Path:
    path = _resolve(base_path, relative_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def read_file(base_path: str, relative_path: str) -> str:
    return _resolve(base_path, relative_path).read_text(encoding="utf-8")


def update_file(base_path: str, relative_path: str, content: str) -> Path:
    path = _resolve(base_path, relative_path)
    if not path.exists():
        raise FileNotFoundError(relative_path)
    path.write_text(content, encoding="utf-8")
    return path


def delete_file(base_path: str, relative_path: str) -> None:
    path = _resolve(base_path, relative_path)
    if path.exists():
        path.unlink()


def list_files(base_path: str) -> list[str]:
    base = Path(base_path).resolve()
    return sorted(
        str(path.relative_to(base)) for path in base.rglob("*") if path.is_file()
    )
