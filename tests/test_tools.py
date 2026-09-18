from pathlib import Path

import pytest

from app.sandbox.security import SandboxSecurityError
from app.tools.file_tools import create_file, list_files, read_file


def test_file_tools_create_read_and_list(tmp_path: Path):
    create_file(str(tmp_path), "app/main.py", "print('hello')")

    assert read_file(str(tmp_path), "app/main.py") == "print('hello')"
    assert list_files(str(tmp_path)) == ["app/main.py"]


def test_file_tools_block_path_traversal(tmp_path: Path):
    with pytest.raises(SandboxSecurityError):
        create_file(str(tmp_path), "../escape.py", "print('nope')")
