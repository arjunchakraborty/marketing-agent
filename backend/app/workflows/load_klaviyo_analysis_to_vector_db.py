"""Workflow to load Klaviyo analysis JSON into vector database."""
from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from ..services.vector_db_service import VectorDBService

logger = logging.getLogger(__name__)


def load_campaigns_from_csv(csv_file_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Load campaign data from CSV file.
    
    Args:
        csv_file_path: Path to email_campaigns.csv file
        
    Returns:
        Dictionary mapping campaign_id to campaign data
    """
    csv_path = Path(csv_file_path)
    
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
    
    logger.info(f"Loading campaign data from CSV: {csv_file_path}")
    
    campaigns = {}
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            campaign_id = row.get("Campaign ID", "").strip()
            if not campaign_id:
                continue
            
            # Convert CSV row to dictionary, cleaning up values
            campaign_data = {
                "campaign_id": campaign_id,
                "campaign_name": row.get("Campaign Name", "").strip(),
                "subject": row.get("Subject", "").strip(),
                "tags": row.get("Tags", "").strip(),
                "list": row.get("List", "").strip(),
                "send_time": row.get("Send Time", "").strip(),
                "send_weekday": row.get("Send Weekday", "").strip(),
                "campaign_channel": row.get("Campaign Channel", "").strip(),
                # Performance metrics
                "total_recipients": _parse_numeric(row.get("Total Recipients", "0")),
                "unique_placed_order": _parse_numeric(row.get("Unique Placed Order", "0")),
                "placed_order_rate": row.get("Placed Order Rate", "0%").strip(),
                "revenue": _parse_numeric(row.get("Revenue", "0")),
                "unique_opens": _parse_numeric(row.get("Unique Opens", "0")),
                "open_rate": row.get("Open Rate", "0%").strip(),
                "total_opens": _parse_numeric(row.get("Total Opens", "0")),
                "unique_clicks": _parse_numeric(row.get("Unique Clicks", "0")),
                "click_rate": row.get("Click Rate", "0%").strip(),
                "total_clicks": _parse_numeric(row.get("Total Clicks", "0")),
                "unsubscribes": _parse_numeric(row.get("Unsubscribes", "0")),
                "spam_complaints": _parse_numeric(row.get("Spam Complaints", "0")),
                "spam_complaints_rate": row.get("Spam Complaints Rate", "0%").strip(),
                "successful_deliveries": _parse_numeric(row.get("Successful Deliveries", "0")),
                "bounces": _parse_numeric(row.get("Bounces", "0")),
                "bounce_rate": row.get("Bounce Rate", "0%").strip(),
            }
            
            campaigns[campaign_id] = campaign_data
    
    logger.info(f"Loaded {len(campaigns)} campaigns from CSV")
    return campaigns


def _parse_numeric(value: str) -> float:
    """Parse numeric value from CSV, handling empty strings and percentages."""
    if not value or value.strip() == "":
        return 0.0
    try:
        # Remove commas and convert to float
        return float(value.replace(",", "").strip())
    except (ValueError, AttributeError):
        return 0.0


def _convert_structured_analysis_to_expected_format(
    img_data: Dict[str, Any], campaign_id: str, img_idx: int
) -> Dict[str, Any]:
    """
    Convert structured analysis format (header, hero_image, etc.) to expected format
    (visual_elements, dominant_colors, composition_analysis, etc.).
    
    This is the same function from campaign_strategy_workflow.py, duplicated here
    to avoid circular imports.
    
    Args:
        img_data: Image data from vector DB with structured analysis
        campaign_id: Campaign ID
        img_idx: Image index
        
    Returns:
        Converted image analysis result in expected format
    """
    analysis = img_data.get("analysis", {})
    
    # Extract visual elements from structured format
    visual_elements = []
    
    # From header
    if "header" in analysis:
        header = analysis["header"]
        if "logo" in header:
            logo = header["logo"]
            visual_elements.append({
                "element_type": "logo",
                "description": f"Logo: {logo.get('text', '')} - {logo.get('tagline', '')}",
                "position": logo.get("position", ""),
                "color": logo.get("color", ""),
            })
        if "navigation" in header:
            nav = header["navigation"]
            visual_elements.append({
                "element_type": "navigation",
                "description": f"Navigation: {', '.join(nav.get('items', []))}",
                "layout": nav.get("layout", ""),
                "color_scheme": nav.get("color_scheme", ""),
            })
    
    # From hero_image
    if "hero_image" in analysis:
        hero = analysis["hero_image"]
        visual_elements.append({
            "element_type": "hero_image",
            "description": hero.get("description", ""),
            "elements": hero.get("elements", []),
            "color_scheme": hero.get("color_scheme", ""),
            "composition": hero.get("composition", ""),
        })
    
    # From call_to_action_button
    if "call_to_action_button" in analysis:
        cta = analysis["call_to_action_button"]
        visual_elements.append({
            "element_type": "cta_button",
            "description": f"CTA: {cta.get('text', '')}",
            "color": cta.get("color", ""),
            "position": cta.get("position", ""),
            "design": cta.get("design", ""),
        })
    
    # From product_images
    if "product_images" in analysis:
        for prod_img in analysis["product_images"]:
            visual_elements.append({
                "element_type": "product_image",
                "description": prod_img.get("description", ""),
                "elements": prod_img.get("elements", []),
                "color_scheme": prod_img.get("color_scheme", ""),
                "composition": prod_img.get("composition", ""),
            })
    
    # Extract dominant colors from background
    dominant_colors = []
    if "background" in analysis:
        bg = analysis["background"]
        if bg.get("main_color"):
            dominant_colors.append({
                "color": bg["main_color"],
                "type": "background",
            })
        if bg.get("accent_color"):
            dominant_colors.append({
                "color": bg["accent_color"],
                "type": "accent",
            })
    
    # Build composition analysis from layout_structure
    composition_analysis = None
    if "layout_structure" in analysis:
        composition_analysis = "\n".join(analysis["layout_structure"])
    
    # Build overall description from design_tone and key elements
    overall_description_parts = []
    if "design_tone" in analysis:
        overall_description_parts.append(f"Design tone: {analysis['design_tone']}")
    if "hero_image" in analysis and analysis["hero_image"].get("description"):
        overall_description_parts.append(f"Hero: {analysis['hero_image']['description']}")
    overall_description = " | ".join(overall_description_parts) if overall_description_parts else None
    
    # Extract text content
    text_content_parts = []
    if "header" in analysis and "logo" in analysis["header"]:
        logo = analysis["header"]["logo"]
        if logo.get("text"):
            text_content_parts.append(f"Logo: {logo['text']}")
        if logo.get("tagline"):
            text_content_parts.append(f"Tagline: {logo['tagline']}")
    if "call_to_action_button" in analysis:
        cta_text = analysis["call_to_action_button"].get("text", "")
        if cta_text:
            text_content_parts.append(f"CTA: {cta_text}")
    text_content = "\n".join(text_content_parts) if text_content_parts else None
    
    # Build marketing relevance from design_tone
    marketing_relevance = analysis.get("design_tone", "")
    
    # Preserve original structured analysis and add converted fields
    converted = {
        "image_id": img_data.get("image_id") or f"{campaign_id}_img_{img_idx}",
        "campaign_id": campaign_id,
        "image_name": img_data.get("image_name", ""),
        "image_path": img_data.get("image_path", ""),
        "visual_elements": visual_elements,
        "dominant_colors": dominant_colors,
        "composition_analysis": composition_analysis,
        "text_content": text_content,
        "overall_description": overall_description,
        "marketing_relevance": marketing_relevance,
        "email_features": [],  # Not available in structured format
        "feature_catalog": {},  # Not available in structured format
        # Keep original structured analysis for reference
        "original_analysis": analysis,
        "metadata": img_data.get("metadata", {}),
    }
    
    return converted


def load_image_analyses_from_folder(folder_path: str, convert_format: bool = True) -> Dict[str, List[Dict[str, Any]]]:
    """
    Load image analysis JSON files from folder and optionally convert to expected format.
    
    Args:
        folder_path: Path to image-analysis-extract folder
        convert_format: If True, convert structured format to expected format
        
    Returns:
        Dictionary mapping campaign_id to list of image analyses
    """
    folder = Path(folder_path)
    
    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {folder_path}")
    
    logger.info(f"Loading image analyses from folder: {folder_path}")
    
    # Find all JSON files
    json_files = list(folder.glob("*.json"))
    logger.info(f"Found {len(json_files)} JSON files")
    
    # Group by campaign_id
    analyses_by_campaign: Dict[str, List[Dict[str, Any]]] = {}
    converted_count = 0
    
    for json_file in json_files:
        try:
            with open(json_file, "r") as f:
                data = json.load(f)
            
            campaign_id = data.get("campaign_id", "").strip()
            if not campaign_id:
                # Try to extract from filename
                campaign_id = json_file.stem
            
            if campaign_id not in analyses_by_campaign:
                analyses_by_campaign[campaign_id] = []
            
            # Convert format if requested and if it's structured format
            if convert_format:
                analysis = data.get("analysis", {})
                is_structured_format = (
                    "header" in analysis or 
                    "hero_image" in analysis or 
                    "call_to_action_button" in analysis or
                    "product_images" in analysis
                )
                
                if is_structured_format:
                    converted_data = _convert_structured_analysis_to_expected_format(
                        data, campaign_id, len(analyses_by_campaign[campaign_id])
                    )
                    analyses_by_campaign[campaign_id].append(converted_data)
                    converted_count += 1
                else:
                    # Already in expected format
                    analyses_by_campaign[campaign_id].append(data)
            else:
                # Keep original format
                analyses_by_campaign[campaign_id].append(data)
            
        except Exception as e:
            logger.warning(f"Failed to load JSON file {json_file.name}: {str(e)}")
            continue
    
    logger.info(f"Loaded image analyses for {len(analyses_by_campaign)} campaigns")
    if convert_format:
        logger.info(f"Converted {converted_count} image analyses from structured format")
    return analyses_by_campaign


def load_klaviyo_analysis_to_vector_db(
    csv_file_path: str,
    image_analysis_folder: str,
    collection_name: str = "klaviyo_campaigns",
    overwrite_existing: bool = False,
) -> Dict[str, Any]:
    """
    Load Klaviyo campaign data from CSV and image analyses from JSON files into vector database.
    
    Args:
        csv_file_path: Path to email_campaigns.csv file
        image_analysis_folder: Path to image-analysis-extract folder containing JSON files
        collection_name: Name of the vector database collection
        overwrite_existing: If True, overwrite existing campaigns
        
    Returns:
        Dictionary with loading statistics
    """
    # Load campaign data from CSV
    campaigns = load_campaigns_from_csv(csv_file_path)
    
    # Load image analyses from JSON files
    image_analyses = load_image_analyses_from_folder(image_analysis_folder)
    
    # Initialize vector database service
    try:
        vector_db = VectorDBService(collection_name=collection_name)
    except RuntimeError as e:
        logger.error(f"Failed to initialize vector database: {str(e)}")
        raise
    
    # Statistics
    loaded_count = 0
    skipped_count = 0
    error_count = 0
    errors = []
    campaigns_with_images = 0
    campaigns_without_images = 0
    
    # Combine CSV data with image analyses and load into vector DB
    for campaign_id, campaign_data in campaigns.items():
        try:
            # Check if campaign already exists
            existing = vector_db.get_campaign_analysis(campaign_id)
            if existing and not overwrite_existing:
                logger.debug(f"Skipping existing campaign: {campaign_id}")
                skipped_count += 1
                continue
            
            # Get image analyses for this campaign
            image_analysis_list = image_analyses.get(campaign_id, [])
            
            # Combine campaign data with image analyses
            combined_data = {
                **campaign_data,
                "images": image_analysis_list,
                "total_image_analyses": len(image_analysis_list),
            }
            
            if image_analysis_list:
                campaigns_with_images += 1
            else:
                campaigns_without_images += 1
            
            # Prepare metadata
            metadata = {
                "campaign_name": campaign_data.get("campaign_name", ""),
                "subject": campaign_data.get("subject", ""),
                "open_rate": campaign_data.get("open_rate", ""),
                "click_rate": campaign_data.get("click_rate", ""),
                "revenue": campaign_data.get("revenue", 0.0),
                "total_image_analyses": len(image_analysis_list),
                "has_image_analysis": len(image_analysis_list) > 0,
            }
            
            # Add to vector database
            vector_db.add_campaign_analysis(
                campaign_id=campaign_id,
                analysis_data=combined_data,
                metadata=metadata,
            )
            
            loaded_count += 1
            logger.info(
                f"Loaded campaign {campaign_id} ({loaded_count}/{len(campaigns)}) - "
                f"{len(image_analysis_list)} image analyses"
            )
            
        except Exception as e:
            error_count += 1
            error_msg = f"Failed to load campaign {campaign_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            errors.append({"campaign_id": campaign_id, "error": str(e)})
    
    summary = {
        "status": "completed",
        "total_campaigns": len(campaigns),
        "loaded": loaded_count,
        "skipped": skipped_count,
        "errors": error_count,
        "campaigns_with_images": campaigns_with_images,
        "campaigns_without_images": campaigns_without_images,
        "error_details": errors,
        "collection_name": collection_name,
        "vector_db_path": str(vector_db.vector_db_path),
    }
    
    logger.info(
        f"Loading complete: loaded={loaded_count}, skipped={skipped_count}, "
        f"errors={error_count}, with_images={campaigns_with_images}, "
        f"without_images={campaigns_without_images}"
    )
    
    return summary


def search_campaigns_by_similarity(
    query_text: str,
    n_results: int = 5,
    collection_name: str = "klaviyo_campaigns",
) -> Dict[str, Any]:
    """
    Search for campaigns similar to the query text.
    
    Args:
        query_text: Text query (e.g., "bright colorful campaigns", "dark themed emails")
        n_results: Number of results to return
        collection_name: Name of the vector database collection
        
    Returns:
        Dictionary with search results
    """
    vector_db = VectorDBService(collection_name=collection_name)
    
    results = vector_db.search_similar_campaigns(
        query_text=query_text,
        n_results=n_results,
    )
    
    return {
        "query": query_text,
        "results": results,
        "total_found": len(results),
    }

