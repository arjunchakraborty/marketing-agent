"""Experiment endpoints for campaign strategy analysis."""
import json
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException

from ...schemas.experiments import (
    CampaignGenerationRequest,
    CampaignGenerationResponse,
    ExperimentRunRequest,
    ExperimentRunResponse,
    ExperimentResultsResponse,
)
from ...workflows.campaign_strategy_workflow import run_campaign_strategy_experiment

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/run", response_model=ExperimentRunResponse, summary="Run campaign strategy experiment")
async def run_experiment(payload: ExperimentRunRequest) -> ExperimentRunResponse:
    """
    Run a complete campaign strategy analysis workflow.
    
    This will:
    1. Query impactful campaigns using SQL (generated from prompt or provided)
    2. Analyze images of those campaigns
    3. Cross-index visual elements with performance
    4. Store all results in database
    """
    logger.info(f"Starting experiment run: name={payload.experiment_name}, has_sql={bool(payload.sql_query)}, has_prompt={bool(payload.prompt_query)}, image_dir={payload.image_directory}")
    
    try:
        logger.debug(f"Experiment payload: sql_query length={len(payload.sql_query) if payload.sql_query else 0}, prompt_query={payload.prompt_query[:100] if payload.prompt_query else None}")
        
        result = run_campaign_strategy_experiment(
            sql_query=payload.sql_query,
            prompt_query=payload.prompt_query,
            image_directory=payload.image_directory,
            experiment_name=payload.experiment_name,
        )
        
        logger.info(f"Experiment workflow completed: experiment_run_id={result.get('experiment_run_id')}, status={result.get('status')}")
        
        if "error" in result:
            logger.error(f"Experiment workflow returned error: experiment_run_id={result.get('experiment_run_id')}, error={result.get('error')}")
            return ExperimentRunResponse(
                experiment_run_id=result.get("experiment_run_id", "unknown"),
                status="failed",
                campaigns_analyzed=0,
                images_analyzed=0,
                visual_elements_found=0,
                error=result["error"],
            )
        
        logger.info(f"Experiment successful: campaigns={result.get('campaigns_analyzed', 0)}, images={result.get('images_analyzed', 0)}, elements={result.get('visual_elements_found', 0)}")
        
        return ExperimentRunResponse(
            experiment_run_id=result["experiment_run_id"],
            status=result.get("status", "completed"),
            campaigns_analyzed=result.get("campaigns_analyzed", 0),
            images_analyzed=result.get("images_analyzed", 0),
            visual_elements_found=result.get("visual_elements_found", 0),
            campaign_ids=result.get("campaign_ids", []),
            products_promoted=result.get("products_promoted", []),
        )
    except Exception as e:
        logger.exception(f"Experiment run failed with exception: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Experiment failed: {str(e)}")


@router.get("/{experiment_run_id}", response_model=ExperimentResultsResponse, summary="Get experiment results")
async def get_experiment_results(experiment_run_id: str) -> ExperimentResultsResponse:
    """Retrieve stored results for a specific experiment run."""
    from sqlalchemy import text
    from ...db.session import engine
    import json
    
    logger.info(f"Retrieving experiment results: experiment_run_id={experiment_run_id}")
    
    try:
        # Get experiment run
        logger.debug(f"Querying experiment_runs table for run_id={experiment_run_id}")
        with engine.begin() as connection:
            result = connection.execute(
                text("SELECT * FROM experiment_runs WHERE experiment_run_id = :run_id"),
                {"run_id": experiment_run_id}
            )
            row = result.fetchone()
            if not row:
                logger.warning(f"Experiment run not found: experiment_run_id={experiment_run_id}")
                raise HTTPException(status_code=404, detail="Experiment run not found")
            
            logger.debug(f"Found experiment run: name={row._mapping.get('name')}, status={row._mapping.get('status')}")
            
            exp_data = dict(row._mapping)
            
            # Handle None values and convert to strings where needed
            if exp_data.get("created_at") is None:
                exp_data["created_at"] = None
            elif not isinstance(exp_data.get("created_at"), str):
                exp_data["created_at"] = str(exp_data["created_at"])
            
            if exp_data.get("updated_at") is None:
                exp_data["updated_at"] = None
            elif not isinstance(exp_data.get("updated_at"), str):
                exp_data["updated_at"] = str(exp_data["updated_at"])
            
            if exp_data.get("completed_at") is None:
                exp_data["completed_at"] = None
            elif not isinstance(exp_data.get("completed_at"), str):
                exp_data["completed_at"] = str(exp_data["completed_at"])
            
            # Parse JSON fields
            try:
                exp_data["config"] = json.loads(exp_data["config"]) if exp_data.get("config") else None
            except (json.JSONDecodeError, TypeError) as e:
                logger.error(f"Failed to parse JSON in experiment config: {e}")
                exp_data["config"] = None
            
            try:
                exp_data["results_summary"] = json.loads(exp_data["results_summary"]) if exp_data.get("results_summary") else None
            except (json.JSONDecodeError, TypeError) as e:
                logger.error(f"Failed to parse JSON in experiment results_summary: {e}")
                exp_data["results_summary"] = None
            
            # Ensure all required fields have defaults
            if exp_data.get("status") is None:
                exp_data["status"] = "unknown"
            
            from ...schemas.experiments import ExperimentRunStored
            try:
                experiment_run = ExperimentRunStored(**exp_data)
            except Exception as e:
                logger.error(f"Failed to create ExperimentRunStored from data: {e}, data keys: {list(exp_data.keys())}")
                raise
        
        # Get campaign analyses
        logger.debug(f"Querying campaign_analysis table for run_id={experiment_run_id}")
        campaign_analyses = []
        try:
            with engine.begin() as connection:
                result = connection.execute(
                    text("SELECT * FROM campaign_analysis WHERE experiment_run_id = :run_id ORDER BY created_at DESC"),
                    {"run_id": experiment_run_id}
                )
                for row in result:
                    try:
                        data = dict(row._mapping)
                        row_id = data.get("id")
                        
                        # Parse JSON fields safely
                        if data.get("query_results"):
                            if isinstance(data["query_results"], str):
                                try:
                                    data["query_results"] = json.loads(data["query_results"])
                                except json.JSONDecodeError as e:
                                    logger.warning(f"Failed to parse query_results JSON for row_id={row_id}: {e}")
                                    data["query_results"] = None
                            # If already a dict/list, keep as is
                        else:
                            data["query_results"] = None
                        
                        if data.get("metrics"):
                            if isinstance(data["metrics"], str):
                                try:
                                    data["metrics"] = json.loads(data["metrics"])
                                except json.JSONDecodeError as e:
                                    logger.warning(f"Failed to parse metrics JSON for row_id={row_id}: {e}")
                                    data["metrics"] = None
                        else:
                            data["metrics"] = None
                        
                        if data.get("products_promoted"):
                            if isinstance(data["products_promoted"], str):
                                try:
                                    data["products_promoted"] = json.loads(data["products_promoted"])
                                except json.JSONDecodeError as e:
                                    logger.warning(f"Failed to parse products_promoted JSON for row_id={row_id}: {e}")
                                    data["products_promoted"] = None
                        else:
                            data["products_promoted"] = None
                        
                        # Handle None values for required fields
                        if not data.get("created_at"):
                            data["created_at"] = datetime.utcnow().isoformat()
                        
                        from ...schemas.experiments import CampaignAnalysisResult
                        campaign_analyses.append(CampaignAnalysisResult(**data))
                    except Exception as e:
                        logger.error(f"Failed to parse campaign analysis row: run_id={experiment_run_id}, row_id={row._mapping.get('id')}, error={type(e).__name__}: {str(e)}", exc_info=True)
                        continue
        except Exception as e:
            logger.error(f"Failed parsing Querying campaign_analysis table for run_id={experiment_run_id}: {type(e).__name__}: {str(e)}", exc_info=True)
            # Continue anyway - return empty list for campaign_analyses
        
        logger.debug(f"Found {len(campaign_analyses)} campaign analyses")
        
        # Get image analyses
        logger.debug(f"Querying image_analysis_results table for run_id={experiment_run_id}")
        image_analyses = []
        try:
            with engine.begin() as connection:
                result = connection.execute(
                    text("SELECT * FROM image_analysis_results WHERE experiment_run_id = :run_id ORDER BY created_at DESC"),
                    {"run_id": experiment_run_id}
                )
                for row in result:
                    try:
                        data = dict(row._mapping)
                        row_id = data.get("id")
                        
                        # Parse JSON fields safely
                        if data.get("visual_elements"):
                            if isinstance(data["visual_elements"], str):
                                try:
                                    data["visual_elements"] = json.loads(data["visual_elements"])
                                except json.JSONDecodeError as e:
                                    logger.warning(f"Failed to parse visual_elements JSON for row_id={row_id}: {e}")
                                    data["visual_elements"] = None
                        else:
                            data["visual_elements"] = None
                        
                        if data.get("dominant_colors"):
                            if isinstance(data["dominant_colors"], str):
                                try:
                                    data["dominant_colors"] = json.loads(data["dominant_colors"])
                                except json.JSONDecodeError as e:
                                    logger.warning(f"Failed to parse dominant_colors JSON for row_id={row_id}: {e}")
                                    data["dominant_colors"] = None
                            
                            # Convert list of dicts to list of strings if needed
                            if isinstance(data["dominant_colors"], list):
                                converted_colors = []
                                for color in data["dominant_colors"]:
                                    if isinstance(color, dict):
                                        # Extract color string from dict
                                        converted_colors.append(color.get("color", str(color)))
                                    elif isinstance(color, str):
                                        converted_colors.append(color)
                                data["dominant_colors"] = converted_colors if converted_colors else None
                        else:
                            data["dominant_colors"] = None
                        
                        # Handle None values for required fields
                        if not data.get("created_at"):
                            data["created_at"] = datetime.utcnow().isoformat()
                        
                        from ...schemas.experiments import ImageAnalysisStoredResult
                        image_analyses.append(ImageAnalysisStoredResult(**data))
                    except Exception as e:
                        logger.error(f"Failed to parse image analysis row: run_id={experiment_run_id}, row_id={row_id}, error={type(e).__name__}: {str(e)}", exc_info=True)
                        continue
        except Exception as e:
            logger.error(f"Failed parsing Querying image_analysis_results table for run_id={experiment_run_id}: {type(e).__name__}: {str(e)}", exc_info=True)
            # Continue anyway - return empty list for image_analyses
        
        logger.debug(f"Found {len(image_analyses)} image analyses")
        
        # Get correlations
        logger.debug(f"Querying visual_element_correlations table for run_id={experiment_run_id}")
        correlations = []
        try:
            with engine.begin() as connection:
                result = connection.execute(
                    text("SELECT * FROM visual_element_correlations WHERE experiment_run_id = :run_id ORDER BY created_at DESC"),
                    {"run_id": experiment_run_id}
                )
                for row in result:
                    try:
                        data = dict(row._mapping)
                        row_id = data.get("id")
                        
                        # Parse JSON fields safely
                        if data.get("average_performance"):
                            if isinstance(data["average_performance"], str):
                                try:
                                    data["average_performance"] = json.loads(data["average_performance"])
                                except json.JSONDecodeError as e:
                                    logger.warning(f"Failed to parse average_performance JSON for row_id={row_id}: {e}")
                                    data["average_performance"] = None
                        else:
                            data["average_performance"] = None
                        
                        # Handle None values for required fields
                        if not data.get("created_at"):
                            data["created_at"] = datetime.utcnow().isoformat()
                        
                        from ...schemas.experiments import VisualElementCorrelationStored
                        correlations.append(VisualElementCorrelationStored(**data))
                    except Exception as e:
                        logger.error(f"Failed to parse correlation row: run_id={experiment_run_id}, row_id={row_id}, error={type(e).__name__}: {str(e)}", exc_info=True)
                        continue
        except Exception as e:
            logger.error(f"Failed parsing Querying visual_element_correlations table for run_id={experiment_run_id}: {type(e).__name__}: {str(e)}", exc_info=True)
            # Continue anyway - return empty list for correlations
        
        logger.debug(f"Found {len(correlations)} correlations")
        logger.info(f"Successfully retrieved experiment results: campaigns={len(campaign_analyses)}, images={len(image_analyses)}, correlations={len(correlations)}")
        
        return ExperimentResultsResponse(
            experiment_run=experiment_run,
            campaign_analyses=campaign_analyses,
            image_analyses=image_analyses,
            correlations=correlations,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to retrieve experiment results: experiment_run_id={experiment_run_id}, error={type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve results: {str(e)}")


@router.get("/", response_model=List[ExperimentResultsResponse], summary="List all experiment runs")
async def list_experiments() -> List[ExperimentResultsResponse]:
    """List all experiment runs."""
    from sqlalchemy import text
    from ...db.session import engine
    
    logger.info("Listing all experiment runs")
    
    try:
        with engine.begin() as connection:
            result = connection.execute(
                text("SELECT experiment_run_id FROM experiment_runs ORDER BY created_at DESC LIMIT 20")
            )
            run_ids = [row[0] for row in result]
        
        logger.info(f"Found {len(run_ids)} experiment runs to retrieve")
        
        # Fetch full results for each
        experiments = []
        failed_count = 0
        for run_id in run_ids:
            try:
                exp_result = await get_experiment_results(run_id)
                experiments.append(exp_result)
            except Exception as e:
                failed_count += 1
                logger.warning(f"Failed to retrieve experiment {run_id}: {type(e).__name__}: {str(e)}")
                continue
        
        logger.info(f"Successfully retrieved {len(experiments)}/{len(run_ids)} experiments (failed: {failed_count})")
        return experiments
    except Exception as e:
        logger.exception(f"Failed to list experiments: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list experiments: {str(e)}")


@router.post("/generate-campaigns", response_model=CampaignGenerationResponse, summary="Generate new campaigns from analysis")
async def generate_campaigns(payload: CampaignGenerationRequest) -> CampaignGenerationResponse:
    """Generate new email campaign formats using insights from analysis."""
    from ...services.intelligence_service import IntelligenceService
    from ...db.session import engine
    from sqlalchemy import text
    import json
    
    try:
        # Get experiment results
        exp_results = await get_experiment_results(payload.experiment_run_id)
        
        # Extract insights
        top_products = []
        if payload.use_top_products and exp_results.experiment_run.results_summary:
            top_products = exp_results.experiment_run.results_summary.get("products_promoted", [])[:10]
        
        if payload.target_products:
            top_products = payload.target_products
        
        # Get visual element insights
        visual_insights = []
        for corr in exp_results.correlations:
            visual_insights.append(f"{corr.element_type}: {corr.recommendation}")
        
        # Generate campaigns using intelligence service
        intelligence_service = IntelligenceService()
        
        objectives = ["Increase conversion rate", "Maximize revenue from sales event"]
        audience_segments = ["High-value customers", "Price-sensitive shoppers"]
        
        constraints = {
            "products": top_products[:5],
            "strategy_focus": payload.strategy_focus or "visual_elements",
            "visual_insights": visual_insights[:3],
        }
        
        campaigns_data = intelligence_service.recommend_campaigns(
            objectives=objectives,
            audience_segments=audience_segments,
            constraints=constraints,
        )
        
        # Format campaigns
        campaigns = []
        for c in campaigns_data[:payload.num_campaigns]:
            campaigns.append({
                "name": c.get("name", "Generated Campaign"),
                "channel": c.get("channel", "email"),
                "objective": c.get("objective", ""),
                "expected_uplift": c.get("expected_uplift", "0%"),
                "summary": c.get("summary", ""),
                "talking_points": c.get("talking_points", []),
            })
        
        strategy_insights = f"Generated {len(campaigns)} campaigns based on analysis of {exp_results.experiment_run.results_summary.get('campaigns_analyzed', 0)} campaigns and {exp_results.experiment_run.results_summary.get('images_analyzed', 0)} images. Using top products: {', '.join(top_products[:3])}"
        
        return CampaignGenerationResponse(
            campaigns=campaigns,
            strategy_insights=strategy_insights,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Campaign generation failed: {str(e)}")

