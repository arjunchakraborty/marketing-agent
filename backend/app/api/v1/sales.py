"""Sales file upload endpoints."""
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from ...schemas.sales import SalesUploadRequest, SalesUploadResponse
from ...services.sales_upload_service import SalesUploadService

router = APIRouter()
sales_upload_service = SalesUploadService()


@router.post("/upload", response_model=SalesUploadResponse, summary="Upload sales file")
async def upload_sales_file(
    file: UploadFile = File(...),
    business: str | None = None,
    auto_ingest: bool = True,
) -> SalesUploadResponse:
    """
    Upload a sales file (CSV, Excel, JSON, or image) for processing and ingestion.
    
    Supports multiple file formats:
    - CSV files (.csv)
    - Excel files (.xlsx, .xls)
    - JSON files (.json)
    - Image files (.png, .jpg, .jpeg, .gif, .webp)
    
    Files are automatically processed and ingested into the database if auto_ingest is True.
    """
    try:
        # Read file content
        file_content = await file.read()
        
        # Process upload
        result = sales_upload_service.process_upload(
            file_content=file_content,
            filename=file.filename or "unknown",
            content_type=file.content_type,
            business=business,
            auto_ingest=auto_ingest,
        )

        # Check for errors
        errors = []
        if result.get("status") == "failed":
            error_msg = result.get("error", "Upload failed")
            errors.append(error_msg)

        return SalesUploadResponse(
            upload_id=result["upload_id"],
            filename=result["filename"],
            file_type=result["file_type"],
            file_size=result["file_size"],
            status=result["status"],
            ingested=result.get("ingested", False),
            table_name=result.get("table_name"),
            row_count=result.get("row_count"),
            errors=errors if errors else None,
            message=result.get("message", "Upload completed successfully"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

