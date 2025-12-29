"""Product performance and inventory endpoints."""
from fastapi import APIRouter, Query

from ...schemas.products import InventoryAlertResponse, ProductPerformanceResponse
from ...services.product_service import ProductService

router = APIRouter()
product_service = ProductService()


@router.get("/top", response_model=ProductPerformanceResponse, summary="Get top performing products")
async def get_top_products(limit: int = Query(default=10, ge=1, le=100)) -> ProductPerformanceResponse:
    """Retrieve top products by sales performance."""
    products = product_service.get_top_products(limit=limit)
    return ProductPerformanceResponse(products=products, count=len(products))


@router.get("/inventory/alerts", response_model=InventoryAlertResponse, summary="Get inventory alerts")
async def get_inventory_alerts(threshold_days: int = Query(default=30, ge=1, le=90)) -> InventoryAlertResponse:
    """Generate inventory alerts for low stock items."""
    alerts = product_service.get_inventory_alerts(threshold_days=threshold_days)
    return InventoryAlertResponse(alerts=alerts, count=len(alerts))

