"""Service for bulk analyzing email images and storing results in database."""
from __future__ import annotations

import base64
import json
import logging
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.engine import Engine

from ..core.config import settings
from ..db.session import engine
from ..models.campaign_analysis import ImageAnalysisResult
from .image_analysis_service import ImageAnalysisService

logger = logging.getLogger(__name__)


def _extract_campaign_id_from_filename(filename: str) -> Optional[str]:
    """
    Extract campaign ID from image filename.
    
    Handles formats like:
    - www.klaviyo.com_campaign_01K4QVNYM1QKSK61X7PXR019DF_web-view.png
    - www.klaviyo.com_sms_campaign_01K77ZJ84N3C9EW4E3VDQXP320_webview_(iPhone 14 Pro Max).png
    - campaign_01K4QVNYM1QKSK61X7PXR019DF.jpg
    """
    # Klaviyo campaign IDs are typically 26 characters (alphanumeric, uppercase)
    # Pattern 1: Extract ID between _campaign_ and _webview or _web-view
    pattern1 = r"(?:sms_)?campaign_([A-Z0-9]{26})"
    match = re.search(pattern1, filename, re.IGNORECASE)
    if match:
        campaign_id = match.group(1)
        logger.debug(f"Extracted campaign ID using pattern1: {campaign_id} from {filename}")
        return campaign_id
    
    # Pattern 2: Extract ID after _campaign_ (more flexible, handles variations)
    pattern2 = r"_campaign_([A-Z0-9]{26})"
    match = re.search(pattern2, filename, re.IGNORECASE)
    if match:
        campaign_id = match.group(1)
        logger.debug(f"Extracted campaign ID using pattern2: {campaign_id} from {filename}")
        return campaign_id
    
    # Pattern 3: Extract ID after campaign_ (without underscore prefix)
    pattern3 = r"campaign_([A-Z0-9]{26})"
    match = re.search(pattern3, filename, re.IGNORECASE)
    if match:
        campaign_id = match.group(1)
        logger.debug(f"Extracted campaign ID using pattern3: {campaign_id} from {filename}")
        return campaign_id
    
    # Pattern 4: Generic long ID (fallback - Klaviyo IDs are typically 26 chars)
    pattern4 = r"([A-Z0-9]{26})"
    match = re.search(pattern4, filename, re.IGNORECASE)
    if match:
        campaign_id = match.group(1)
        logger.debug(f"Extracted campaign ID using pattern4 (generic): {campaign_id} from {filename}")
        return campaign_id
    
    logger.warning(f"Could not extract campaign ID from filename: {filename}")
    return None


def analyze_and_store_image(
    image_path: Path,
    campaign_id: Optional[str],
    experiment_run_id: str,
    image_analysis_service: ImageAnalysisService,
    db_engine: Engine,
    skip_existing: bool = True,
) -> Dict[str, any]:
    """
    Analyze a single image and store results in database.
    
    Args:
        image_path: Path to the image file
        campaign_id: Campaign ID extracted from filename
        experiment_run_id: Experiment run ID for grouping analyses
        image_analysis_service: Initialized image analysis service
        db_engine: Database engine
        skip_existing: If True, skip images that already have analysis stored
        
    Returns:
        Dictionary with analysis result and status
    """
    image_id = str(uuid.uuid4())
    
    # Check if analysis already exists
    if skip_existing:
        with db_engine.begin() as connection:
            result = connection.execute(
                text("""
                    SELECT id FROM image_analysis_results 
                    WHERE image_path = :image_path AND experiment_run_id = :experiment_run_id
                """),
                {"image_path": str(image_path), "experiment_run_id": experiment_run_id}
            )
            if result.fetchone():
                logger.info(f"Skipping {image_path.name} - analysis already exists")
                return {"status": "skipped", "image_path": str(image_path)}
    
    try:
        # Read image and convert to base64
        with open(image_path, "rb") as f:
            image_data = f.read()
            image_base64 = base64.b64encode(image_data).decode("utf-8")
        
        # Analyze image
        logger.info(f"Analyzing image: {image_path.name} (campaign_id: {campaign_id})")
        analysis_result = image_analysis_service.analyze_image(
            image_base64=image_base64,
            campaign_id=campaign_id,
            campaign_name=None,
            analysis_type="full",
            use_feature_detection=False,
        )
        
        # Extract email features and catalog
        email_features = analysis_result.get("email_features", [])
        feature_catalog = analysis_result.get("feature_catalog", {})
        
        # Store in database
        with db_engine.begin() as connection:
            connection.execute(
                text("""
                    INSERT INTO image_analysis_results
                    (experiment_run_id, campaign_id, image_id, image_path, visual_elements, 
                     dominant_colors, composition_analysis, text_content, overall_description, 
                     marketing_relevance, email_features, feature_catalog)
                    VALUES (:experiment_run_id, :campaign_id, :image_id, :image_path, :visual_elements,
                            :dominant_colors, :composition_analysis, :text_content, :overall_description, 
                            :marketing_relevance, :email_features, :feature_catalog)
                """),
                {
                    "experiment_run_id": experiment_run_id,
                    "campaign_id": campaign_id,
                    "image_id": analysis_result.get("image_id", image_id),
                    "image_path": str(image_path),
                    "visual_elements": json.dumps(analysis_result.get("visual_elements", [])),
                    "dominant_colors": json.dumps(analysis_result.get("dominant_colors", [])),
                    "composition_analysis": analysis_result.get("composition_analysis"),
                    "text_content": analysis_result.get("text_content"),
                    "overall_description": analysis_result.get("overall_description"),
                    "marketing_relevance": analysis_result.get("marketing_relevance"),
                    "email_features": json.dumps(email_features) if email_features else None,
                    "feature_catalog": json.dumps(feature_catalog) if feature_catalog else None,
                }
            )
            
            # Store individual features in email_feature_catalog table
            if email_features and campaign_id:
                for feature in email_features:
                    try:
                        feature_category = feature.get("feature_category", "content")
                        feature_type = feature.get("feature_type", "unknown")
                        bbox = feature.get("bbox")
                        confidence = feature.get("confidence", 0.0)
                        position = feature.get("position")
                        
                        # Extract metadata
                        metadata = {
                            "text_content": feature.get("text_content"),
                            "color": feature.get("color"),
                        }
                        
                        connection.execute(
                            text("""
                                INSERT INTO email_feature_catalog
                                (experiment_run_id, campaign_id, feature_category, feature_type,
                                 feature_description, bbox, confidence, position, mData)
                                VALUES (:experiment_run_id, :campaign_id, :feature_category, :feature_type,
                                        :feature_description, :bbox, :confidence, :position, :mData)
                            """),
                            {
                                "experiment_run_id": experiment_run_id,
                                "campaign_id": campaign_id,
                                "feature_category": feature_category,
                                "feature_type": feature_type,
                                "feature_description": json.dumps(feature),
                                "bbox": json.dumps(bbox) if bbox else None,
                                "confidence": confidence,
                                "position": position,
                                "mData": json.dumps(metadata),
                            }
                        )
                    except Exception as e:
                        logger.error(f"Failed to store feature {feature.get('feature_type')}: {str(e)}", exc_info=True)
                        continue
        
        logger.info(f"Successfully analyzed and stored: {image_path.name}")
        return {
            "status": "success",
            "image_path": str(image_path),
            "campaign_id": campaign_id,
            "image_id": analysis_result.get("image_id", image_id),
            "features_detected": len(email_features),
        }
        
    except Exception as e:
        logger.error(f"Failed to analyze {image_path.name}: {type(e).__name__}: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "image_path": str(image_path),
            "campaign_id": campaign_id,
            "error": str(e),
        }


def analyze_all_images_in_directory(
    directory_path: str,
    experiment_run_id: Optional[str] = None,
    skip_existing: bool = True,
    db_engine: Optional[Engine] = None,
) -> Dict[str, any]:
    """
    Analyze all images in a directory and store results in database.
    
    Args:
        directory_path: Path to directory containing images
        experiment_run_id: Experiment run ID (defaults to timestamp-based ID)
        skip_existing: If True, skip images that already have analysis
        db_engine: Database engine (defaults to global engine)
        
    Returns:
        Dictionary with summary statistics
    """
    work_engine = db_engine or engine
    image_dir = Path(directory_path)
    
    if not image_dir.exists():
        raise ValueError(f"Directory does not exist: {directory_path}")
    
    if not image_dir.is_dir():
        raise ValueError(f"Path is not a directory: {directory_path}")
    
    # Generate experiment_run_id if not provided
    if not experiment_run_id:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        experiment_run_id = f"bulk_analysis_{timestamp}"
    
    logger.info(f"Starting bulk image analysis: directory={directory_path}, experiment_run_id={experiment_run_id}")
    
    # Ensure tables exist
    ImageAnalysisResult.__table__.create(work_engine, checkfirst=True)
    
    # Find all image files
    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    image_files = [
        f for f in image_dir.iterdir()
        if f.is_file() and f.suffix.lower() in image_extensions
    ]
    
    logger.info(f"Found {len(image_files)} image files")
    
    if not image_files:
        return {
            "experiment_run_id": experiment_run_id,
            "status": "completed",
            "total_images": 0,
            "analyzed": 0,
            "skipped": 0,
            "errors": 0,
            "results": [],
        }
    
    # Initialize image analysis service
    image_analysis_service = ImageAnalysisService()
    
    # Process each image
    results = []
    analyzed_count = 0
    skipped_count = 0
    error_count = 0
    
    for image_file in image_files:
        # Extract campaign ID from filename
        campaign_id = _extract_campaign_id_from_filename(image_file.name)
        
        # Analyze and store
        result = analyze_and_store_image(
            image_path=image_file,
            campaign_id=campaign_id,
            experiment_run_id=experiment_run_id,
            image_analysis_service=image_analysis_service,
            db_engine=work_engine,
            skip_existing=skip_existing,
        )
        
        results.append(result)
        
        if result["status"] == "success":
            analyzed_count += 1
        elif result["status"] == "skipped":
            skipped_count += 1
        else:
            error_count += 1
    
    summary = {
        "experiment_run_id": experiment_run_id,
        "status": "completed",
        "total_images": len(image_files),
        "analyzed": analyzed_count,
        "skipped": skipped_count,
        "errors": error_count,
        "results": results,
    }
    
    logger.info(
        f"Bulk analysis complete: analyzed={analyzed_count}, skipped={skipped_count}, errors={error_count}"
    )
    
    return summary


def get_analysis_for_campaign(
    campaign_id: str,
    experiment_run_id: Optional[str] = None,
    db_engine: Optional[Engine] = None,
) -> List[Dict[str, any]]:
    """
    Retrieve stored analysis results for a specific campaign.
    
    Args:
        campaign_id: Campaign ID to retrieve analyses for
        experiment_run_id: Optional experiment run ID to filter by
        db_engine: Database engine (defaults to global engine)
        
    Returns:
        List of analysis results
    """
    work_engine = db_engine or engine
    
    query = """
        SELECT * FROM image_analysis_results 
        WHERE campaign_id = :campaign_id
    """
    params = {"campaign_id": campaign_id}
    
    if experiment_run_id:
        query += " AND experiment_run_id = :experiment_run_id"
        params["experiment_run_id"] = experiment_run_id
    
    query += " ORDER BY created_at DESC"
    
    with work_engine.begin() as connection:
        result = connection.execute(text(query), params)
        rows = [dict(row._mapping) for row in result]
    
    # Parse JSON fields
    for row in rows:
        if row.get("visual_elements"):
            try:
                row["visual_elements"] = json.loads(row["visual_elements"])
            except (json.JSONDecodeError, TypeError):
                pass
        if row.get("dominant_colors"):
            try:
                row["dominant_colors"] = json.loads(row["dominant_colors"])
            except (json.JSONDecodeError, TypeError):
                pass
        if row.get("feature_catalog"):
            try:
                row["feature_catalog"] = json.loads(row["feature_catalog"])
            except (json.JSONDecodeError, TypeError):
                pass
    
    return rows

