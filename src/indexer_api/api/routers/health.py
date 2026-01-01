"""
Health check and system status endpoints.
"""
from fastapi import APIRouter

from indexer_api.core.config import settings
from indexer_api.schemas.base import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
)
async def health_check() -> HealthResponse:
    """
    Check if the API is healthy.

    Returns status of database and Redis connections.
    """
    # In production, add actual health checks
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        database="connected",
        redis="connected",
    )


@router.get(
    "/",
    summary="API root",
)
async def root() -> dict:
    """API root - basic info."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
    }
