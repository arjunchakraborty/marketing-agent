"""Service for handling sales file uploads in multiple formats."""
import json
import mimetypes
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from ..core.config import settings
from ..workflows.local_csv_ingestion import ingest_directory


class SalesUploadService:
    """Handle multi-format file uploads for sales data."""

    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "marketing_agent_uploads"
        self.temp_dir.mkdir(exist_ok=True)

    def detect_file_type(self, filename: str, content_type: Optional[str] = None) -> str:
        """Detect file type from filename and content type."""
        if content_type:
            if "csv" in content_type or filename.endswith(".csv"):
                return "csv"
            if "excel" in content_type or "spreadsheet" in content_type:
                return "excel"
            if "json" in content_type or filename.endswith(".json"):
                return "json"
            if "image" in content_type:
                return "image"

        # Fallback to extension
        ext = Path(filename).suffix.lower()
        if ext == ".csv":
            return "csv"
        if ext in [".xlsx", ".xls"]:
            return "excel"
        if ext == ".json":
            return "json"
        if ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
            return "image"

        return "unknown"

    def process_csv(self, file_path: Path, business: Optional[str] = None) -> Dict[str, Any]:
        """Process CSV file and ingest into database."""
        try:
            df = pd.read_csv(file_path)
            row_count = len(df)
            
            # Create temporary directory structure for ingestion
            if business:
                business_dir = self.temp_dir / business
                business_dir.mkdir(exist_ok=True)
                sales_dir = business_dir / "sales"
                sales_dir.mkdir(exist_ok=True)
                target_file = sales_dir / file_path.name
            else:
                sales_dir = self.temp_dir / "sales"
                sales_dir.mkdir(exist_ok=True)
                target_file = sales_dir / file_path.name

            # Copy file to ingestion structure
            import shutil
            shutil.copy2(file_path, target_file)

            # Ingest using existing workflow
            ingested = ingest_directory(sales_dir.parent if business else self.temp_dir, business=business)
            
            table_name = None
            if ingested:
                table_name = ingested[0].table_name if ingested else None

            return {
                "status": "completed",
                "row_count": row_count,
                "table_name": table_name,
                "ingested": True,
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "ingested": False,
            }

    def process_excel(self, file_path: Path, business: Optional[str] = None) -> Dict[str, Any]:
        """Process Excel file and ingest into database."""
        try:
            # Read all sheets
            excel_file = pd.ExcelFile(file_path)
            total_rows = 0
            sheets_processed = []

            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                total_rows += len(df)
                
                # Save each sheet as CSV for ingestion
                if business:
                    business_dir = self.temp_dir / business
                    business_dir.mkdir(exist_ok=True)
                    sales_dir = business_dir / "sales"
                    sales_dir.mkdir(exist_ok=True)
                    csv_file = sales_dir / f"{file_path.stem}_{sheet_name}.csv"
                else:
                    sales_dir = self.temp_dir / "sales"
                    sales_dir.mkdir(exist_ok=True)
                    csv_file = sales_dir / f"{file_path.stem}_{sheet_name}.csv"

                df.to_csv(csv_file, index=False)
                sheets_processed.append(sheet_name)

            # Ingest all CSV files
            ingested = ingest_directory(sales_dir.parent if business else self.temp_dir, business=business)

            return {
                "status": "completed",
                "row_count": total_rows,
                "sheets_processed": sheets_processed,
                "ingested": True,
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "ingested": False,
            }

    def process_json(self, file_path: Path, business: Optional[str] = None) -> Dict[str, Any]:
        """Process JSON file and ingest into database."""
        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            # Convert to DataFrame
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                # If it's a dict, try to find a list of records
                for key, value in data.items():
                    if isinstance(value, list):
                        df = pd.DataFrame(value)
                        break
                else:
                    # Single record
                    df = pd.DataFrame([data])
            else:
                return {
                    "status": "failed",
                    "error": "Unsupported JSON structure",
                    "ingested": False,
                }

            row_count = len(df)

            # Save as CSV for ingestion
            if business:
                business_dir = self.temp_dir / business
                business_dir.mkdir(exist_ok=True)
                sales_dir = business_dir / "sales"
                sales_dir.mkdir(exist_ok=True)
                csv_file = sales_dir / f"{file_path.stem}.csv"
            else:
                sales_dir = self.temp_dir / "sales"
                sales_dir.mkdir(exist_ok=True)
                csv_file = sales_dir / f"{file_path.stem}.csv"

            df.to_csv(csv_file, index=False)

            # Ingest
            ingested = ingest_directory(sales_dir.parent if business else self.temp_dir, business=business)

            return {
                "status": "completed",
                "row_count": row_count,
                "ingested": True,
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "ingested": False,
            }

    def process_image(self, file_path: Path) -> Dict[str, Any]:
        """Process image file - store for later analysis."""
        try:
            # For now, just store the image path
            # In the future, this could trigger image analysis
            return {
                "status": "completed",
                "stored": True,
                "file_path": str(file_path),
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "stored": False,
            }

    def process_upload(
        self,
        file_content: bytes,
        filename: str,
        content_type: Optional[str] = None,
        business: Optional[str] = None,
        auto_ingest: bool = True,
    ) -> Dict[str, Any]:
        """Process uploaded file based on type."""
        upload_id = f"upload_{uuid.uuid4().hex[:8]}"
        file_type = self.detect_file_type(filename, content_type)

        # Save file temporarily
        temp_file = self.temp_dir / f"{upload_id}_{filename}"
        temp_file.write_bytes(file_content)
        file_size = len(file_content)

        result = {
            "upload_id": upload_id,
            "filename": filename,
            "file_type": file_type,
            "file_size": file_size,
            "status": "uploaded",
        }

        if not auto_ingest:
            return result

        # Process based on file type
        if file_type == "csv":
            process_result = self.process_csv(temp_file, business)
        elif file_type == "excel":
            process_result = self.process_excel(temp_file, business)
        elif file_type == "json":
            process_result = self.process_json(temp_file, business)
        elif file_type == "image":
            process_result = self.process_image(temp_file)
        else:
            return {
                **result,
                "status": "failed",
                "message": f"Unsupported file type: {file_type}",
                "ingested": False,
            }

        result.update(process_result)
        result["status"] = process_result.get("status", "completed")
        result["ingested"] = process_result.get("ingested", False)
        result["message"] = process_result.get("error") or "File processed successfully"

        return result

