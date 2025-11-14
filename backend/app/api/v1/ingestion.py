"""Endpoints for data ingestion orchestration."""
from fastapi import APIRouter, HTTPException

from ...schemas.ingestion import (
    CsvIngestionRequest,
    CsvIngestionResponse,
    SourceRegistrationRequest,
    SourceRegistrationResponse,
)
from ...schemas.klaviyo import KlaviyoIngestionRequest, KlaviyoIngestionResponse
from ...services.ingestion_service import IngestionService
from ...workflows.klaviyo_ingestion import ingest_klaviyo_csv

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


@router.post("/klaviyo", response_model=KlaviyoIngestionResponse, summary="Ingest Klaviyo campaign CSV")
async def ingest_klaviyo_campaigns(payload: KlaviyoIngestionRequest) -> KlaviyoIngestionResponse:
    """
    Ingest Klaviyo campaign CSV file from a file path.
    
    The CSV should contain campaign data with columns like:
    - campaign_id, campaign_name, subject
    - sent_count, opened_count, clicked_count, converted_count
    - revenue, open_rate, click_rate, conversion_rate
    - sent_at (date/time)
    
    Column names will be automatically normalized to match expected format.
    """
    try:
        result = ingest_klaviyo_csv(
            csv_file_path=payload.file_path,
            table_name=payload.table_name or "campaigns",
        )
        
        return KlaviyoIngestionResponse(
            status=result["status"],
            table_name=result["table_name"],
            total_rows=result["total_rows"],
            inserted=result["inserted"],
            updated=result["updated"],
            errors=result.get("errors"),
            columns=result["columns"],
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"File not found: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Klaviyo ingestion failed: {str(e)}")
