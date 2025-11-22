"""Service for precomputing and managing KPI SQL queries."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.engine import Engine

from ..core.config import settings
from ..db.session import engine
from ..models.kpi_cache import KPI_PRECOMPUTED_TABLE, ensure_kpi_precomputed_table
from ..services.prompt_sql_service import PromptToSqlService


# Standard KPI definitions from agent-spec.md
STANDARD_KPI_PROMPTS = {
    "Revenue": "What is the total revenue for business in the last 30 days?",
    "AOV": "What is the average order value (AOV) from all campaigns for business in the 30 days before the last 30 days?",
    "Conversion Rate": "What is the average conversion rate from all campaigns for business in the last 30 days?",
    "Email CTR": "What is the average email click-through rate (CTR) from all email campaigns in the 30 days before the last 30 days?",
}


class KpiPrecomputationService:
    """Service for precomputing KPI SQL queries and storing them in the database."""

    def __init__(self, db_engine: Optional[Engine] = None) -> None:
        self.engine = db_engine or engine
        ensure_kpi_precomputed_table(self.engine)
        self.prompt_sql_service = PromptToSqlService(db_engine=self.engine)

    def _normalize_prompt(self, prompt: str, business: Optional[str] = None) -> str:
        """Normalize prompt by replacing business placeholder with actual business name."""
        if business:
            return prompt.replace("business", business)
        return prompt

    def precompute_kpi_sql(self, kpi_name: str, prompt: str, business: Optional[str] = None) -> Dict[str, str]:
        """Precompute SQL for a KPI prompt and store it in the database."""
        normalized_prompt = self._normalize_prompt(prompt, business)

        try:
            # Generate SQL using prompt-to-SQL service
            result = self.prompt_sql_service.generate_sql(normalized_prompt)
            sql_query = result.get("sql", "")

            if not sql_query:
                raise ValueError(f"Failed to generate SQL for KPI: {kpi_name}")

            # Store in database
            now = datetime.utcnow().isoformat()
            with self.engine.begin() as connection:
                connection.execute(
                    text(
                        f"""
                        INSERT INTO {KPI_PRECOMPUTED_TABLE} (
                            kpi_name, prompt, sql_query, business, created_at, updated_at
                        ) VALUES (
                            :kpi_name, :prompt, :sql_query, :business, :created_at, :updated_at
                        )
                        ON CONFLICT(kpi_name, business) DO UPDATE SET
                            prompt=excluded.prompt,
                            sql_query=excluded.sql_query,
                            updated_at=excluded.updated_at
                        """
                    ),
                    {
                        "kpi_name": kpi_name,
                        "prompt": normalized_prompt,
                        "sql_query": sql_query,
                        "business": business,
                        "created_at": now,
                        "updated_at": now,
                    },
                )

            return {
                "kpi_name": kpi_name,
                "prompt": normalized_prompt,
                "sql_query": sql_query,
                "business": business,
                "status": "precomputed",
            }
        except Exception as e:
            return {
                "kpi_name": kpi_name,
                "prompt": normalized_prompt,
                "sql_query": "",
                "business": business,
                "status": "failed",
                "error": str(e),
            }

    def precompute_standard_kpis(self, business: Optional[str] = None) -> List[Dict[str, str]]:
        """Precompute SQL for all standard KPIs."""
        results = []
        for kpi_name, prompt in STANDARD_KPI_PROMPTS.items():
            result = self.precompute_kpi_sql(kpi_name, prompt, business)
            results.append(result)
        return results

    def get_precomputed_kpi_sql(self, kpi_name: str, business: Optional[str] = None) -> Optional[str]:
        """Retrieve precomputed SQL for a KPI."""
        # SQLite doesn't support NULLS LAST, so we use CASE to prioritize business-specific entries
        query = text(
            f"""
            SELECT sql_query FROM {KPI_PRECOMPUTED_TABLE}
            WHERE kpi_name = :kpi_name AND (business = :business OR business IS NULL)
            ORDER BY CASE WHEN business IS NOT NULL THEN 0 ELSE 1 END, business DESC
            LIMIT 1
            """
        )
        with self.engine.begin() as connection:
            result = connection.execute(query, {"kpi_name": kpi_name, "business": business})
            row = result.fetchone()
            if row:
                # Update usage statistics
                connection.execute(
                    text(
                        f"""
                        UPDATE {KPI_PRECOMPUTED_TABLE}
                        SET execution_count = execution_count + 1,
                            last_executed_at = :last_executed_at
                        WHERE kpi_name = :kpi_name AND (business = :business OR business IS NULL)
                        """
                    ),
                    {
                        "kpi_name": kpi_name,
                        "business": business,
                        "last_executed_at": datetime.utcnow().isoformat(),
                    },
                )
                return row[0]
        return None

    def list_precomputed_kpis(self, business: Optional[str] = None) -> List[Dict[str, str]]:
        """List all precomputed KPIs."""
        if business:
            query = text(
                f"""
                SELECT kpi_name, prompt, sql_query, business, created_at, updated_at, 
                       last_executed_at, execution_count
                FROM {KPI_PRECOMPUTED_TABLE}
                WHERE business = :business OR business IS NULL
                ORDER BY kpi_name
                """
            )
            params = {"business": business}
        else:
            query = text(
                f"""
                SELECT kpi_name, prompt, sql_query, business, created_at, updated_at,
                       last_executed_at, execution_count
                FROM {KPI_PRECOMPUTED_TABLE}
                ORDER BY kpi_name, business
                """
            )
            params = {}

        with self.engine.begin() as connection:
            result = connection.execute(query, params)
            rows = [dict(row._mapping) for row in result]
        return rows

    def execute_precomputed_kpi(self, kpi_name: str, business: Optional[str] = None) -> Optional[float]:
        """Execute a precomputed KPI SQL query and return the result."""
        sql_query = self.get_precomputed_kpi_sql(kpi_name, business)
        if not sql_query:
            return None

        try:
            with self.engine.begin() as connection:
                result = connection.execute(text(sql_query))
                row = result.fetchone()
                if row and len(row) > 0:
                    value = row[0]
                    return float(value) if value is not None else 0.0
        except Exception:
            return None
        return None

