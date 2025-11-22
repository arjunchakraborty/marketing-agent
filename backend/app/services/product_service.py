"""Product performance and inventory insights service."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.engine import Engine

from ..db.session import engine
from ..models.constants import DATASET_REGISTRY_TABLE


class ProductService:
    """Service for product performance and inventory alert generation."""

    def __init__(self, db_engine: Optional[Engine] = None) -> None:
        self.engine = db_engine or engine

    def get_top_products(self, limit: int = 10, filters: Optional[Dict[str, str]] = None) -> List[Dict[str, any]]:
        """Get top performing products by sales."""
        filters = filters or {}
        datasets = self._load_sales_datasets()

        products: Dict[str, Dict[str, any]] = {}

        for dataset in datasets:
            table_name = dataset["table_name"]
            columns = dataset.get("columns", [])

            product_col = next((col for col in columns if "product" in col.lower()), None)
            sales_col = next((col for col in columns if "sales" in col.lower() or "revenue" in col.lower()), None)

            if not product_col or not sales_col:
                continue

            try:
                where_clause = self._build_where_clause(filters)
                query = text(
                    f'SELECT "{product_col}", SUM(CAST("{sales_col}" AS REAL)) as total_sales FROM "{table_name}" {where_clause} GROUP BY "{product_col}" ORDER BY total_sales DESC LIMIT {limit}'
                )
                with self.engine.begin() as connection:
                    result = connection.execute(query)
                    for row in result:
                        product_name = str(row[0])
                        sales = float(row[1])
                        if product_name not in products:
                            products[product_name] = {"product_name": product_name, "total_sales": 0.0, "order_count": 0}
                        products[product_name]["total_sales"] += sales
            except Exception:
                continue

        return sorted(products.values(), key=lambda x: x["total_sales"], reverse=True)[:limit]

    def get_inventory_alerts(self, threshold_days: int = 30) -> List[Dict[str, any]]:
        """Generate inventory alerts for low stock items."""
        alerts: List[Dict[str, any]] = []

        # Look for inventory-related datasets
        datasets = self._load_datasets_by_category(["sales", "inventory"])

        for dataset in datasets:
            table_name = dataset["table_name"]
            columns = dataset.get("columns", [])

            # Look for SKU, product name, and inventory/stock columns
            sku_col = next((col for col in columns if "sku" in col.lower()), None)
            product_col = next((col for col in columns if "product" in col.lower() and "name" in col.lower()), None)
            stock_col = next((col for col in columns if "stock" in col.lower() or "inventory" in col.lower() or "quantity" in col.lower()), None)
            date_col = next((col for col in columns if "date" in col.lower() or "day" in col.lower()), None)

            if not (sku_col or product_col):
                continue

            try:
                query = text(f'SELECT * FROM "{table_name}" LIMIT 100')
                with self.engine.begin() as connection:
                    result = connection.execute(query)
                    for row in result:
                        row_dict = dict(row._mapping)
                        product_name = str(row_dict.get(product_col or sku_col, "Unknown"))
                        sku = str(row_dict.get(sku_col, product_name))

                        # Estimate days remaining (simplified heuristic)
                        days_remaining = self._estimate_days_remaining(row_dict, stock_col, date_col)

                        if days_remaining and days_remaining <= threshold_days:
                            priority = "high" if days_remaining <= 7 else "medium" if days_remaining <= 14 else "low"
                            alerts.append(
                                {
                                    "sku": sku,
                                    "product_name": product_name,
                                    "days_remaining": days_remaining,
                                    "priority": priority,
                                    "source_table": table_name,
                                }
                            )
            except Exception:
                continue

        return alerts[:20]  # Limit to top 20 alerts

    def _load_sales_datasets(self) -> List[Dict[str, str]]:
        """Load datasets related to sales."""
        return self._load_datasets_by_category(["sales"])

    def _load_datasets_by_category(self, categories: List[str]) -> List[Dict[str, str]]:
        """Load datasets matching category patterns."""
        query = text(f"SELECT table_name, business, category, columns FROM {DATASET_REGISTRY_TABLE}")
        with self.engine.begin() as connection:
            result = connection.execute(query)
            rows = [dict(row._mapping) for row in result]

        filtered = []
        for row in rows:
            category = row.get("category", "").lower()
            if any(cat.lower() in category for cat in categories):
                if isinstance(row.get("columns"), str):
                    try:
                        row["columns"] = json.loads(row["columns"])
                    except:
                        row["columns"] = []
                filtered.append(row)

        return filtered

    def _build_where_clause(self, filters: Dict[str, str]) -> str:
        """Build WHERE clause from filters."""
        if not filters:
            return ""
        conditions = []
        for key, value in filters.items():
            conditions.append(f'"{key}" = "{value}"')
        return "WHERE " + " AND ".join(conditions) if conditions else ""

    def _estimate_days_remaining(self, row_dict: Dict[str, any], stock_col: Optional[str], date_col: Optional[str]) -> Optional[int]:
        """Estimate days remaining based on row data (simplified heuristic)."""
        if stock_col and stock_col in row_dict:
            stock_value = row_dict[stock_col]
            try:
                stock = float(stock_value)
                # Simple heuristic: assume 10 units per day consumption
                return int(stock / 10) if stock > 0 else 0
            except:
                pass

        # Fallback: random estimate for demo
        return None

