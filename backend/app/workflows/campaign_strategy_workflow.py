"""Workflow for processing Klaviyo campaign data and analyzing images."""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.engine import Engine

from ..core.config import settings
from ..db.session import engine
from ..services.analytics_service import AnalyticsService
from ..services.image_analysis_service import ImageAnalysisService
from ..services.prompt_sql_service import PromptToSqlService


def _ensure_tables(db_engine: Engine) -> None:
    """Ensure all required tables exist."""
    from ..models.campaign_analysis import (
        CampaignAnalysis,
        ExperimentRun,
        ImageAnalysisResult,
        VisualElementCorrelation,
    )

    # Create tables
    CampaignAnalysis.__table__.create(db_engine, checkfirst=True)
    ImageAnalysisResult.__table__.create(db_engine, checkfirst=True)
    VisualElementCorrelation.__table__.create(db_engine, checkfirst=True)
    ExperimentRun.__table__.create(db_engine, checkfirst=True)


def _extract_campaign_id_from_filename(filename: str) -> Optional[str]:
    """Extract campaign ID from image filename."""
    # Pattern: www.klaviyo.com_campaign_01K4QVNYM1QKSK61X7PXR019DF_web-view.png
    # Or: campaign_01K4QVNYM1QKSK61X7PXR019DF.jpg
    patterns = [
        r"campaign_([A-Z0-9]+)",  # campaign_01K4QVNYM1QKSK61X7PXR019DF
        r"_campaign_([A-Z0-9]+)",  # _campaign_01K4QVNYM1QKSK61X7PXR019DF
        r"([A-Z0-9]{26,})",  # Generic long ID (Klaviyo IDs are typically 26 chars)
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename, re.IGNORECASE)
        if match:
            return match.group(1)
    
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
    _ensure_tables(work_engine)
    
    experiment_run_id = str(uuid.uuid4())
    print(f"[CAMPAIGN_STRATEGY] Starting experiment run: {experiment_run_id}")
    
    # Initialize services
    prompt_sql_service = PromptToSqlService()
    analytics_service = AnalyticsService(work_engine)
    image_analysis_service = ImageAnalysisService()
    print(f"[CAMPAIGN_STRATEGY] Services initialized")
    
    # Step 1: Generate or use SQL query to find impactful campaigns
    print(f"[CAMPAIGN_STRATEGY] Step 1: Generating SQL query (prompt_query={bool(prompt_query)}, sql_query={bool(sql_query)})")
    if prompt_query and not sql_query:
        try:
            sql_result = prompt_sql_service.generate_sql(prompt_query)
            sql_query = sql_result.get("sql", "")
        except Exception as e:
            return {
                "error": f"SQL generation failed: {str(e)}",
                "experiment_run_id": experiment_run_id,
            }
    
    if not sql_query:
        # Default query to find top campaigns by performance
        sql_query = """
        SELECT campaign_id, campaign_name, open_rate, click_rate, conversion_rate, revenue
        FROM campaigns
        WHERE open_rate > 0.2 OR conversion_rate > 0.05
        ORDER BY conversion_rate DESC, revenue DESC
        LIMIT 20
        """
    
    # Execute SQL query
    try:
        with work_engine.begin() as connection:
            result = connection.execute(text(sql_query))
            rows = [dict(row._mapping) for row in result]
    except Exception as e:
        return {
            "error": f"SQL query execution failed: {str(e)}",
            "experiment_run_id": experiment_run_id,
            "sql_query": sql_query,
        }
    
    if not rows:
        return {
            "error": "No campaigns found matching query criteria",
            "experiment_run_id": experiment_run_id,
            "sql_query": sql_query,
        }
    
    # Store campaign analysis results
    campaign_ids = []
    products_promoted = []
    
    for row in rows:
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
                except:
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
    
    # Step 2: Analyze images for these campaigns
    image_analyses = []
    visual_elements_list = []
    
    if image_directory:
        image_dir = Path(image_directory)
        if image_dir.exists():
            # Find images matching campaign IDs
            image_files = list(image_dir.glob("*.jpg")) + list(image_dir.glob("*.png")) + list(image_dir.glob("*.jpeg"))
            
            for image_file in image_files:
                campaign_id_from_file = _extract_campaign_id_from_filename(image_file.name)
                
                # Match image to campaign if ID found
                matched_campaign_id = None
                if campaign_id_from_file:
                    # Try exact match first
                    if campaign_id_from_file in campaign_ids:
                        matched_campaign_id = campaign_id_from_file
                    else:
                        # Try partial match
                        for cid in campaign_ids:
                            if campaign_id_from_file in str(cid) or str(cid) in campaign_id_from_file:
                                matched_campaign_id = cid
                                break
                
                # Analyze image
                try:
                    with open(image_file, "rb") as f:
                        import base64
                        image_data = base64.b64encode(f.read()).decode("utf-8")
                    
                    analysis_result = image_analysis_service.analyze_image(
                        image_base64=image_data,
                        campaign_id=matched_campaign_id,
                        campaign_name=None,
                        analysis_type="full",
                    )
                    
                    image_analyses.append(analysis_result)
                    
                    # Extract visual elements for correlation
                    for element in analysis_result.get("visual_elements", []):
                        visual_elements_list.append({
                            "element_type": element.get("element_type", "unknown"),
                            "description": element.get("description", ""),
                            "campaign_id": matched_campaign_id,
                        })
                    
                    # Store image analysis result
                    with work_engine.begin() as connection:
                        connection.execute(
                            text("""
                                INSERT INTO image_analysis_results
                                (experiment_run_id, campaign_id, image_id, image_path, visual_elements, 
                                 dominant_colors, composition_analysis, text_content, overall_description, marketing_relevance)
                                VALUES (:experiment_run_id, :campaign_id, :image_id, :image_path, :visual_elements,
                                        :dominant_colors, :composition_analysis, :text_content, :overall_description, :marketing_relevance)
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
                            }
                        )
                except Exception as e:
                    print(f"Failed to analyze image {image_file}: {str(e)}")
                    continue
    
    # Step 3: Cross-index visual elements with performance
    if visual_elements_list:
        # Group elements by type
        element_types = {}
        for elem in visual_elements_list:
            elem_type = elem["element_type"]
            if elem_type not in element_types:
                element_types[elem_type] = []
            element_types[elem_type].append(elem)
        
        # Correlate with performance
        for elem_type, elements in element_types.items():
            try:
                correlation_result = image_analysis_service.correlate_visual_elements_with_performance(
                    visual_elements=[elem["description"] for elem in elements],
                    date_range=None,
                    min_campaigns=1,
                )
                
                for corr in correlation_result.get("correlations", []):
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
            except Exception as e:
                print(f"Failed to correlate element type {elem_type}: {str(e)}")
    
    # Store experiment run
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
                "description": f"Analyzed {len(rows)} campaigns, {len(image_analyses)} images",
                "sql_query": sql_query,
                "status": "completed",
                "config": json.dumps({
                    "prompt_query": prompt_query,
                    "image_directory": image_directory,
                }),
                "results_summary": json.dumps({
                    "campaigns_analyzed": len(rows),
                    "images_analyzed": len(image_analyses),
                    "visual_elements_found": len(visual_elements_list),
                    "campaign_ids": campaign_ids[:10],  # First 10
                    "products_promoted": list(set(products_promoted))[:10],
                }),
                "completed_at": datetime.utcnow().isoformat(),
            }
        )
    
    return {
        "experiment_run_id": experiment_run_id,
        "status": "completed",
        "campaigns_analyzed": len(rows),
        "images_analyzed": len(image_analyses),
        "visual_elements_found": len(visual_elements_list),
        "campaign_ids": campaign_ids,
        "products_promoted": list(set(products_promoted)),
    }

