from pathlib import Path

import pytest

from app.sandbox.security import SandboxSecurityError, ensure_within_base, validate_task


def test_sandbox_security_rejects_invalid_task():
    with pytest.raises(SandboxSecurityError):
        validate_task("bash")


def test_path_traversal_prevention(tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with pytest.raises(SandboxSecurityError):
        ensure_within_base(workspace, workspace / ".." / "escape")
