from pathlib import Path

import pytest

from app.models import schemas
from app.sandbox.security import SandboxSecurityError
from app.tools.file_tools import (
    MAX_FILE_SIZE_BYTES,
    FileToolError,
    create_file,
    delete_file,
    list_files,
    read_file,
    update_file,
)
from app.tools.git_tools import GitTools
from app.tools.test_tools import parse_test_result


def test_file_tools_create_read_and_list(tmp_path: Path):
    create_file(str(tmp_path), "app/main.py", "print('hello')")

    assert read_file(str(tmp_path), "app/main.py") == "print('hello')"
    assert list_files(str(tmp_path)) == ["app/main.py"]


@pytest.mark.parametrize("unsafe_path", ["../escape.py", "/etc/passwd", "."])
def test_file_tools_block_unsafe_paths(tmp_path: Path, unsafe_path: str) -> None:
    with pytest.raises(FileToolError):
        create_file(str(tmp_path), unsafe_path, "print('nope')")

    with pytest.raises(FileToolError):
        update_file(str(tmp_path), unsafe_path, "print('nope')")

    with pytest.raises(FileToolError):
        delete_file(str(tmp_path), unsafe_path)


def test_file_tools_limit_size_and_report_missing_files(tmp_path: Path) -> None:
    with pytest.raises(FileToolError, match="size limit"):
        create_file(str(tmp_path), "large.txt", "x" * (MAX_FILE_SIZE_BYTES + 1))

    with pytest.raises(FileToolError, match="does not exist"):
        read_file(str(tmp_path), "missing.txt")

    with pytest.raises(FileToolError, match="does not exist"):
        delete_file(str(tmp_path), "missing.txt")


def test_file_tools_ignore_symlinks_escaping_workspace(tmp_path: Path) -> None:
    external_file = tmp_path.parent / "external.txt"
    external_file.write_text("private", encoding="utf-8")
    (tmp_path / "escaped-link").symlink_to(external_file)

    assert list_files(str(tmp_path)) == []

    with pytest.raises(FileToolError):
        read_file(str(tmp_path), "escaped-link")


def test_file_tools_delete_existing_file(tmp_path: Path) -> None:
    create_file(str(tmp_path), "app/main.py", "print('hello')")
    delete_file(str(tmp_path), "app/main.py")

    assert list_files(str(tmp_path)) == []


def test_file_tools_block_path_traversal(tmp_path: Path):
    with pytest.raises(FileToolError):
        create_file(str(tmp_path), "../escape.py", "print('nope')")

    with pytest.raises(FileToolError):
        update_file(str(tmp_path), "../escape.py", "print('nope')")

    with pytest.raises(FileToolError):
        delete_file(str(tmp_path), "../escape.py")


def test_parse_test_result_handles_any_pytest_order():
    result = schemas.SandboxResult(
        status="failed",
        exit_code=1,
        stdout="2 passed, 1 failed, 3 skipped in 0.15s",
        stderr="",
        duration=0.15,
    )

    parsed = parse_test_result(result)

    assert parsed.passed == 2
    assert parsed.failed == 1
    assert parsed.skipped == 3


def test_parse_test_result_prefers_most_complete_summary():
    result = schemas.SandboxResult(
        status="passed",
        exit_code=0,
        stdout="1 passed in 0.05s\n2 passed, 1 skipped in 0.10s",
        stderr="",
        duration=0.10,
    )

    parsed = parse_test_result(result)

    assert parsed.passed == 2
    assert parsed.skipped == 1


def test_parse_test_result_preserves_execution_errors():
    result = schemas.SandboxResult(
        status="failed",
        exit_code=124,
        stdout="",
        stderr="timeout",
        duration=60.0,
        error_message="Sandbox execution timed out.",
    )

    parsed = parse_test_result(result)

    assert parsed.status == "error"


def test_git_add_blocks_path_traversal(tmp_path: Path):
    (tmp_path / "workspace").mkdir()
    tools = GitTools(str(tmp_path), allow_host_git=True)

    with pytest.raises(SandboxSecurityError):
        tools.add(str(tmp_path / "workspace"), "../outside.txt")
