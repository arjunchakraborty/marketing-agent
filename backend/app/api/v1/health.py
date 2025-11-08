"""Health and readiness endpoints."""
from fastapi import APIRouter

from ..schemas.system import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health_check() -> HealthResponse:
    """Return service health metadata for monitoring."""
    return HealthResponse(status="ok")
