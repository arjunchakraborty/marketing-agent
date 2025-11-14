"""Schemas for Klaviyo campaign data ingestion."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class KlaviyoIngestionRequest(BaseModel):
    """Request to ingest Klaviyo campaign CSV."""
    file_path: str = Field(..., description="Path to Klaviyo campaign CSV file")
    table_name: Optional[str] = Field(
        default="campaigns", description="Name of the table to create/update (default: campaigns)"
    )


class KlaviyoIngestionResponse(BaseModel):
    """Response from Klaviyo ingestion."""
    status: str
    table_name: str
    total_rows: int
    inserted: int
    updated: int
    errors: Optional[List[str]] = None
    columns: List[str]
    ingested_at: datetime = Field(default_factory=datetime.utcnow)

