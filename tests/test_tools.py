from pathlib import Path

import pytest

from app.sandbox.security import SandboxSecurityError
from app.models import schemas
from app.tools.file_tools import create_file, delete_file, list_files, read_file, update_file
from app.tools.git_tools import GitTools
from app.tools.test_tools import parse_test_result


def test_file_tools_create_read_and_list(tmp_path: Path):
    create_file(str(tmp_path), "app/main.py", "print('hello')")

    assert read_file(str(tmp_path), "app/main.py") == "print('hello')"
    assert list_files(str(tmp_path)) == ["app/main.py"]


def test_file_tools_block_path_traversal(tmp_path: Path):
    with pytest.raises(SandboxSecurityError):
        create_file(str(tmp_path), "../escape.py", "print('nope')")

    with pytest.raises(SandboxSecurityError):
        update_file(str(tmp_path), "../escape.py", "print('nope')")

    with pytest.raises(SandboxSecurityError):
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
    tools = GitTools(str(tmp_path))

    with pytest.raises(SandboxSecurityError):
        tools.add(str(tmp_path / "workspace"), "../outside.txt")
