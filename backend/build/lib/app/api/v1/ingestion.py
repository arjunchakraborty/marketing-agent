"""Endpoints for data ingestion orchestration."""
from fastapi import APIRouter

from ...schemas.ingestion import (
    CsvIngestionRequest,
    CsvIngestionResponse,
    SourceRegistrationRequest,
    SourceRegistrationResponse,
)
from ...services.ingestion_service import IngestionService

router = APIRouter()
ingestion_service = IngestionService()


@router.post("/sources", response_model=SourceRegistrationResponse, summary="Register a data source")
async def register_source(payload: SourceRegistrationRequest) -> SourceRegistrationResponse:
    """Register a Shopify store, CSV feed, or plugin data source for ingestion."""
    result = ingestion_service.register_source(payload.model_dump())
    return SourceRegistrationResponse(source_id=result["source_id"], status=result["status"])


@router.post("/csv", response_model=CsvIngestionResponse, summary="Ingest CSV data")
async def ingest_csv(payload: CsvIngestionRequest) -> CsvIngestionResponse:
    """Kick off CSV ingestion job and return job metadata."""
    result = ingestion_service.submit_csv_job(payload.model_dump())
    return CsvIngestionResponse(
        job_id=result["job_id"],
        status=result["status"],
        ingested_count=result["ingested_count"],
        datasets=result["datasets"],
        warnings=result.get("warnings") or None,
    )
