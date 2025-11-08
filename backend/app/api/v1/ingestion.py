"""Endpoints for data ingestion orchestration."""
from fastapi import APIRouter

from ..schemas.ingestion import (
    CsvIngestionRequest,
    CsvIngestionResponse,
    SourceRegistrationRequest,
    SourceRegistrationResponse,
)

router = APIRouter()


@router.post("/sources", response_model=SourceRegistrationResponse, summary="Register a data source")
async def register_source(payload: SourceRegistrationRequest) -> SourceRegistrationResponse:
    """Register a Shopify store, CSV feed, or plugin data source for ingestion."""
    # Placeholder implementation; to be wired to ingestion orchestrator in future milestone.
    return SourceRegistrationResponse(source_id="src_0001", status="registered")


@router.post("/csv", response_model=CsvIngestionResponse, summary="Ingest CSV data")
async def ingest_csv(payload: CsvIngestionRequest) -> CsvIngestionResponse:
    """Kick off CSV ingestion job and return job metadata."""
    return CsvIngestionResponse(job_id="job_0001", status="accepted")
