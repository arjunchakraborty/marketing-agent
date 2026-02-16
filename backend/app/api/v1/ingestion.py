"""Endpoints for data ingestion orchestration."""
import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, Query
from typing import Optional
from pydantic import Field
from typing import Optional

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
from ...services.vector_db_service import delete_collection_if_exists
from ...workflows.local_csv_ingestion import ingest_directory
from ...workflows.product_zip_ingestion import load_product_zip_to_vector_db

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

"""
@router.post("/klaviyo", response_model=CampaignDataIngestionResponse, summary="Ingest campaign data CSV")
async def ingest_klaviyo_campaigns(payload: CampaignDataIngestionRequest) -> CampaignDataIngestionResponse:
"""
"""
    Ingest campaign data CSV file from a file path.
    
    The CSV should contain campaign data with columns like:
    - campaign_id, campaign_name, subject
    - sent_count, opened_count, clicked_count, converted_count
    - revenue, open_rate, click_rate, conversion_rate
    - sent_at (date/time)
    
    Column names will be automatically normalized to match expected format.
"""
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
"""
"""
@router.post("/upload/klaviyo", response_model=CampaignDataZipUploadResponse, summary="Upload and ingest campaign data from zip file")
async def upload_klaviyo_zip(
    file: UploadFile = File(..., description="Zip file containing campaign data CSV and image analysis JSONs."),
    table_name: str = "campaigns",
    collection_name: Optional[str] = Query(None, description="Collection name (defaults to 'UCO_Gear_Campaigns')."),
    business_name: Optional[str] = Query(None, description="Optional name of the business (for metadata only)."),
    overwrite_existing: bool = False,
    replace_collection: bool = Query(False, description="Delete existing collection before load so it is recreated with cosine (better search)."),
) -> CampaignDataZipUploadResponse:
"""
"""
    Upload a zip file containing campaign data and image analyses.
    
    Business name is extracted from the zip filename if not provided.
    Example: "UCO_Gear_Campaigns.zip" -> business_name = "UCO_Gear"
    
    Expected zip structure:
    - email_campaigns.csv (or any CSV file with campaign data)
    - image-analysis-extract/ (folder containing JSON analysis files)
      - *.json files (can be in subdirectories)
    
    The workflow will:
    1. Extract and ingest CSV campaign data into database
    2. Process image-analysis-extract folder (if present):
       - Load JSON analysis files (searches recursively in subdirectories)
       - Match analyses to campaigns from CSV
       - Store campaign data with image analyses in vector database
    3. Clean up extracted files
    
    The zip file will be extracted, processed, and then deleted.
"""
"""
    zip_file_path = None
    extract_dir = None
    
    try:
        # Save uploaded file to temporary location
        original_filename = file.filename or "campaigns.zip"
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            zip_file_path = tmp_file.name
        
        # Always use UCO_Gear_Campaigns collection
        if not collection_name or collection_name.strip() == "":
            collection_name = "UCO_Gear_Campaigns"

        if replace_collection:
            delete_collection_if_exists(collection_name)

        logger.info(f"Using collection name: '{collection_name}' for vector DB ingestion")

        # Extract zip file
        extract_dir = extract_zip_file(zip_file_path)
        
        # Find CSV file (look for email_campaigns.csv or any CSV file)
        csv_file = find_file_in_directory(extract_dir, "campaigns.csv") or \
                   find_file_in_directory(extract_dir, "*.csv")
        
        if not csv_file:
            raise HTTPException(
                status_code=400,
                detail="No CSV file found in zip. Expected email_campaigns.csv or any CSV file."
            )
        
        # Find image analysis folder - search for image-analysis-extract directory
        image_analysis_folder = find_directory_in_directory(
            extract_dir, "image-analysis-extract"
        )
        
        # If not found, search recursively for any folder containing JSON files
        if not image_analysis_folder:
            extract_path = Path(extract_dir)
            # Search for folders with JSON files
            for potential_folder in extract_path.rglob("*"):
                if potential_folder.is_dir():
                    json_files = list(potential_folder.glob("*.json"))
                    if json_files:
                        logger.info(f"Found JSON files in folder: {potential_folder}")
                        image_analysis_folder = str(potential_folder)
                        break
        
        # If still not found, check if JSON files are in root
        if not image_analysis_folder:
            json_files = list(Path(extract_dir).glob("*.json"))
            if json_files:
                logger.info(f"Found {len(json_files)} JSON files in root directory")
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
            logger.info(f"Processing image analyses from folder: {image_analysis_folder}")
            try:
                vector_db_result = load_klaviyo_analysis_to_vector_db(
                    csv_file_path=csv_file,
                    image_analysis_folder=image_analysis_folder,
                    collection_name=collection_name,
                    overwrite_existing=overwrite_existing,
                )
                logger.info(f"Successfully loaded image analyses into vector DB. Collection: {collection_name}")
            except Exception as e:
                logger.error(f"Failed to load image analyses into vector DB: {str(e)}", exc_info=True)
                # Don't fail the entire upload if image analysis fails
                vector_db_result = {
                    "status": "error",
                    "error": f"Image analysis loading failed: {str(e)}",
                    "total_campaigns": 0,
                    "loaded": 0,
                    "skipped": 0,
                    "errors": 1,
                    "campaigns_with_images": 0,
                    "campaigns_without_images": 0,
                    "collection_name": collection_name,
                }
        else:
            logger.info("No image-analysis-extract folder or JSON files found in zip. Skipping image analysis loading.")
        
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
"""

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
    collection_name: str = "UCO_Gear_Campaigns",
    overwrite_existing: bool = False,
    replace_collection: bool = Query(False, description="Delete existing collection before load so it is recreated with cosine (better search)."),
) -> ZipIngestionResponse:
    """
    Upload a zip file containing campaign data and image analyses for vector database.

    Expected zip structure:
    - email_campaigns.csv (or any CSV file with campaign data)
    - image-analysis-extract/ (folder containing JSON analysis files)
      - *.json files

    If replace_collection is True, the collection is deleted first so the next load
    creates it with cosine distance (improves semantic search ranking).

    The zip file will be extracted, processed, and then deleted.
    """
    zip_file_path = None
    extract_dir = None

    try:
        if replace_collection:
            delete_collection_if_exists(collection_name)

        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            zip_file_path = tmp_file.name
        
        # Extract zip file
        extract_dir = extract_zip_file(zip_file_path)
        
        # Find CSV file
        csv_file = find_file_in_directory(extract_dir, "campaigns.csv") or \
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

        if not image_analysis_folder:
            extract_path = Path(extract_dir)
            # Search for folders with JSON files
            for potential_folder in extract_path.rglob("*"):
                if potential_folder.is_dir():
                    logger.info(f"looking for images analysis in  folder: {potential_folder}")
                    json_files = list(potential_folder.glob("*.json"))
                    if json_files:
                        logger.info(f"Found JSON files in folder: {potential_folder}")
                        image_analysis_folder = str(potential_folder)
                        break
        
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


@router.post("/upload/products", response_model=ZipIngestionResponse, summary="Upload and ingest products with images from zip file")
async def upload_products_zip(
    file: UploadFile = File(..., description="Zip file containing product data (CSV/JSON) and product images. Business name will be extracted from zip filename if not provided."),
    business_name: Optional[str] = Query(None, description="Optional name of the business. If not provided, extracted from zip filename."),
    collection_name: Optional[str] = Query(None, description="Optional custom collection name (default: UCO_Gear_Products)"),
) -> ZipIngestionResponse:
    """
    Upload a zip file containing products and images for vector database storage.
    
    Business name is extracted from the zip filename if not provided.
    Example: "acme_products.zip" -> business_name = "acme"
    
    Images are stored in a private folder on the server: storage/product_images/{business_name}/{product_id}/
    
    Expected zip structure:
    - products.csv or products.json (product data file)
    - images/ (folder containing product images)
      - *.jpg, *.png, etc.
    
    Or flat structure:
    - products.csv or products.json
    - product_image_1.jpg
    - product_image_2.png
    - ...
    
    The workflow will:
    1. Extract business name from zip filename (if not provided)
    2. Extract and process product data (CSV or JSON)
    3. Match images to products based on filename patterns
    4. Store images in private server folder: storage/product_images/{business_name}/{product_id}/
    5. Store products and image paths in vector database
    
    Product data should include fields like:
    - product_id, id, or sku (for identification)
    - name or product_name
    - description or product_description
    - category or product_category
    - price or product_price (optional)
    """
    zip_file_path = None
    
    try:
        # Save uploaded file to temporary location
        original_filename = file.filename or "products.zip"
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            zip_file_path = tmp_file.name
        
        # If business_name not provided, extract from original filename
        if not business_name:
            from ...workflows.product_zip_ingestion import _extract_business_name_from_filename
            # Extract business name from the original uploaded filename
            business_name = _extract_business_name_from_filename(original_filename)
            logger.info(f"Extracted business name '{business_name}' from uploaded filename '{original_filename}'")
        
        # Load products and images into vector DB
        result = load_product_zip_to_vector_db(
            zip_file_path=zip_file_path,
            business_name=business_name,
            collection_name=collection_name,
            cleanup_extracted=True,
        )
        
        if result["status"] == "error":
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Product ingestion failed")
            )
        
        return ZipIngestionResponse(
            status="completed",
            extracted_path="",  # Already cleaned up
            details={
                "products_processed": result["products_processed"],
                "images_stored": result["images_stored"],
                "collection_name": result["collection_name"],
                "product_ids": result["product_ids"],
            },
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process products zip file: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process products zip file: {str(e)}"
        )
    finally:
        # Cleanup: remove zip file
        if zip_file_path:
            cleanup_file(zip_file_path)
