"""Schemas for product performance and inventory operations."""
from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class ProductPerformance(BaseModel):
    product_name: str
    total_sales: float
    order_count: int = Field(default=0)


class ProductPerformanceResponse(BaseModel):
    products: List[ProductPerformance]
    count: int
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class InventoryAlert(BaseModel):
    sku: str
    product_name: str
    days_remaining: int
    priority: str = Field(..., description="Priority level: high, medium, or low")
    source_table: str = Field(default="")


class InventoryAlertResponse(BaseModel):
    alerts: List[InventoryAlert]
    count: int
    generated_at: datetime = Field(default_factory=datetime.utcnow)

