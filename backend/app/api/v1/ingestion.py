"""Endpoints for data ingestion orchestration."""
import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

logger = logging.getLogger(__name__)

from ...schemas.ingestion import (
    CsvIngestionRequest,
    CsvIngestionResponse,
    SourceRegistrationRequest,
    SourceRegistrationResponse,
    ZipIngestionResponse,
)
from ...schemas.klaviyo import (
    CampaignDataIngestionRequest,
    CampaignDataIngestionResponse,
    CampaignDataZipUploadResponse,
    KlaviyoIngestionRequest,  # Backward compatibility
    KlaviyoIngestionResponse,  # Backward compatibility
    KlaviyoZipUploadResponse,  # Backward compatibility
)
from ...services.ingestion_service import IngestionService
from ...services.zip_handler import (
    cleanup_directory,
    cleanup_file,
    extract_zip_file,
    find_directory_in_directory,
    find_file_in_directory,
)
from ...workflows.klaviyo_ingestion import ingest_klaviyo_csv
from ...workflows.load_klaviyo_analysis_to_vector_db import (
    load_klaviyo_analysis_to_vector_db,
)
from ...workflows.local_csv_ingestion import ingest_directory

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


@router.post("/klaviyo", response_model=CampaignDataIngestionResponse, summary="Ingest campaign data CSV")
async def ingest_klaviyo_campaigns(payload: CampaignDataIngestionRequest) -> CampaignDataIngestionResponse:
    """
    Ingest campaign data CSV file from a file path.
    
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
        
        return CampaignDataIngestionResponse(
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
        raise HTTPException(status_code=500, detail=f"Campaign data ingestion failed: {str(e)}")


@router.post("/upload/klaviyo", response_model=CampaignDataZipUploadResponse, summary="Upload and ingest campaign data from zip file")
async def upload_klaviyo_zip(
    file: UploadFile = File(..., description="Zip file containing campaign data CSV and image analysis JSONs"),
    table_name: str = "campaigns",
    collection_name: str = "campaign_data",
    overwrite_existing: bool = False,
) -> CampaignDataZipUploadResponse:
    """
    Upload a zip file containing campaign data and image analyses.
    
    Expected zip structure:
    - email_campaigns.csv (or any CSV file with campaign data)
    - image-analysis-extract/ (folder containing JSON analysis files)
      - *.json files
    
    The zip file will be extracted, processed, and then deleted.
    """
    zip_file_path = None
    extract_dir = None
    
    try:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            zip_file_path = tmp_file.name
        
        # Extract zip file
        extract_dir = extract_zip_file(zip_file_path)
        
        # Find CSV file (look for email_campaigns.csv or any CSV file)
        csv_file = find_file_in_directory(extract_dir, "email_campaigns.csv") or \
                   find_file_in_directory(extract_dir, "*.csv")
        
        if not csv_file:
            raise HTTPException(
                status_code=400,
                detail="No CSV file found in zip. Expected email_campaigns.csv or any CSV file."
            )
        
        # Find image analysis folder
        image_analysis_folder = find_directory_in_directory(
            extract_dir, "image-analysis-extract"
        )
        
        # If not found, check if JSON files are in root
        if not image_analysis_folder:
            json_files = list(Path(extract_dir).glob("*.json"))
            if json_files:
                image_analysis_folder = extract_dir
        
        # Ingest CSV into database
        csv_result = None
        if csv_file:
            csv_result = ingest_klaviyo_csv(
                csv_file_path=csv_file,
                table_name=table_name,
            )
        
        # Load into vector DB if image analysis folder exists
        vector_db_result = None
        if image_analysis_folder:
            vector_db_result = load_klaviyo_analysis_to_vector_db(
                csv_file_path=csv_file,
                image_analysis_folder=image_analysis_folder,
                collection_name=collection_name,
                overwrite_existing=overwrite_existing,
            )
        
        # Build response
        csv_response = None
        if csv_result:
            csv_response = CampaignDataIngestionResponse(
                status=csv_result["status"],
                table_name=csv_result["table_name"],
                total_rows=csv_result["total_rows"],
                inserted=csv_result["inserted"],
                updated=csv_result["updated"],
                errors=csv_result.get("errors"),
                columns=csv_result["columns"],
            )
        
        return CampaignDataZipUploadResponse(
            status="completed",
            csv_ingestion=csv_response,
            vector_db_loading=vector_db_result,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process campaign data zip file: {str(e)}"
        )
    finally:
        # Cleanup: remove zip file and extracted directory
        if zip_file_path:
            cleanup_file(zip_file_path)
        if extract_dir:
            cleanup_directory(extract_dir)


@router.post("/upload/shopify-integration", response_model=ZipIngestionResponse, summary="Upload and ingest Shopify integration data from zip file")
async def upload_shopify_integration_zip(
    file: UploadFile = File(..., description="Zip file containing Shopify integration datasets"),
    business: str = None,
) -> ZipIngestionResponse:
    """
    Upload a zip file containing Shopify integration datasets for ingestion.
    
    Expected zip structure:
    - business_name/
      - category/
        - dataset.csv
    
    The zip file will be extracted, processed, and then deleted.
    """
    zip_file_path = None
    extract_dir = None
    
    try:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            zip_file_path = tmp_file.name
        
        # Extract zip file
        extract_dir = extract_zip_file(zip_file_path)
        extract_path = Path(extract_dir)
        
        logger.info(f"Extracted zip to {extract_path}")
        logger.info(f"Contents of extract_dir: {list(extract_path.iterdir())}")
        
        # Handle case where zip has a single root directory
        # Check if extract_dir contains only one directory
        dir_contents = [item for item in extract_path.iterdir() if item.is_dir()]
        file_contents = [item for item in extract_path.iterdir() if item.is_file()]
        
        if len(dir_contents) == 1 and len(file_contents) == 0:
            # Zip has a single root directory, use that as the base path
            extract_path = dir_contents[0]
            logger.info(f"Zip has single root directory '{extract_path.name}', using it as base path")
        
        # Validate directory structure
        if not extract_path.exists():
            raise HTTPException(
                status_code=400,
                detail=f"Extracted directory does not exist: {extract_path}"
            )
        
        # Check if we have any business directories
        business_dirs = [item for item in extract_path.iterdir() if item.is_dir()]
        if not business_dirs:
            raise HTTPException(
                status_code=400,
                detail=f"No business directories found in {extract_path}. Expected structure: business_name/category/dataset.csv"
            )
        
        logger.info(f"Found {len(business_dirs)} business directories: {[d.name for d in business_dirs]}")
        
        # Ingest directory
        ingested_datasets = ingest_directory(
            base_path=extract_path,
            business=business,
        )
        
        if not ingested_datasets:
            raise HTTPException(
                status_code=400,
                detail=f"No datasets were ingested. Check that CSV files exist in the expected structure: business_name/category/dataset.csv"
            )
        
        logger.info(f"Successfully ingested {len(ingested_datasets)} datasets")
        
        # Build response details
        details = {
            "ingested_count": len(ingested_datasets),
            "datasets": [
                {
                    "table_name": ds.table_name,
                    "business": ds.business,
                    "category": ds.category,
                    "dataset_name": ds.dataset_name,
                    "row_count": ds.row_count,
                    "columns": ds.columns,
                }
                for ds in ingested_datasets
            ],
        }
        
        return ZipIngestionResponse(
            status="completed",
            extracted_path=str(extract_path),
            details=details,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process Shopify integration zip file: {str(e)}"
        )
    finally:
        # Cleanup: remove zip file and extracted directory
        if zip_file_path:
            cleanup_file(zip_file_path)
        if extract_dir:
            cleanup_directory(extract_dir)


# Backward compatibility - keep old CSV endpoint
@router.post("/upload/csv", response_model=ZipIngestionResponse, summary="[Deprecated] Upload and ingest CSV data from zip file - use /upload/shopify-integration instead")
async def upload_csv_zip(
    file: UploadFile = File(..., description="Zip file containing CSV datasets"),
    business: str = None,
) -> ZipIngestionResponse:
    """Deprecated: Use /upload/shopify-integration instead."""
    return await upload_shopify_integration_zip(file, business)


@router.post("/upload/vector-db", response_model=ZipIngestionResponse, summary="Upload and load data into vector database from zip file")
async def upload_vector_db_zip(
    file: UploadFile = File(..., description="Zip file containing CSV and image analysis JSONs"),
    collection_name: str = "campaign_data",
    overwrite_existing: bool = False,
) -> ZipIngestionResponse:
    """
    Upload a zip file containing campaign data and image analyses for vector database.
    
    Expected zip structure:
    - email_campaigns.csv (or any CSV file with campaign data)
    - image-analysis-extract/ (folder containing JSON analysis files)
      - *.json files
    
    The zip file will be extracted, processed, and then deleted.
    """
    zip_file_path = None
    extract_dir = None
    
    try:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            zip_file_path = tmp_file.name
        
        # Extract zip file
        extract_dir = extract_zip_file(zip_file_path)
        
        # Find CSV file
        csv_file = find_file_in_directory(extract_dir, "email_campaigns.csv") or \
                   find_file_in_directory(extract_dir, "*.csv")
        
        if not csv_file:
            raise HTTPException(
                status_code=400,
                detail="No CSV file found in zip. Expected email_campaigns.csv or any CSV file."
            )
        
        # Find image analysis folder
        image_analysis_folder = find_directory_in_directory(
            extract_dir, "image-analysis-extract"
        )
        
        # If not found, check if JSON files are in root
        if not image_analysis_folder:
            json_files = list(Path(extract_dir).glob("*.json"))
            if json_files:
                image_analysis_folder = extract_dir
        
        if not image_analysis_folder:
            raise HTTPException(
                status_code=400,
                detail="No image analysis folder or JSON files found in zip."
            )
        
        # Load into vector DB
        vector_db_result = load_klaviyo_analysis_to_vector_db(
            csv_file_path=csv_file,
            image_analysis_folder=image_analysis_folder,
            collection_name=collection_name,
            overwrite_existing=overwrite_existing,
        )
        
        return ZipIngestionResponse(
            status="completed",
            extracted_path=extract_dir,
            details=vector_db_result,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process vector DB zip file: {str(e)}"
        )
    finally:
        # Cleanup: remove zip file and extracted directory
        if zip_file_path:
            cleanup_file(zip_file_path)
        if extract_dir:
            cleanup_directory(extract_dir)
