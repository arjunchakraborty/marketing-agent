"""Experiment endpoints for campaign strategy analysis."""
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
    try:
        result = run_campaign_strategy_experiment(
            sql_query=payload.sql_query,
            prompt_query=payload.prompt_query,
            image_directory=payload.image_directory,
            experiment_name=payload.experiment_name,
        )
        
        if "error" in result:
            return ExperimentRunResponse(
                experiment_run_id=result.get("experiment_run_id", "unknown"),
                status="failed",
                campaigns_analyzed=0,
                images_analyzed=0,
                visual_elements_found=0,
                error=result["error"],
            )
        
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
        raise HTTPException(status_code=500, detail=f"Experiment failed: {str(e)}")


@router.get("/{experiment_run_id}", response_model=ExperimentResultsResponse, summary="Get experiment results")
async def get_experiment_results(experiment_run_id: str) -> ExperimentResultsResponse:
    """Retrieve stored results for a specific experiment run."""
    from sqlalchemy import text
    from ...db.session import engine
    import json
    
    try:
        # Get experiment run
        with engine.begin() as connection:
            result = connection.execute(
                text("SELECT * FROM experiment_runs WHERE experiment_run_id = :run_id"),
                {"run_id": experiment_run_id}
            )
            row = result.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Experiment run not found")
            
            exp_data = dict(row._mapping)
            exp_data["config"] = json.loads(exp_data["config"]) if exp_data.get("config") else None
            exp_data["results_summary"] = json.loads(exp_data["results_summary"]) if exp_data.get("results_summary") else None
            
            from ...schemas.experiments import ExperimentRunStored
            experiment_run = ExperimentRunStored(**exp_data)
        
        # Get campaign analyses
        campaign_analyses = []
        with engine.begin() as connection:
            result = connection.execute(
                text("SELECT * FROM campaign_analysis WHERE experiment_run_id = :run_id ORDER BY created_at DESC"),
                {"run_id": experiment_run_id}
            )
            for row in result:
                data = dict(row._mapping)
                data["query_results"] = json.loads(data["query_results"]) if data.get("query_results") else None
                data["metrics"] = json.loads(data["metrics"]) if data.get("metrics") else None
                data["products_promoted"] = json.loads(data["products_promoted"]) if data.get("products_promoted") else None
                from ...schemas.experiments import CampaignAnalysisResult
                campaign_analyses.append(CampaignAnalysisResult(**data))
        
        # Get image analyses
        image_analyses = []
        with engine.begin() as connection:
            result = connection.execute(
                text("SELECT * FROM image_analysis_results WHERE experiment_run_id = :run_id ORDER BY created_at DESC"),
                {"run_id": experiment_run_id}
            )
            for row in result:
                data = dict(row._mapping)
                data["visual_elements"] = json.loads(data["visual_elements"]) if data.get("visual_elements") else None
                data["dominant_colors"] = json.loads(data["dominant_colors"]) if data.get("dominant_colors") else None
                from ...schemas.experiments import ImageAnalysisStoredResult
                image_analyses.append(ImageAnalysisStoredResult(**data))
        
        # Get correlations
        correlations = []
        with engine.begin() as connection:
            result = connection.execute(
                text("SELECT * FROM visual_element_correlations WHERE experiment_run_id = :run_id ORDER BY created_at DESC"),
                {"run_id": experiment_run_id}
            )
            for row in result:
                data = dict(row._mapping)
                data["average_performance"] = json.loads(data["average_performance"]) if data.get("average_performance") else None
                from ...schemas.experiments import VisualElementCorrelationStored
                correlations.append(VisualElementCorrelationStored(**data))
        
        return ExperimentResultsResponse(
            experiment_run=experiment_run,
            campaign_analyses=campaign_analyses,
            image_analyses=image_analyses,
            correlations=correlations,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve results: {str(e)}")


@router.get("/", response_model=List[ExperimentResultsResponse], summary="List all experiment runs")
async def list_experiments() -> List[ExperimentResultsResponse]:
    """List all experiment runs."""
    from sqlalchemy import text
    from ...db.session import engine
    
    try:
        with engine.begin() as connection:
            result = connection.execute(
                text("SELECT experiment_run_id FROM experiment_runs ORDER BY created_at DESC LIMIT 20")
            )
            run_ids = [row[0] for row in result]
        
        # Fetch full results for each
        experiments = []
        for run_id in run_ids:
            try:
                exp_result = await get_experiment_results(run_id)
                experiments.append(exp_result)
            except:
                continue
        
        return experiments
    except Exception as e:
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

