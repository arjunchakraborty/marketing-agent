"""Product performance and inventory endpoints."""
import logging
from typing import Dict, List

from fastapi import APIRouter, Query

from ...schemas.products import (
    InventoryAlertResponse,
    ProductPerformanceResponse,
    VectorProductListResponse,
)
from ...services.product_service import ProductService
from ...services.vector_db_service import (
    DEFAULT_PRODUCT_COLLECTION_NAME,
    get_all_products,
    get_product_names,
    list_all_collections,
)

logger = logging.getLogger(__name__)

router = APIRouter()
product_service = ProductService()


@router.get("/top", response_model=ProductPerformanceResponse, summary="Get top performing products")
async def get_top_products(limit: int = Query(default=10, ge=1, le=100)) -> ProductPerformanceResponse:
    """Retrieve top products by sales performance."""
    products = product_service.get_top_products(limit=limit)
    return ProductPerformanceResponse(products=products, count=len(products))


@router.get(
    "/from-vector",
    response_model=VectorProductListResponse,
    summary="Get product names from UCO_Gear_Products vector collection",
)
async def get_products_from_vector() -> VectorProductListResponse:
    """
    Get all products with full metadata from the UCO_Gear_Products collection in the vector database.
    Returns product name, brand, category, description, price, sale_price, hyperlink, and stored image count.
    """
    collection_name = DEFAULT_PRODUCT_COLLECTION_NAME
    products = get_all_products(collection_name)
    return VectorProductListResponse(
        products=products,
        count=len(products),
        collection_name=collection_name,
    )


@router.get("/collections", summary="List vector DB collections and their product counts (debug)")
async def list_product_collections() -> List[Dict]:
    """List all vector DB collections and how many product names each contains."""
    collections = list_all_collections()
    result = []
    for coll_name in collections:
        names = get_product_names(coll_name)
        result.append({
            "collection_name": coll_name,
            "product_count": len(names),
            "sample_products": names[:5],
        })
    return result


@router.get("/inventory/alerts", response_model=InventoryAlertResponse, summary="Get inventory alerts")
async def get_inventory_alerts(threshold_days: int = Query(default=30, ge=1, le=90)) -> InventoryAlertResponse:
    """Generate inventory alerts for low stock items."""
    alerts = product_service.get_inventory_alerts(threshold_days=threshold_days)
    return InventoryAlertResponse(alerts=alerts, count=len(alerts))
