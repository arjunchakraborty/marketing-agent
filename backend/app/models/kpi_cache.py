"""Database models for KPI precomputation and prompt-to-SQL caching."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, text
from sqlalchemy.engine import Engine


# Table names
KPI_PRECOMPUTED_TABLE = "kpi_precomputed_sql"
PROMPT_SQL_CACHE_TABLE = "prompt_sql_cache"


def ensure_kpi_precomputed_table(engine: Engine) -> None:
    """Create the KPI precomputed SQL table if it doesn't exist."""
    create_stmt = text(
        f"""
        CREATE TABLE IF NOT EXISTS {KPI_PRECOMPUTED_TABLE} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kpi_name TEXT NOT NULL,
            prompt TEXT NOT NULL,
            sql_query TEXT NOT NULL,
            business TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            last_executed_at TEXT,
            execution_count INTEGER DEFAULT 0,
            UNIQUE(kpi_name, business)
        )
        """
    )
    with engine.begin() as connection:
        connection.execute(create_stmt)


def ensure_prompt_sql_cache_table(engine: Engine) -> None:
    """Create the prompt-to-SQL cache table if it doesn't exist."""
    create_stmt = text(
        f"""
        CREATE TABLE IF NOT EXISTS {PROMPT_SQL_CACHE_TABLE} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt_hash TEXT NOT NULL UNIQUE,
            prompt TEXT NOT NULL,
            sql_query TEXT NOT NULL,
            table_name TEXT,
            business TEXT,
            dataset_name TEXT,
            columns TEXT,
            schema_version TEXT,
            generated_by TEXT,
            model TEXT,
            created_at TEXT NOT NULL,
            last_used_at TEXT,
            usage_count INTEGER DEFAULT 0,
            ttl_seconds INTEGER,
            expires_at TEXT
        )
        """
    )
    with engine.begin() as connection:
        connection.execute(create_stmt)
        # Create index on prompt_hash for faster lookups
        try:
            connection.execute(text(f"CREATE INDEX IF NOT EXISTS idx_prompt_hash ON {PROMPT_SQL_CACHE_TABLE}(prompt_hash)"))
        except Exception:
            pass  # Index might already exist


def ensure_cache_tables(engine: Engine) -> None:
    """Ensure all cache tables exist."""
    ensure_kpi_precomputed_table(engine)
    ensure_prompt_sql_cache_table(engine)

