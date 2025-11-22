"""Enhanced prompt-to-SQL service with LLM integration."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta
from difflib import get_close_matches
from typing import Dict, List, Optional, Sequence

from sqlalchemy import text
from sqlalchemy.engine import Engine

from ..core.config import settings
from ..db.session import engine
from ..models.constants import DATASET_REGISTRY_TABLE
from ..models.kpi_cache import PROMPT_SQL_CACHE_TABLE, ensure_prompt_sql_cache_table
from .llm_service import LLMService


def _normalize(text_value: str) -> str:
    return text_value.lower().replace("_", " ")


class PromptToSqlService:
    """Generate SQL statements from natural language prompts using LLM or heuristics."""

    def __init__(self, db_engine: Optional[Engine] = None, use_llm: Optional[bool] = None) -> None:
        self.engine = db_engine or engine
        ensure_prompt_sql_cache_table(self.engine)
        self.use_llm = use_llm if use_llm is not None else settings.use_llm_for_sql
        self.llm_service: Optional[LLMService] = None
        if self.use_llm:
            # Try providers in order: configured default, then ollama (local), then openai, then anthropic
            providers_to_try = [settings.default_llm_provider]
            if settings.default_llm_provider != "ollama":
                providers_to_try.append("ollama")
            if settings.default_llm_provider != "openai" and settings.openai_api_key:
                providers_to_try.append("openai")
            if settings.default_llm_provider != "anthropic" and settings.anthropic_api_key:
                providers_to_try.append("anthropic")

            for provider in providers_to_try:
                try:
                    self.llm_service = LLMService(provider=provider)
                    break
                except Exception:
                    continue
            if not self.llm_service:
                self.use_llm = False

    def _normalize_prompt_for_cache(self, prompt: str) -> str:
        """Normalize prompt for consistent caching (case-insensitive, whitespace-normalized)."""
        # Normalize: lowercase, strip, collapse whitespace
        normalized = " ".join(prompt.lower().strip().split())
        return normalized

    def _get_cache_key(self, prompt: str) -> str:
        """Generate a cache key hash from the normalized prompt."""
        normalized_prompt = self._normalize_prompt_for_cache(prompt)
        return hashlib.sha256(normalized_prompt.encode()).hexdigest()

    def _get_schema_version(self) -> str:
        """Get current schema version for cache invalidation."""
        # Simple version based on dataset registry modification
        try:
            query = text(f"SELECT COUNT(*) as count FROM {DATASET_REGISTRY_TABLE}")
            with self.engine.begin() as connection:
                result = connection.execute(query)
                row = result.fetchone()
                count = row[0] if row else 0
            return f"schema_v{count}"
        except Exception:
            return "schema_v0"

    def _get_cached_sql(self, prompt: str) -> Optional[Dict[str, object]]:
        """Retrieve cached SQL from database."""
        prompt_hash = self._get_cache_key(prompt)
        schema_version = self._get_schema_version()
        now = datetime.utcnow().isoformat()

        query = text(
            f"""
            SELECT prompt, sql_query, table_name, business, dataset_name, columns,
                   schema_version, generated_by, model, expires_at
            FROM {PROMPT_SQL_CACHE_TABLE}
            WHERE prompt_hash = :prompt_hash
            """
        )
        with self.engine.begin() as connection:
            result = connection.execute(query, {"prompt_hash": prompt_hash})
            row = result.fetchone()
            if row:
                cached = dict(row._mapping)
                # Check if cache entry is expired
                expires_at = cached.get("expires_at")
                if expires_at:
                    try:
                        expires_dt = datetime.fromisoformat(expires_at)
                        if datetime.utcnow() > expires_dt:
                            # Cache expired, delete it
                            connection.execute(
                                text(f"DELETE FROM {PROMPT_SQL_CACHE_TABLE} WHERE prompt_hash = :prompt_hash"),
                                {"prompt_hash": prompt_hash},
                            )
                            return None
                    except Exception:
                        pass

                # Check schema version mismatch
                if cached.get("schema_version") != schema_version:
                    # Schema changed, invalidate cache
                    connection.execute(
                        text(f"DELETE FROM {PROMPT_SQL_CACHE_TABLE} WHERE prompt_hash = :prompt_hash"),
                        {"prompt_hash": prompt_hash},
                    )
                    return None

                # Update usage statistics
                connection.execute(
                    text(
                        f"""
                        UPDATE {PROMPT_SQL_CACHE_TABLE}
                        SET usage_count = usage_count + 1,
                            last_used_at = :last_used_at
                        WHERE prompt_hash = :prompt_hash
                        """
                    ),
                    {"prompt_hash": prompt_hash, "last_used_at": now},
                )

                # Parse columns JSON if it's a string
                if isinstance(cached.get("columns"), str):
                    try:
                        cached["columns"] = json.loads(cached["columns"])
                    except Exception:
                        cached["columns"] = []

                return cached
        return None

    def _store_cached_sql(
        self,
        prompt: str,
        sql_query: str,
        table_info: Dict[str, str],
        generated_by: str = "llm",
        model: str = "",
        ttl_seconds: Optional[int] = None,
    ) -> None:
        """Store SQL query in database cache."""
        prompt_hash = self._get_cache_key(prompt)
        normalized_prompt = self._normalize_prompt_for_cache(prompt)
        schema_version = self._get_schema_version()
        now = datetime.utcnow().isoformat()

        expires_at = None
        if ttl_seconds:
            expires_at = (datetime.utcnow() + timedelta(seconds=ttl_seconds)).isoformat()

        columns_json = json.dumps(table_info.get("columns", []))

        with self.engine.begin() as connection:
            connection.execute(
                text(
                    f"""
                    INSERT INTO {PROMPT_SQL_CACHE_TABLE} (
                        prompt_hash, prompt, sql_query, table_name, business, dataset_name,
                        columns, schema_version, generated_by, model,
                        created_at, last_used_at, usage_count, ttl_seconds, expires_at
                    ) VALUES (
                        :prompt_hash, :prompt, :sql_query, :table_name, :business, :dataset_name,
                        :columns, :schema_version, :generated_by, :model,
                        :created_at, :last_used_at, :usage_count, :ttl_seconds, :expires_at
                    )
                    ON CONFLICT(prompt_hash) DO UPDATE SET
                        sql_query=excluded.sql_query,
                        table_name=excluded.table_name,
                        business=excluded.business,
                        dataset_name=excluded.dataset_name,
                        columns=excluded.columns,
                        schema_version=excluded.schema_version,
                        generated_by=excluded.generated_by,
                        model=excluded.model,
                        last_used_at=excluded.last_used_at,
                        expires_at=excluded.expires_at
                    """
                ),
                {
                    "prompt_hash": prompt_hash,
                    "prompt": normalized_prompt,
                    "sql_query": sql_query,
                    "table_name": table_info.get("table_name", ""),
                    "business": table_info.get("business", ""),
                    "dataset_name": table_info.get("dataset_name", ""),
                    "columns": columns_json,
                    "schema_version": schema_version,
                    "generated_by": generated_by,
                    "model": model,
                    "created_at": now,
                    "last_used_at": now,
                    "usage_count": 1,
                    "ttl_seconds": ttl_seconds,
                    "expires_at": expires_at,
                },
            )

    def _load_registry(self) -> List[Dict[str, str]]:
        query = text(
            f"SELECT table_name, business, category, dataset_name, columns FROM {DATASET_REGISTRY_TABLE}"
        )
        with self.engine.begin() as connection:
            result = connection.execute(query)
            rows = [dict(row._mapping) for row in result]
        for row in rows:
            if isinstance(row["columns"], str):
                row["columns"] = json.loads(row["columns"])
        return rows

    def _select_dataset(self, prompt: str, datasets: Sequence[Dict[str, str]]) -> Dict[str, str]:
        prompt_norm = _normalize(prompt)

        scores = []
        for dataset in datasets:
            candidates = [
                dataset["table_name"],
                dataset["dataset_name"],
                f"{dataset['business']} {dataset['dataset_name']}",
            ]
            normalized_candidates = [_normalize(candidate) for candidate in candidates]
            best = get_close_matches(prompt_norm, normalized_candidates, n=1, cutoff=0)
            score = 0.0
            if best:
                match = best[0]
                score = len(set(match.split()).intersection(prompt_norm.split())) / max(len(prompt_norm.split()), 1)
            scores.append((score, dataset))

        scores.sort(key=lambda item: item[0], reverse=True)
        return scores[0][1] if scores else datasets[0]

    def _build_query(self, dataset: Dict[str, str]) -> str:
        table_name = dataset["table_name"]
        columns = dataset["columns"]

        order_column = next(
            (
                column
                for column in columns
                if any(token in column for token in ("date", "day", "occurred_at", "week", "time"))
            ),
            None,
        )

        quoted_table = f'"{table_name}"'
        order_clause = f' ORDER BY "{order_column}" DESC' if order_column else ""
        return f"SELECT * FROM {quoted_table}{order_clause} LIMIT 50;"

    def generate_sql(self, prompt: str) -> Dict[str, str]:
        """Generate SQL from prompt without executing it. Returns dict with 'sql' key."""
        datasets = self._load_registry()
        if not datasets:
            raise ValueError("No datasets have been ingested yet.")

        if self.use_llm and self.llm_service:
            return self._generate_sql_llm(prompt, datasets)
        else:
            return self._generate_sql_heuristic(prompt, datasets)

    def execute_prompt(self, prompt: str) -> Dict[str, object]:
        """Execute prompt and return full results including data rows."""
        datasets = self._load_registry()
        if not datasets:
            raise ValueError("No datasets have been ingested yet.")

        if self.use_llm and self.llm_service:
            return self._execute_prompt_llm(prompt, datasets)
        else:
            return self._execute_prompt_heuristic(prompt, datasets)

    def _generate_sql_llm(self, prompt: str, datasets: List[Dict[str, str]]) -> Dict[str, str]:
        """Generate SQL using LLM without executing it. Uses database cache when available."""
        # Check database cache first
        cached = self._get_cached_sql(prompt)
        if cached:
            return {
                "sql": cached.get("sql_query", ""),
                "cached": True,
            }

        # Generate SQL using LLM (cache miss)
        sample_rows = []
        try:
            first_table = datasets[0]
            sample_query = text(f'SELECT * FROM "{first_table["table_name"]}" LIMIT 3')
            with self.engine.begin() as connection:
                result = connection.execute(sample_query)
                sample_rows = [dict(row._mapping) for row in result]
        except Exception:
            pass

        # Pass sample_rows to help Ollama understand data structure better
        llm_result = self.llm_service.generate_sql(prompt, datasets, sample_rows)
        sql = llm_result["sql"]

        # Validate SQL safety
        if not self._is_safe_sql(sql):
            raise ValueError("Generated SQL contains unsafe operations")

        # Determine which table was used
        table_info = self._extract_table_from_sql(sql, datasets)

        # Store in database cache
        self._store_cached_sql(
            prompt=prompt,
            sql_query=sql,
            table_info=table_info,
            generated_by=llm_result.get("provider", "llm"),
            model=llm_result.get("model", ""),
        )

        return {
            "sql": sql,
            "cached": False,
        }

    def _generate_sql_heuristic(self, prompt: str, datasets: List[Dict[str, str]]) -> Dict[str, str]:
        """Generate SQL using heuristic matching without executing it."""
        dataset = self._select_dataset(prompt, datasets)
        sql = self._build_query(dataset)
        return {"sql": sql, "cached": False}

    def _execute_prompt_llm(self, prompt: str, datasets: List[Dict[str, str]]) -> Dict[str, object]:
        """Execute prompt using LLM for SQL generation. Uses database cache when available."""
        # Check database cache first
        cached = self._get_cached_sql(prompt)
        if cached:
            # Re-execute the cached SQL to get fresh data (since data may have changed)
            sql = cached.get("sql_query", "")
            table_info = {
                "table_name": cached.get("table_name", ""),
                "business": cached.get("business", ""),
                "dataset_name": cached.get("dataset_name", ""),
                "columns": cached.get("columns", []),
            }
            
            # Execute cached SQL to get fresh results
            try:
                with self.engine.begin() as connection:
                    result = connection.execute(text(sql))
                    rows = [dict(row._mapping) for row in result]
                
                # Return cached metadata with fresh data
                return {
                    "table_name": table_info.get("table_name", ""),
                    "business": table_info.get("business", ""),
                    "dataset_name": table_info.get("dataset_name", ""),
                    "sql": sql,
                    "columns": list(rows[0].keys()) if rows else [],
                    "rows": rows,
                    "generated_by": cached.get("generated_by", "llm"),
                    "model": cached.get("model", ""),
                    "cached": True,
                }
            except Exception:
                # If cached SQL fails (e.g., schema changed), fall through to regenerate
                # Cache will be invalidated by schema version check on next access
                pass

        # Generate SQL using LLM (cache miss or cache invalid)
        sample_rows = []
        try:
            first_table = datasets[0]
            sample_query = text(f'SELECT * FROM "{first_table["table_name"]}" LIMIT 3')
            with self.engine.begin() as connection:
                result = connection.execute(sample_query)
                sample_rows = [dict(row._mapping) for row in result]
        except Exception:
            pass

        # Pass sample_rows to help Ollama understand data structure better
        llm_result = self.llm_service.generate_sql(prompt, datasets, sample_rows)
        sql = llm_result["sql"]

        # Validate SQL safety
        if not self._is_safe_sql(sql):
            raise ValueError("Generated SQL contains unsafe operations")

        # Determine which table was used (best guess from SQL) - do this before execution for error messages
        table_info = self._extract_table_from_sql(sql, datasets)

        # Execute SQL
        try:
            with self.engine.begin() as connection:
                result = connection.execute(text(sql))
                rows = [dict(row._mapping) for row in result]
        except Exception as e:
            error_msg = str(e)
            # Provide helpful error message if columns don't exist
            if "no such column" in error_msg.lower() or "no such table" in error_msg.lower():
                available_cols = table_info.get("columns", [])
                if available_cols:
                    raise ValueError(
                        f"SQL execution failed: {error_msg}\n"
                        f"Available columns for table '{table_info.get('table_name', 'unknown')}': {', '.join(available_cols)}"
                    )
            raise ValueError(f"SQL execution failed: {error_msg}")

        result = {
            "table_name": table_info.get("table_name", ""),
            "business": table_info.get("business", ""),
            "dataset_name": table_info.get("dataset_name", ""),
            "sql": sql,
            "columns": list(rows[0].keys()) if rows else [],
            "rows": rows,
            "generated_by": llm_result.get("provider", "llm"),
            "model": llm_result.get("model", ""),
            "cached": False,
        }

        # Store in database cache (store metadata, not the rows since data changes)
        self._store_cached_sql(
            prompt=prompt,
            sql_query=sql,
            table_info=table_info,
            generated_by=result["generated_by"],
            model=result["model"],
        )

        return result

    def _execute_prompt_heuristic(self, prompt: str, datasets: List[Dict[str, str]]) -> Dict[str, object]:
        """Execute prompt using heuristic matching (fallback)."""
        dataset = self._select_dataset(prompt, datasets)
        sql = self._build_query(dataset)

        with self.engine.begin() as connection:
            result = connection.execute(text(sql))
            rows = [dict(row._mapping) for row in result]

        return {
            "table_name": dataset["table_name"],
            "business": dataset["business"],
            "dataset_name": dataset["dataset_name"],
            "sql": sql,
            "columns": dataset["columns"],
            "rows": rows,
            "generated_by": "heuristic",
        }

    def _is_safe_sql(self, sql: str) -> bool:
        """Check if SQL contains only safe operations."""
        dangerous_keywords = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "TRUNCATE", "CREATE", "EXEC"]
        sql_upper = sql.upper()
        return not any(keyword in sql_upper for keyword in dangerous_keywords)

    def _extract_table_from_sql(self, sql: str, datasets: List[Dict[str, str]]) -> Dict[str, str]:
        """Extract table name from SQL query."""
        sql_upper = sql.upper()
        for dataset in datasets:
            table_name = dataset["table_name"]
            if table_name.upper() in sql_upper or f'"{table_name}"' in sql:
                return dataset
        return datasets[0] if datasets else {}


