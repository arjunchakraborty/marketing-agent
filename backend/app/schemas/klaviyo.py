"""Schemas for campaign data ingestion."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CampaignDataIngestionRequest(BaseModel):
    """Request to ingest campaign data CSV."""
    file_path: str = Field(..., description="Path to campaign data CSV file")
    table_name: Optional[str] = Field(
        default="campaigns", description="Name of the table to create/update (default: campaigns)"
    )


class CampaignDataIngestionResponse(BaseModel):
    """Response from campaign data ingestion."""
    status: str
    table_name: str
    total_rows: int
    inserted: int
    updated: int
    errors: Optional[List[str]] = None
    columns: List[str]
    ingested_at: datetime = Field(default_factory=datetime.utcnow)


class CampaignDataZipUploadResponse(BaseModel):
    """Response from campaign data zip file upload and ingestion."""
    status: str
    csv_ingestion: Optional[CampaignDataIngestionResponse] = None
    vector_db_loading: Optional[Dict[str, Any]] = None
    processed_at: datetime = Field(default_factory=datetime.utcnow)


# Backward compatibility aliases
KlaviyoIngestionRequest = CampaignDataIngestionRequest
KlaviyoIngestionResponse = CampaignDataIngestionResponse
KlaviyoZipUploadResponse = CampaignDataZipUploadResponse

