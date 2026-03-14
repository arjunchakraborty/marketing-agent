"""Analytics service for KPI and cohort computations."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy import func, text
from sqlalchemy.engine import Engine

from ..core.config import settings
from ..db.session import engine
from ..workflows.local_csv_ingestion import DATASET_REGISTRY_TABLE


class AnalyticsService:
    """Compute KPI aggregates, cohorts, anomalies, and forecasts."""

    def __init__(self, db_engine: Optional[Engine] = None) -> None:
        self.engine = db_engine or engine

    def query_kpis(self, metrics: List[str], filters: Dict[str, str]) -> Dict[str, float]:
        """Compute real KPI metrics from ingested datasets."""
        results: Dict[str, float] = {}

        # Load available datasets
        datasets = self._load_available_datasets()

        for metric in metrics:
            try:
                value = self._compute_metric(metric, datasets, filters)
                results[metric] = value
            except Exception as e:
                results[metric] = 0.0

        return results

    def _load_available_datasets(self) -> List[Dict[str, str]]:
        """Load dataset registry."""
        query = text(f"SELECT table_name, business, category, columns FROM {DATASET_REGISTRY_TABLE}")
        with self.engine.begin() as connection:
            result = connection.execute(query)
            rows = [dict(row._mapping) for row in result]
        for row in rows:
            if isinstance(row.get("columns"), str):
                try:
                    row["columns"] = json.loads(row["columns"])
                except:
                    row["columns"] = []
        return rows

    def _compute_metric(self, metric: str, datasets: List[Dict[str, str]], filters: Dict[str, str]) -> float:
        """Compute a specific metric from available datasets."""
        metric_lower = metric.lower()

        # Revenue metrics
        if "revenue" in metric_lower or "sales" in metric_lower:
            return self._sum_from_tables(datasets, ["sales", "revenue", "total_sales"], filters)

        # AOV (Average Order Value)
        if "aov" in metric_lower or "average_order" in metric_lower:
            return self._compute_aov(datasets, filters)

        # ROAS (Return on Ad Spend)
        if "roas" in metric_lower:
            return self._compute_roas(datasets, filters)

        # Conversion rate
        if "conversion" in metric_lower:
            return self._compute_conversion_rate(datasets, filters)

        # Session metrics
        if "sessions" in metric_lower:
            return self._sum_from_tables(datasets, ["sessions", "session_count"], filters)

        return 0.0

    def _sum_from_tables(self, datasets: List[Dict[str, str]], column_patterns: List[str], filters: Dict[str, str]) -> float:
        """Sum values from tables matching column patterns."""
        total = 0.0
        for dataset in datasets:
            table_name = dataset["table_name"]
            columns = dataset.get("columns", [])
            matching_cols = [col for col in columns if any(pattern in col.lower() for pattern in column_patterns)]

            if not matching_cols:
                continue

            try:
                col = matching_cols[0]
                where_clause = self._build_where_clause(filters)
                query = text(f'SELECT SUM(CAST("{col}" AS REAL)) FROM "{table_name}" {where_clause}')
                with self.engine.begin() as connection:
                    result = connection.execute(query)
                    row = result.fetchone()
                    if row and row[0]:
                        total += float(row[0])
            except Exception:
                continue

        return total

    def _compute_aov(self, datasets: List[Dict[str, str]], filters: Dict[str, str]) -> float:
        """Compute Average Order Value."""
        revenue = self._sum_from_tables(datasets, ["sales", "revenue", "total_sales"], filters)
        orders = self._sum_from_tables(datasets, ["orders", "order_count"], filters)
        return revenue / orders if orders > 0 else 0.0

    def _compute_roas(self, datasets: List[Dict[str, str]], filters: Dict[str, str]) -> float:
        """Compute Return on Ad Spend."""
        revenue = self._sum_from_tables(datasets, ["sales", "revenue"], filters)
        spend = self._sum_from_tables(datasets, ["spend", "ad_spend", "marketing_spend"], filters)
        return revenue / spend if spend > 0 else 0.0

    def _compute_conversion_rate(self, datasets: List[Dict[str, str]], filters: Dict[str, str]) -> float:
        """Compute conversion rate percentage."""
        conversions = self._sum_from_tables(datasets, ["conversions", "converted_sessions"], filters)
        sessions = self._sum_from_tables(datasets, ["sessions", "session_count"], filters)
        return (conversions / sessions * 100) if sessions > 0 else 0.0

    def _build_where_clause(self, filters: Dict[str, str]) -> str:
        """Build WHERE clause from filters."""
        if not filters:
            return ""
        conditions = []
        for key, value in filters.items():
            conditions.append(f'"{key}" = "{value}"')
        return "WHERE " + " AND ".join(conditions) if conditions else ""

    def cohort_analysis(self, group_by: str, metric: str, filters: Dict[str, str]) -> Dict[str, Dict[str, float]]:
        """Perform cohort analysis grouping by specified dimension."""
        cohorts: Dict[str, Dict[str, float]] = {}
        datasets = self._load_available_datasets()

        for dataset in datasets:
            table_name = dataset["table_name"]
            columns = dataset.get("columns", [])

            if group_by not in columns:
                continue

            try:
                where_clause = self._build_where_clause(filters)
                query = text(
                    f'SELECT "{group_by}", SUM(CAST("{metric}" AS REAL)) as total FROM "{table_name}" {where_clause} GROUP BY "{group_by}"'
                )
                with self.engine.begin() as connection:
                    result = connection.execute(query)
                    for row in result:
                        cohort_key = str(row[0])
                        cohorts[cohort_key] = {"total": float(row[1]), "count": 1.0}
            except Exception:
                continue

        return cohorts
