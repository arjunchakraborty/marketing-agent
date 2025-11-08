"""Schemas for data ingestion operations."""
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class SourceRegistrationRequest(BaseModel):
    name: str = Field(..., description="Human-readable name for the data source")
    source_type: str = Field(..., description="Type of source, e.g., shopify, csv, plugin")
    configuration: Dict[str, str] = Field(default_factory=dict, description="Source-specific configuration settings")


class SourceRegistrationResponse(BaseModel):
    source_id: str
    status: str
    registered_at: datetime = Field(default_factory=datetime.utcnow)


class CsvIngestionRequest(BaseModel):
    dataset_name: str
    file_path: str
    column_mappings: Dict[str, str] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, str] = Field(default_factory=dict)


class CsvIngestionResponse(BaseModel):
    job_id: str
    status: str
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    warnings: Optional[List[str]] = None
