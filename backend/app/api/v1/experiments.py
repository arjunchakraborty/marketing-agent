"""Experiment endpoints for campaign strategy analysis."""
import json
import logging
from datetime import datetime
from typing import List, Optional, Any

from fastapi import APIRouter, HTTPException

from ...schemas.experiments import (
    CampaignGenerationRequest,
    CampaignGenerationResponse,
    ExperimentRunRequest,
    ExperimentRunResponse,
    ExperimentResultsResponse,
)
from ...workflows.vector_db_experiment_workflow import run_vector_db_experiment

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/run", response_model=ExperimentRunResponse, summary="Run campaign strategy experiment using vector database")
async def run_experiment(payload: ExperimentRunRequest) -> ExperimentRunResponse:
    """
    Run a campaign strategy analysis workflow using vector database.
    
    This will:
    1. Search for campaigns in vector database using the prompt query
    2. Extract key features and patterns from identified campaigns
    3. Generate recommendations about what makes these campaigns effective
    4. Return insights about campaign features
    
    The prompt_query should describe what type of campaigns to find (e.g., 
    "high performing email campaigns", "campaigns with high conversion rates",
    "product launch campaigns", etc.)
    """
    logger.info(f"Starting vector DB experiment: name={payload.experiment_name}, prompt_query={payload.prompt_query[:100]}")
    
    try:
        result = run_vector_db_experiment(
            prompt_query=payload.prompt_query,
            collection_name=payload.collection_name,
            experiment_name=payload.experiment_name,
            num_campaigns=payload.num_campaigns,
        )
        
        logger.info(f"Experiment workflow completed: experiment_run_id={result.get('experiment_run_id')}, status={result.get('status')}")
        
        if result.get("status") == "error" or "error" in result:
            logger.error(f"Experiment workflow returned error: experiment_run_id={result.get('experiment_run_id')}, error={result.get('error')}")
            return ExperimentRunResponse(
                experiment_run_id=result.get("experiment_run_id", "unknown"),
                status="failed",
                campaigns_analyzed=0,
                images_analyzed=0,
                visual_elements_found=0,
                error=result.get("error", "Unknown error"),
            )
        
        key_features = result.get("key_features", {})
        recommendations = key_features.get("recommendations", [])
        
        logger.info(f"Experiment successful: campaigns={result.get('campaigns_analyzed', 0)}, features={len(key_features.get('key_features', []))}")
        
        return ExperimentRunResponse(
            experiment_run_id=result["experiment_run_id"],
            status=result.get("status", "completed"),
            campaigns_analyzed=result.get("campaigns_analyzed", 0),
            images_analyzed=0,  # Not using image analysis in vector DB workflow
            visual_elements_found=len(key_features.get("key_features", [])),
            campaign_ids=result.get("campaign_ids", []),
            products_promoted=[],  # Can be extracted from campaigns if needed
            key_features=key_features,
        )
    except HTTPException:
        raise
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


