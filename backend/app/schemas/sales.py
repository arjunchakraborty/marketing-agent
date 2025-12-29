"""Schemas for sales file upload endpoints."""
from typing import List, Optional

from pydantic import BaseModel, Field


class SalesUploadRequest(BaseModel):
    """Request schema for sales file upload."""
    
    business: Optional[str] = Field(None, description="Business name for the uploaded data")
    auto_ingest: bool = Field(True, description="Automatically ingest file after upload")


class SalesUploadResponse(BaseModel):
    """Response schema for sales file upload."""
    
    upload_id: str = Field(..., description="Unique identifier for the upload")
    filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="Detected file type (csv, excel, json, image)")
    file_size: int = Field(..., description="File size in bytes")
    status: str = Field(..., description="Upload status: uploaded, processing, completed, failed")
    ingested: bool = Field(False, description="Whether file was successfully ingested")
    table_name: Optional[str] = Field(None, description="Database table name if ingested")
    row_count: Optional[int] = Field(None, description="Number of rows ingested")
    errors: Optional[List[str]] = Field(None, description="List of errors if any occurred")
    message: str = Field(..., description="Status message")

