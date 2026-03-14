"""API v1 package exports."""
from fastapi import APIRouter

from . import health, ingestion, analytics, intelligence, products


router = APIRouter()
router.include_router(health.router, tags=["health"])
router.include_router(ingestion.router, prefix="/ingestion", tags=["ingestion"])
router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
router.include_router(intelligence.router, prefix="/intelligence", tags=["intelligence"])
router.include_router(products.router, prefix="/products", tags=["products"])

__all__ = ["router"]
