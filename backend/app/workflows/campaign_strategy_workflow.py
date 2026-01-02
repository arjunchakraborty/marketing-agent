"""Workflow for processing Klaviyo campaign data and analyzing images."""
from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.engine import Engine

from ..core.config import settings
from ..db.session import engine
from ..services.analytics_service import AnalyticsService
from ..services.bulk_image_analysis_service import get_analysis_for_campaign
from ..services.image_analysis_service import ImageAnalysisService
from ..services.intelligence_service import IntelligenceService
from ..services.prompt_sql_service import PromptToSqlService
from ..services.vector_db_service import VectorDBService

logger = logging.getLogger(__name__)


def _ensure_tables(db_engine: Engine) -> None:
    """Ensure all required tables exist."""
    from ..models.campaign_analysis import (
        CampaignAnalysis,
        EmailFeatureCatalog,
        ExperimentRun,
        ImageAnalysisResult,
        VisualElementCorrelation,
    )

    # Create tables
    CampaignAnalysis.__table__.create(db_engine, checkfirst=True)
    ImageAnalysisResult.__table__.create(db_engine, checkfirst=True)
    VisualElementCorrelation.__table__.create(db_engine, checkfirst=True)
    EmailFeatureCatalog.__table__.create(db_engine, checkfirst=True)
    ExperimentRun.__table__.create(db_engine, checkfirst=True)


def _convert_structured_analysis_to_expected_format(
    img_data: Dict[str, Any], campaign_id: str, img_idx: int
) -> Dict[str, Any]:
    """
    Convert structured analysis format (header, hero_image, etc.) to expected format
    (visual_elements, dominant_colors, composition_analysis, etc.).
    
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
    
    return {
        "image_id": img_data.get("image_id") or f"{campaign_id}_img_{img_idx}",
        "campaign_id": campaign_id,
        "visual_elements": visual_elements,
        "dominant_colors": dominant_colors,
        "composition_analysis": composition_analysis,
        "text_content": text_content,
        "overall_description": overall_description,
        "marketing_relevance": marketing_relevance,
        "email_features": [],  # Not available in structured format
        "feature_catalog": {},  # Not available in structured format
    }


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
    # This handles: www.klaviyo.com_campaign_01K4QVNYM1QKSK61X7PXR019DF_web-view.png
    # And: www.klaviyo.com_sms_campaign_01K77ZJ84N3C9EW4E3VDQXP320_webview_(iPhone 14 Pro Max).png
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


def run_campaign_strategy_experiment(
    sql_query: Optional[str] = None,
    prompt_query: Optional[str] = None,
    image_directory: Optional[str] = None,
    experiment_name: Optional[str] = None,
    db_engine: Optional[Engine] = None,
) -> Dict[str, any]:
    """
    Run the complete campaign strategy analysis workflow.
    
    Steps:
    1. Query impactful campaigns using SQL (generated from prompt or provided)
    2. Analyze images of those campaigns
    3. Cross-index visual elements with performance
    4. Store all results in database
    """
    work_engine = db_engine or engine
    logger.info("Ensuring database tables exist")
    _ensure_tables(work_engine)
    
    experiment_run_id = str(uuid.uuid4())
    logger.info(f"Starting campaign strategy experiment: experiment_run_id={experiment_run_id}, experiment_name={experiment_name}")
    logger.debug(f"Experiment parameters: has_sql_query={bool(sql_query)}, has_prompt_query={bool(prompt_query)}, image_directory={image_directory}")
    
    # Initialize services
    logger.debug("Initializing services")
    try:
        prompt_sql_service = PromptToSqlService()
        analytics_service = AnalyticsService(work_engine)
        image_analysis_service = ImageAnalysisService()
        intelligence_service = IntelligenceService()
        
        # Initialize vector DB service if enabled
        vector_db_service = None
        if settings.enable_vector_search:
            try:
                # Use default_collection as default (matches ingestion default)
                vector_db_service = VectorDBService(collection_name="default_collection")
                logger.info("Vector DB service initialized successfully")
            except Exception as e:
                logger.warning(f"Vector DB service not available: {str(e)}. Will fall back to image directory analysis.")
        else:
            logger.info("Vector search disabled, will use image directory analysis")
        
        logger.debug("Services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {type(e).__name__}: {str(e)}", exc_info=True)
        return {
            "error": f"Service initialization failed: {str(e)}",
            "experiment_run_id": experiment_run_id,
        }
    
    # Step 1: Generate or use SQL query to find impactful campaigns
    logger.info("Step 1: Generating/validating SQL query")
    if prompt_query and not sql_query:
        logger.info(f"Generating SQL from prompt query (length={len(prompt_query)})")
        try:
            sql_result = prompt_sql_service.generate_sql(prompt_query)
            sql_query = sql_result.get("sql", "")
            logger.info(f"Generated SQL query (length={len(sql_query)})")
            logger.debug(f"Generated SQL: {sql_query[:200]}...")
        except Exception as e:
            logger.error(f"SQL generation failed: {type(e).__name__}: {str(e)}", exc_info=True)
            return {
                "error": f"SQL generation failed: {str(e)}",
                "experiment_run_id": experiment_run_id,
            }
    
    if not sql_query:
        logger.info("Using default SQL query")
        # Default query to find top campaigns by performance
        sql_query = """
        SELECT campaign_id, campaign_name, open_rate, click_rate, conversion_rate, revenue
        FROM campaigns
        WHERE open_rate > 0.2 OR conversion_rate > 0.05
        ORDER BY conversion_rate DESC, revenue DESC
        """
    
    logger.debug(f"Executing SQL query: {sql_query[:200]}...")
    # Execute SQL query
    try:
        with work_engine.begin() as connection:
            result = connection.execute(text(sql_query))
            all_rows = [dict(row._mapping) for row in result]
        logger.info(f"SQL query executed successfully: found {len(all_rows)} campaigns")
    except Exception as e:
        logger.error(f"SQL query execution failed: {type(e).__name__}: {str(e)}, sql_query={sql_query[:200]}", exc_info=True)
        return {
            "error": f"SQL query execution failed: {str(e)}",
            "experiment_run_id": experiment_run_id,
            "sql_query": sql_query,
        }
    
    if not all_rows:
        logger.warning(f"No campaigns found matching query criteria: sql_query={sql_query[:200]}")
        return {
            "error": "No campaigns found matching query criteria",
            "experiment_run_id": experiment_run_id,
            "sql_query": sql_query,
        }
    
    # Limit to top 5 campaigns for analysis
    # Sort by performance metrics if available (conversion_rate, revenue, etc.)
    def get_sort_key(row):
        """Get sort key for ranking campaigns by performance."""
        # Prioritize conversion_rate, then revenue, then open_rate
        conversion_rate = row.get("conversion_rate") or 0
        revenue = row.get("revenue") or 0
        open_rate = row.get("open_rate") or 0
        # Return tuple for multi-level sorting
        return (conversion_rate, revenue, open_rate)
    
    # Sort rows by performance (descending)
    sorted_rows = sorted(all_rows, key=get_sort_key, reverse=True)
    rows = sorted_rows[:5]  # Take top 5 campaigns
    logger.info(f"Limited to top {len(rows)} campaigns out of {len(all_rows)} total campaigns found")
    
    # Step 2: Generate LLM summary of query results
    logger.info("Step 2: Generating LLM summary of query results")
    query_summary = None
    try:
        # Prepare signals from query results
        signals = []
        if rows:
            # Helper function to parse numeric values (handles percentages and strings)
            def parse_numeric(value):
                if value is None:
                    return 0.0
                if isinstance(value, (int, float)):
                    return float(value)
                if isinstance(value, str):
                    # Remove % and commas, then parse
                    cleaned = value.replace("%", "").replace(",", "").strip()
                    try:
                        return float(cleaned)
                    except ValueError:
                        return 0.0
                return 0.0
            
            # Extract key metrics as signals
            conversion_rates = [parse_numeric(r.get("conversion_rate")) for r in rows]
            open_rates = [parse_numeric(r.get("open_rate")) for r in rows]
            revenues = [parse_numeric(r.get("revenue")) for r in rows]
            
            avg_conversion = sum(conversion_rates) / len(rows) if conversion_rates else 0
            avg_open_rate = sum(open_rates) / len(rows) if open_rates else 0
            total_revenue = sum(revenues)
            
            signals.append(f"Found {len(rows)} top-performing campaigns")
            if avg_conversion > 0:
                signals.append(f"Average conversion rate: {avg_conversion:.2%}" if avg_conversion < 1 else f"Average conversion rate: {avg_conversion:.2f}%")
            else:
                signals.append("Conversion rate data available")
            
            if avg_open_rate > 0:
                signals.append(f"Average open rate: {avg_open_rate:.2%}" if avg_open_rate < 1 else f"Average open rate: {avg_open_rate:.2f}%")
            else:
                signals.append("Open rate data available")
            
            if total_revenue > 0:
                signals.append(f"Total revenue: ${total_revenue:,.2f}")
            else:
                signals.append("Revenue data available")
            
            # Add campaign names
            campaign_names = [r.get("campaign_name", "Unknown") for r in rows[:3]]
            if campaign_names:
                signals.append(f"Top campaigns: {', '.join(campaign_names)}")
        
        # Prepare context with query details and results
        context = {
            "sql_query": sql_query,
            "total_campaigns_found": len(all_rows),
            "top_campaigns_analyzed": len(rows),
            "query_results": rows[:10],  # Include first 10 for context
            "experiment_name": experiment_name,
        }
        
        # Generate summary using intelligence service
        query_summary = intelligence_service.summarize_insights(signals, context)
        logger.info(f"Generated query summary (length: {len(query_summary)} chars)")
        logger.debug(f"Query summary: {query_summary[:200]}...")
    except Exception as e:
        logger.warning(f"Failed to generate query summary: {type(e).__name__}: {str(e)}", exc_info=True)
        query_summary = f"Summary generation failed: {str(e)}"
    
    # Step 3: Store campaign analysis results (top 5 campaigns only)
    logger.info(f"Step 3: Storing campaign analysis results for top {len(rows)} campaigns")
    campaign_ids = []
    products_promoted = []
    
    stored_count = 0
    for idx, row in enumerate(rows):
        try:
            campaign_id = row.get("campaign_id") or row.get("id")
            campaign_name = row.get("campaign_name") or row.get("name", "Unknown")
            
            if campaign_id:
                campaign_ids.append(str(campaign_id))
            
            # Extract products if available
            if "products" in row:
                products = row["products"]
                if isinstance(products, str):
                    try:
                        products = json.loads(products)
                    except json.JSONDecodeError:
                        logger.debug(f"Failed to parse products JSON for campaign {campaign_id}, treating as string")
                        products = [products]
                if isinstance(products, list):
                    products_promoted.extend(products)
            
            # Store campaign analysis
            with work_engine.begin() as connection:
                connection.execute(
                    text("""
                        INSERT INTO campaign_analysis 
                        (experiment_run_id, campaign_id, campaign_name, sql_query, query_results, metrics)
                        VALUES (:experiment_run_id, :campaign_id, :campaign_name, :sql_query, :query_results, :metrics)
                    """),
                    {
                        "experiment_run_id": experiment_run_id,
                        "campaign_id": str(campaign_id) if campaign_id else None,
                        "campaign_name": campaign_name,
                        "sql_query": sql_query,
                        "query_results": json.dumps(row),
                        "metrics": json.dumps({
                            "open_rate": row.get("open_rate"),
                            "click_rate": row.get("click_rate"),
                            "conversion_rate": row.get("conversion_rate"),
                            "revenue": row.get("revenue"),
                        }),
                    }
                )
            stored_count += 1
        except Exception as e:
            logger.error(f"Failed to store campaign analysis for row {idx}: {type(e).__name__}: {str(e)}", exc_info=True)
            continue
    
    logger.info(f"Stored {stored_count}/{len(rows)} campaign analyses. Found {len(campaign_ids)} unique campaign IDs")
    
    # Step 4: Retrieve campaign analyses from vector database or analyze images
    logger.info(f"Step 4: Retrieving campaign analyses for top {len(rows)} campaigns")
    image_analyses = []
    visual_elements_list = []
    
    # Try to retrieve from vector DB first if enabled
    if vector_db_service and campaign_ids:
        logger.info(f"Attempting to retrieve {len(campaign_ids)} campaigns from vector database")
        vector_db_results = {}
        retrieved_count = 0
        
        for campaign_id in campaign_ids:
            try:
                analysis_data = vector_db_service.get_campaign_analysis(str(campaign_id))
                if analysis_data:
                    vector_db_results[campaign_id] = analysis_data
                    retrieved_count += 1
                    logger.debug(f"Retrieved campaign {campaign_id} from vector DB")
            except Exception as e:
                logger.warning(f"Failed to retrieve campaign {campaign_id} from vector DB: {str(e)}")
                continue
        
        logger.info(f"Retrieved {retrieved_count}/{len(campaign_ids)} campaigns from vector database")
        
        # Process vector DB results
        if vector_db_results:
            logger.info("Processing vector DB results to extract image analyses")
            for campaign_id, analysis_data in vector_db_results.items():
                # Extract image analyses from vector DB data
                logger.info(analysis_data)
                images = analysis_data.get("images", [])
                campaign_name = analysis_data.get("campaign_name", "Unknown")
                
                for img_idx, img_data in enumerate(images):
                    # Handle both old format (direct image data) and new format (nested analysis)
                    analysis = img_data.get("analysis", {}) if "analysis" in img_data else img_data
                    
                    # Check if this is the structured format (has header, hero_image, etc.)
                    # vs the expected format (has visual_elements, dominant_colors, etc.)
                    is_structured_format = (
                        "header" in analysis or 
                        "hero_image" in analysis or 
                        "call_to_action_button" in analysis or
                        "product_images" in analysis
                    )
                    
                    if is_structured_format:
                        # Convert structured format to expected format
                        image_analysis_result = _convert_structured_analysis_to_expected_format(
                            img_data, campaign_id, img_idx
                        )
                    else:
                        # Already in expected format
                        image_analysis_result = {
                            "image_id": analysis.get("image_id") or f"{campaign_id}_img_{img_idx}",
                            "campaign_id": campaign_id,
                            "visual_elements": analysis.get("visual_elements", []),
                            "dominant_colors": analysis.get("dominant_colors", []),
                            "composition_analysis": analysis.get("composition_analysis"),
                            "text_content": analysis.get("text_content"),
                            "overall_description": analysis.get("overall_description"),
                            "marketing_relevance": analysis.get("marketing_relevance"),
                            "email_features": analysis.get("email_features", []),
                            "feature_catalog": analysis.get("feature_catalog", {}),
                        }
                    
                    # Ensure image_path is set
                    if "image_path" not in image_analysis_result:
                        image_analysis_result["image_path"] = img_data.get("image_path") or f"vector_db_{campaign_id}_{img_idx}"
                    
                    image_analyses.append(image_analysis_result)
                    
                    # Extract visual elements for correlation
                    for element in image_analysis_result.get("visual_elements", []):
                        visual_elements_list.append({
                            "element_type": element.get("element_type", "unknown"),
                            "description": element.get("description", ""),
                            "campaign_id": campaign_id,
                        })
                    
                    # Store image analysis result in database
                    try:
                        with work_engine.begin() as connection:
                            connection.execute(
                                text("""
                                    INSERT INTO image_analysis_results
                                    (experiment_run_id, campaign_id, image_id, image_path, visual_elements, 
                                     dominant_colors, composition_analysis, text_content, overall_description, 
                                     marketing_relevance, feature_catalog)
                                    VALUES (:experiment_run_id, :campaign_id, :image_id, :image_path, :visual_elements,
                                            :dominant_colors, :composition_analysis, :text_content, :overall_description, 
                                            :marketing_relevance, :feature_catalog)
                                """),
                                {
                                    "experiment_run_id": experiment_run_id,
                                    "campaign_id": campaign_id,
                                    "image_id": image_analysis_result.get("image_id"),
                                    "image_path": analysis.get("image_path") or f"vector_db_{campaign_id}_{img_idx}",
                                    "visual_elements": json.dumps(image_analysis_result.get("visual_elements", [])),
                                    "dominant_colors": json.dumps(image_analysis_result.get("dominant_colors", [])),
                                    "composition_analysis": image_analysis_result.get("composition_analysis"),
                                    "text_content": image_analysis_result.get("text_content"),
                                    "overall_description": image_analysis_result.get("overall_description"),
                                    "marketing_relevance": image_analysis_result.get("marketing_relevance"),
                                    "feature_catalog": json.dumps(image_analysis_result.get("feature_catalog", {})) if image_analysis_result.get("feature_catalog") else None,
                                }
                            )
                            
                            # Store individual features in email_feature_catalog table
                            email_features = image_analysis_result.get("email_features", [])
                            if email_features:
                                for feature in email_features:
                                    try:
                                        feature_category = feature.get("feature_category", "content")
                                        feature_type = feature.get("feature_type", "unknown")
                                        bbox = feature.get("bbox")
                                        confidence = feature.get("confidence", 0.0)
                                        position = feature.get("position")
                                        
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
                    except Exception as e:
                        logger.error(f"Failed to store image analysis result: {str(e)}", exc_info=True)
                        continue
            
            logger.info(f"Processed {len(image_analyses)} image analyses from vector database")
    
    # Fallback to image directory analysis if vector DB not available or no results found
    if not image_analyses and image_directory:
        logger.info(f"Falling back to image directory analysis: {image_directory}")
        image_dir = Path(image_directory)
        if not image_dir.exists():
            logger.warning(f"Image directory does not exist: {image_directory}")
        else:
            # First, try to load existing analyses from database
            logger.info("Checking for existing image analyses in database...")
            existing_analyses = {}
            for campaign_id in campaign_ids:
                stored_analyses = get_analysis_for_campaign(campaign_id, db_engine=work_engine)
                if stored_analyses:
                    existing_analyses[campaign_id] = stored_analyses
                    logger.info(f"Found {len(stored_analyses)} stored analyses for campaign {campaign_id}")
            
            # Find images matching campaign IDs (only for top 5 campaigns)
            image_files = list(image_dir.glob("*.jpg")) + list(image_dir.glob("*.png")) + list(image_dir.glob("*.jpeg"))
            logger.info(f"Found {len(image_files)} image files in directory, filtering for top {len(rows)} campaigns")
            
            analyzed_count = 0
            matched_count = 0
            reused_count = 0
            for image_file in image_files:
                try:
                    campaign_id_from_file = _extract_campaign_id_from_filename(image_file.name)
                    logger.debug(f"Processing image: {image_file.name}, extracted_campaign_id={campaign_id_from_file}")
                    
                    # Match image to campaign if ID found
                    matched_campaign_id = None
                    if campaign_id_from_file:
                        # Try exact match first
                        if campaign_id_from_file in campaign_ids:
                            matched_campaign_id = campaign_id_from_file
                            matched_count += 1
                            logger.debug(f"Matched image {image_file.name} to campaign {matched_campaign_id} (exact match)")
                        else:
                            # Try partial match
                            for cid in campaign_ids:
                                if campaign_id_from_file in str(cid) or str(cid) in campaign_id_from_file:
                                    matched_campaign_id = cid
                                    matched_count += 1
                                    logger.debug(f"Matched image {image_file.name} to campaign {matched_campaign_id} (partial match)")
                                    break
                    
                    if not matched_campaign_id:
                        logger.debug(f"No campaign match found for image {image_file.name}, analyzing anyway")
                    
                    # Check if we have stored analysis for this campaign/image
                    analysis_result = None
                    if matched_campaign_id and matched_campaign_id in existing_analyses:
                        # Try to find analysis for this specific image path
                        for stored_analysis in existing_analyses[matched_campaign_id]:
                            if stored_analysis.get("image_path") == str(image_file):
                                logger.info(f"Reusing stored analysis for {image_file.name}")
                                # Convert stored analysis to expected format
                                analysis_result = {
                                    "image_id": stored_analysis.get("image_id"),
                                    "campaign_id": matched_campaign_id,
                                    "visual_elements": stored_analysis.get("visual_elements", []),
                                    "dominant_colors": stored_analysis.get("dominant_colors", []),
                                    "composition_analysis": stored_analysis.get("composition_analysis"),
                                    "text_content": stored_analysis.get("text_content"),
                                    "overall_description": stored_analysis.get("overall_description"),
                                    "marketing_relevance": stored_analysis.get("marketing_relevance"),
                                    "email_features": [],  # Will be loaded from feature_catalog if needed
                                    "feature_catalog": stored_analysis.get("feature_catalog", {}),
                                }
                                reused_count += 1
                                break
                    
                    # If no stored analysis found, analyze now
                    if not analysis_result:
                        logger.debug(f"Analyzing image: {image_file.name} (size: {image_file.stat().st_size} bytes)")
                        with open(image_file, "rb") as f:
                            import base64
                            image_data = base64.b64encode(f.read()).decode("utf-8")
                        
                        analysis_result = image_analysis_service.analyze_image(
                            image_base64=image_data,
                            campaign_id=matched_campaign_id,
                            campaign_name=None,
                            analysis_type="full",
                        )
                        analyzed_count += 1
                    
                    image_analyses.append(analysis_result)
                    
                    # Extract visual elements for correlation
                    elements_found = len(analysis_result.get("visual_elements", []))
                    for element in analysis_result.get("visual_elements", []):
                        visual_elements_list.append({
                            "element_type": element.get("element_type", "unknown"),
                            "description": element.get("description", ""),
                            "campaign_id": matched_campaign_id,
                        })
                    
                    logger.debug(f"Image analysis complete: {image_file.name}, elements={elements_found}, colors={len(analysis_result.get('dominant_colors', []))}")
                    
                    # Extract email features for cataloging
                    email_features = analysis_result.get("email_features", [])
                    feature_catalog = analysis_result.get("feature_catalog", {})
                    
                    # Store image analysis result
                    with work_engine.begin() as connection:
                        connection.execute(
                            text("""
                                INSERT INTO image_analysis_results
                                (experiment_run_id, campaign_id, image_id, image_path, visual_elements, 
                                 dominant_colors, composition_analysis, text_content, overall_description, 
                                 marketing_relevance, feature_catalog)
                                VALUES (:experiment_run_id, :campaign_id, :image_id, :image_path, :visual_elements,
                                        :dominant_colors, :composition_analysis, :text_content, :overall_description, 
                                        :marketing_relevance, :feature_catalog)
                            """),
                            {
                                "experiment_run_id": experiment_run_id,
                                "campaign_id": matched_campaign_id,
                                "image_id": analysis_result.get("image_id"),
                                "image_path": str(image_file),
                                "visual_elements": json.dumps(analysis_result.get("visual_elements", [])),
                                "dominant_colors": json.dumps(analysis_result.get("dominant_colors", [])),
                                "composition_analysis": analysis_result.get("composition_analysis"),
                                "text_content": analysis_result.get("text_content"),
                                "overall_description": analysis_result.get("overall_description"),
                                "marketing_relevance": analysis_result.get("marketing_relevance"),
                                "feature_catalog": json.dumps(feature_catalog) if feature_catalog else None,
                            }
                        )
                        
                        # Store individual features in email_feature_catalog table
                        if email_features and matched_campaign_id:
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
                                            "campaign_id": matched_campaign_id,
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
                except Exception as e:
                    logger.error(f"Failed to analyze image {image_file}: {type(e).__name__}: {str(e)}", exc_info=True)
                    continue
            
            logger.info(f"Image analysis complete: analyzed {analyzed_count} new, reused {reused_count} stored, matched {matched_count} to campaigns, found {len(visual_elements_list)} visual elements")
    elif not image_analyses:
        logger.info("No vector DB results and no image directory provided, skipping image analysis")
    
    # Step 5: Cross-index visual elements with performance
    logger.info(f"Step 5: Cross-indexing visual elements with performance (found {len(visual_elements_list)} elements)")
    correlation_count = 0
    if visual_elements_list:
        # Group elements by type
        element_types = {}
        for elem in visual_elements_list:
            elem_type = elem["element_type"]
            if elem_type not in element_types:
                element_types[elem_type] = []
            element_types[elem_type].append(elem)
        
        logger.debug(f"Grouped visual elements into {len(element_types)} types: {list(element_types.keys())}")
        
        # Correlate with performance
        for elem_type, elements in element_types.items():
            logger.debug(f"Correlating element type '{elem_type}' with {len(elements)} instances")
            try:
                correlation_result = image_analysis_service.correlate_visual_elements_with_performance(
                    visual_elements=[elem["description"] for elem in elements],
                    date_range=None,
                    min_campaigns=1,
                )
                
                correlations_found = len(correlation_result.get("correlations", []))
                logger.debug(f"Found {correlations_found} correlations for element type '{elem_type}'")
                
                for corr in correlation_result.get("correlations", []):
                    try:
                        with work_engine.begin() as connection:
                            connection.execute(
                                text("""
                                    INSERT INTO visual_element_correlations
                                    (experiment_run_id, element_type, element_description, average_performance,
                                     performance_impact, recommendation, campaign_count)
                                    VALUES (:experiment_run_id, :element_type, :element_description, :average_performance,
                                            :performance_impact, :recommendation, :campaign_count)
                                """),
                                {
                                    "experiment_run_id": experiment_run_id,
                                    "element_type": corr.get("element_type", elem_type),
                                    "element_description": corr.get("element_description", ""),
                                    "average_performance": json.dumps(corr.get("average_performance", {})),
                                    "performance_impact": corr.get("performance_impact", ""),
                                    "recommendation": corr.get("recommendation", ""),
                                    "campaign_count": len(elements),
                                }
                            )
                        correlation_count += 1
                    except Exception as e:
                        logger.error(f"Failed to store correlation for element type '{elem_type}': {type(e).__name__}: {str(e)}", exc_info=True)
                        continue
            except Exception as e:
                logger.error(f"Failed to correlate element type '{elem_type}': {type(e).__name__}: {str(e)}", exc_info=True)
                continue
        
        logger.info(f"Stored {correlation_count} visual element correlations")
    else:
        logger.info("No visual elements found, skipping correlation step")
    
    # Store experiment run
    logger.info(f"Step 6: Storing experiment run metadata")
    try:
        results_summary = {
            "campaigns_analyzed": len(rows),
            "images_analyzed": len(image_analyses),
            "visual_elements_found": len(visual_elements_list),
            "campaign_ids": campaign_ids[:10],  # First 10
            "products_promoted": list(set(products_promoted))[:10],
            "query_summary": query_summary,  # Include LLM-generated summary
        }
        
        with work_engine.begin() as connection:
            connection.execute(
                text("""
                    INSERT INTO experiment_runs
                    (experiment_run_id, name, description, sql_query, status, config, results_summary, completed_at)
                    VALUES (:experiment_run_id, :name, :description, :sql_query, :status, :config, :results_summary, :completed_at)
                """),
            {
                "experiment_run_id": experiment_run_id,
                "name": experiment_name or f"Campaign Strategy Analysis {experiment_run_id[:8]}",
                "description": f"Analyzed top {len(rows)} campaigns, {len(image_analyses)} images",
                "sql_query": sql_query,
                "status": "completed",
                "config": json.dumps({
                    "prompt_query": prompt_query,
                    "image_directory": image_directory,
                }),
                "results_summary": json.dumps(results_summary),
                "completed_at": datetime.utcnow().isoformat(),
            }
        )
        logger.info(f"Experiment run stored successfully: experiment_run_id={experiment_run_id}")
    except Exception as e:
        logger.error(f"Failed to store experiment run metadata: {type(e).__name__}: {str(e)}", exc_info=True)
        # Continue anyway - we still want to return results
    
    logger.info(f"Experiment completed successfully: experiment_run_id={experiment_run_id}, campaigns={len(rows)}, images={len(image_analyses)}, elements={len(visual_elements_list)}, correlations={correlation_count}")
    
    return {
        "experiment_run_id": experiment_run_id,
        "status": "completed",
        "campaigns_analyzed": len(rows),
        "images_analyzed": len(image_analyses),
        "visual_elements_found": len(visual_elements_list),
        "campaign_ids": campaign_ids,
        "products_promoted": list(set(products_promoted)),
        "query_summary": query_summary,  # Include LLM-generated summary
        "query_results": rows,  # Include the actual query results
    }

