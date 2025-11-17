"""Enhanced prompt-to-SQL service with LLM integration."""
from __future__ import annotations

import hashlib
import json
import re
from difflib import get_close_matches
from typing import Dict, List, Optional, Sequence

from sqlalchemy import text
from sqlalchemy.engine import Engine

from ..core.config import settings
from ..db.session import engine
from ..workflows.local_csv_ingestion import DATASET_REGISTRY_TABLE
from .llm_service import LLMService


def _normalize(text_value: str) -> str:
    return text_value.lower().replace("_", " ")


class PromptToSqlService:
    """Generate SQL statements from natural language prompts using LLM or heuristics."""

    # Class-level cache shared across all instances
    _sql_cache: Dict[str, Dict[str, object]] = {}

    def __init__(self, db_engine: Optional[Engine] = None, use_llm: Optional[bool] = None) -> None:
        self.engine = db_engine or engine
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

    def _get_cache_key(self, prompt: str) -> str:
        """Generate a cache key from the prompt."""
        # Normalize prompt (lowercase, strip whitespace) for consistent caching
        normalized_prompt = prompt.lower().strip()
        return hashlib.sha256(normalized_prompt.encode()).hexdigest()

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
        """Generate SQL using LLM without executing it. Uses cache when available."""
        # Check cache first
        cache_key = self._get_cache_key(prompt)
        if cache_key in self._sql_cache:
            cached_result = self._sql_cache[cache_key]
            return {
                "sql": cached_result.get("sql", ""),
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

        # Cache the result
        self._sql_cache[cache_key] = {
            "table_name": table_info.get("table_name", ""),
            "business": table_info.get("business", ""),
            "dataset_name": table_info.get("dataset_name", ""),
            "sql": sql,
            "columns": table_info.get("columns", []),
            "generated_by": llm_result.get("provider", "llm"),
            "model": llm_result.get("model", ""),
        }

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
        """Execute prompt using LLM for SQL generation."""
        # Check cache first
        cache_key = self._get_cache_key(prompt)
        if cache_key in self._sql_cache:
            cached_result = self._sql_cache[cache_key]
            # Re-execute the cached SQL to get fresh data (since data may have changed)
            sql = cached_result.get("sql", "")
            table_info = {
                "table_name": cached_result.get("table_name", ""),
                "business": cached_result.get("business", ""),
                "dataset_name": cached_result.get("dataset_name", ""),
                "columns": cached_result.get("columns", []),
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
                    "generated_by": cached_result.get("generated_by", "llm"),
                    "model": cached_result.get("model", ""),
                    "cached": True,
                }
            except Exception:
                # If cached SQL fails (e.g., schema changed), fall through to regenerate
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

        # Cache the result (store metadata, not the rows since data changes)
        self._sql_cache[cache_key] = {
            "table_name": result["table_name"],
            "business": result["business"],
            "dataset_name": result["dataset_name"],
            "sql": sql,
            "columns": result["columns"],
            "generated_by": result["generated_by"],
            "model": result["model"],
        }

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


