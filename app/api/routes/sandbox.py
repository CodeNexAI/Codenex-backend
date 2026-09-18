from fastapi import APIRouter, HTTPException

from app.api.dependencies import SettingsDependency, get_sandbox_runner
from app.models.schemas import SandboxRequest, SandboxResult
from app.sandbox.executor import SandboxExecutionError
from app.sandbox.security import SandboxSecurityError, ensure_within_base

router = APIRouter(prefix="/api/sandbox", tags=["sandbox"])


@router.post("/run", response_model=SandboxResult)
async def run_sandbox(payload: SandboxRequest, settings: SettingsDependency) -> SandboxResult:
    runner = get_sandbox_runner(settings)
    try:
        ensure_within_base(settings.workspace_root, payload.workspace_path)
        return runner.run_task(payload.workspace_path, payload.task, payload.args)
    except SandboxSecurityError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except SandboxExecutionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
