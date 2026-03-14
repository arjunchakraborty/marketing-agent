"""Ingestion service orchestrating CSV and API datasets."""
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any, Dict

from ..core.config import settings
from ..workflows.local_csv_ingestion import ingest_directory


class IngestionService:
    """Coordinate ingestion flows for Shopify, CSV, and plugin sources."""

    def register_source(self, configuration: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new data source and return metadata."""
        return {"source_id": "src_placeholder", "status": "registered", "configuration": configuration}

    def submit_csv_job(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a CSV ingestion job into the orchestration queue."""
        directory = payload.get("file_path") or payload.get("directory")
        business = payload.get("business")

        base_directory = Path(directory) if directory else Path(settings.ingestion_data_root)
        try:
            ingested = ingest_directory(base_directory, business=business)
            status = "completed"
            warnings = []
        except FileNotFoundError as exc:
            ingested = []
            status = "failed"
            warnings = [str(exc)]

        return {
            "job_id": f"job_{uuid.uuid4().hex[:8]}",
            "status": status,
            "ingested_count": len(ingested),
            "datasets": [dataset.__dict__ for dataset in ingested],
            "warnings": warnings,
        }

