"""Schemas for campaign strategy experiments."""
from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field


class ExperimentRunRequest(BaseModel):
    """Request to run a campaign strategy experiment using vector database."""
    prompt_query: str = Field(..., description="Natural language prompt describing what campaigns to find (e.g., 'high performing email campaigns', 'campaigns with high conversion rates')")
    collection_name: Optional[str] = Field(None, description="Optional vector database collection name to search. If not provided, searches default collections.")
    experiment_name: Optional[str] = Field(None, description="Name for this experiment run")
    num_campaigns: int = Field(10, description="Number of campaigns to retrieve and analyze")


class ExperimentRunResponse(BaseModel):
    """Response from experiment run."""
    experiment_run_id: str
    status: str
    campaigns_analyzed: int
    images_analyzed: int
    visual_elements_found: int
    campaign_ids: List[str] = Field(default_factory=list)
    products_promoted: List[str] = Field(default_factory=list)
    key_features: Optional[Dict[str, Any]] = Field(None, description="Key features, patterns, and recommendations extracted from campaigns")
    error: Optional[str] = None


class CampaignAnalysisResult(BaseModel):
    """Stored campaign analysis result."""
    id: int
    experiment_run_id: str
    campaign_id: Optional[str]
    campaign_name: Optional[str]
    sql_query: str
    query_results: Optional[Dict] = None
    metrics: Optional[Dict] = None
    products_promoted: Optional[List[str]] = None
    created_at: str


class ImageAnalysisStoredResult(BaseModel):
    """Stored image analysis result."""
    id: int
    experiment_run_id: str
    campaign_id: Optional[str]
    image_id: str
    image_path: Optional[str]
    visual_elements: Optional[List[Dict]] = None
    dominant_colors: Optional[List[str]] = None
    composition_analysis: Optional[str] = None
    text_content: Optional[str] = None
    overall_description: Optional[str] = None
    marketing_relevance: Optional[str] = None
    created_at: str


class VisualElementCorrelationStored(BaseModel):
    """Stored visual element correlation."""
    id: int
    experiment_run_id: str
    element_type: str
    element_description: Optional[str]
    average_performance: Optional[Dict] = None
    performance_impact: Optional[str]
    recommendation: Optional[str]
    campaign_count: Optional[int]
    created_at: str


class ExperimentRunStored(BaseModel):
    """Stored experiment run."""
    id: int
    experiment_run_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    sql_query: Optional[str] = None
    status: str
    config: Optional[Dict] = None
    results_summary: Optional[Dict] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None


class ExperimentResultsResponse(BaseModel):
    """Response with stored experiment results."""
    experiment_run: ExperimentRunStored
    campaign_analyses: List[CampaignAnalysisResult] = Field(default_factory=list)
    image_analyses: List[ImageAnalysisStoredResult] = Field(default_factory=list)
    correlations: List[VisualElementCorrelationStored] = Field(default_factory=list)
    hero_image_prompts: Optional[List[str]] = Field(None, description="Hero image prompts generated from experiment")
    text_prompts: Optional[List[str]] = Field(None, description="Text prompts generated from experiment")
    call_to_action_prompts: Optional[List[str]] = Field(None, description="Call to action prompts generated from experiment")


class CampaignGenerationRequest(BaseModel):
    """Request to generate new campaigns based on analysis."""
    experiment_run_id: str
    target_products: Optional[List[str]] = Field(None, description="Specific products to promote")
    use_top_products: bool = Field(True, description="Use top products from analysis")
    strategy_focus: Optional[str] = Field(None, description="Focus area: visual_elements, colors, layout, etc.")
    num_campaigns: int = Field(5, description="Number of campaign variations to generate")


class CampaignGenerationResponse(BaseModel):
    """Response with generated campaigns."""
    campaigns: List[Dict] = Field(default_factory=list)
    strategy_insights: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)

