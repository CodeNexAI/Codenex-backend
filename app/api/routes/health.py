from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    name="health_check",
    summary="Check service health",
    description=(
        "Reports whether the CodeNex backend is available. "
        "No authentication is required."
    ),
)
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "codenex-backend"}
