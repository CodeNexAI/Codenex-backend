from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health", name="health_check")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "codenex-backend"}
