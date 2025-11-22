"""Utilities for ingesting local CSV datasets into the analytics warehouse."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from ..core.config import settings
from ..db.session import engine
from ..models.constants import DATASET_REGISTRY_TABLE


@dataclass
class IngestedDataset:
    table_name: str
    business: str
    category: str
    dataset_name: str
    source_file: str
    row_count: int
    columns: List[str]


def _normalize_identifier(raw: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", " ", raw).lower()
    cleaned = re.sub(r"[\s-]+", "_", cleaned).strip("_")
    return cleaned or "dataset"


def _ensure_registry(engine: Engine) -> None:
    create_stmt = text(
        f"""
        CREATE TABLE IF NOT EXISTS {DATASET_REGISTRY_TABLE} (
            table_name TEXT PRIMARY KEY,
            business TEXT NOT NULL,
            category TEXT NOT NULL,
            dataset_name TEXT NOT NULL,
            source_file TEXT NOT NULL,
            row_count INTEGER NOT NULL,
            columns TEXT NOT NULL,
            ingested_at TEXT NOT NULL
        )
        """
    )
    with engine.begin() as connection:
        connection.execute(create_stmt)


def _record_dataset(engine: Engine, dataset: IngestedDataset) -> None:
    payload = {
        "table_name": dataset.table_name,
        "business": dataset.business,
        "category": dataset.category,
        "dataset_name": dataset.dataset_name,
        "source_file": dataset.source_file,
        "row_count": dataset.row_count,
        "columns": json.dumps(dataset.columns),
        "ingested_at": datetime.utcnow().isoformat(),
    }

    with engine.begin() as connection:
        connection.execute(
            text(
                f"""
                INSERT INTO {DATASET_REGISTRY_TABLE} (
                    table_name, business, category, dataset_name,
                    source_file, row_count, columns, ingested_at
                ) VALUES (
                    :table_name, :business, :category, :dataset_name,
                    :source_file, :row_count, :columns, :ingested_at
                )
                ON CONFLICT(table_name) DO UPDATE SET
                    business=excluded.business,
                    category=excluded.category,
                    dataset_name=excluded.dataset_name,
                    source_file=excluded.source_file,
                    row_count=excluded.row_count,
                    columns=excluded.columns,
                    ingested_at=excluded.ingested_at
                """
            ),
            payload,
        )


def _load_csv(file_path: Path) -> pd.DataFrame:
    df = pd.read_csv(file_path)
    df.columns = [_normalize_identifier(col) for col in df.columns]
    return df


def iter_business_directories(base_path: Path) -> Iterable[Path]:
    for child in sorted(base_path.iterdir()):
        if child.is_dir():
            yield child


def iter_dataset_files(business_dir: Path) -> Iterable[tuple[str, Path]]:
    for category_dir in sorted(business_dir.iterdir()):
        if not category_dir.is_dir():
            continue
        category_slug = _normalize_identifier(category_dir.name)
        for csv_file in sorted(category_dir.glob("*.csv")):
            yield category_slug, csv_file


def ingest_directory(
    base_path: Optional[Path] = None,
    *,
    engine_override: Optional[Engine] = None,
    business: Optional[str] = None,
) -> List[IngestedDataset]:
    base_path = base_path or Path(settings.ingestion_data_root)
    if not base_path.exists():
        raise FileNotFoundError(f"Ingestion data root not found: {base_path}")

    work_engine = engine_override or engine
    _ensure_registry(work_engine)

    ingested: List[IngestedDataset] = []

    for business_dir in iter_business_directories(base_path):
        business_name = business_dir.name
        if business and _normalize_identifier(business) != _normalize_identifier(business_name):
            continue

        business_slug = _normalize_identifier(business_name)

        for category_slug, csv_file in iter_dataset_files(business_dir):
            dataset_slug = _normalize_identifier(csv_file.stem)
            table_name = f"{business_slug}_{category_slug}_{dataset_slug}"
            df = _load_csv(csv_file)
            df["business_name"] = business_name
            df["category"] = category_slug
            df["source_file"] = str(csv_file)

            df.to_sql(table_name, work_engine, if_exists="replace", index=False)

            dataset = IngestedDataset(
                table_name=table_name,
                business=business_name,
                category=category_slug,
                dataset_name=csv_file.stem,
                source_file=str(csv_file),
                row_count=len(df),
                columns=list(df.columns),
            )
            _record_dataset(work_engine, dataset)
            ingested.append(dataset)

    # Populate cache after ingestion: precompute standard KPIs for each business
    # Use lazy import to avoid circular dependency
    if ingested:
        from ..services.kpi_precomputation_service import KpiPrecomputationService
        kpi_service = KpiPrecomputationService(db_engine=work_engine)
        businesses = set(dataset.business for dataset in ingested)
        for business in businesses:
            try:
                kpi_service.precompute_standard_kpis(business=business)
            except Exception:
                # Continue even if KPI precomputation fails
                pass

    return ingested


def ingest_default_data() -> List[IngestedDataset]:
    return ingest_directory()


if __name__ == "__main__":
    results = ingest_default_data()
    print(json.dumps([dataset.__dict__ for dataset in results], indent=2))


