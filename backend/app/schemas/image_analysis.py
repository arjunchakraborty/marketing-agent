"""Schemas for image analysis and visual element detection."""
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class VisualElement(BaseModel):
    """Detected visual element in an image."""
    element_type: str = Field(..., description="Type of visual element (e.g., 'product', 'text', 'CTA button', 'logo')")
    description: str = Field(..., description="Description of the visual element")
    position: Optional[Dict[str, float]] = Field(None, description="Position coordinates if available")
    confidence: Optional[float] = Field(None, description="Confidence score for detection")
    color_palette: Optional[List[str]] = Field(None, description="Dominant colors in this element")
    text_content: Optional[str] = Field(None, description="Extracted text content if applicable")


class ImageAnalysisRequest(BaseModel):
    """Request to analyze an image."""
    image_url: Optional[str] = Field(None, description="URL of the image to analyze")
    image_base64: Optional[str] = Field(None, description="Base64-encoded image data")
    campaign_id: Optional[str] = Field(None, description="Associated campaign identifier")
    campaign_name: Optional[str] = Field(None, description="Campaign name for context")
    analysis_type: str = Field(
        default="full",
        description="Type of analysis: 'full', 'visual_elements', 'colors', 'text', 'composition'"
    )


class ImageAnalysisResponse(BaseModel):
    """Response from image analysis."""
    image_id: str = Field(..., description="Unique identifier for the analyzed image")
    campaign_id: Optional[str] = Field(None, description="Associated campaign identifier")
    visual_elements: List[VisualElement] = Field(default_factory=list, description="Detected visual elements")
    dominant_colors: List[str] = Field(default_factory=list, description="Dominant colors in the image")
    composition_analysis: Optional[str] = Field(None, description="Analysis of image composition and layout")
    text_content: Optional[str] = Field(None, description="All extracted text from the image")
    overall_description: str = Field(..., description="Overall description of the image")
    marketing_relevance: Optional[str] = Field(None, description="Marketing-specific insights")
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


class VisualElementCorrelationRequest(BaseModel):
    """Request to correlate visual elements with campaign performance."""
    visual_elements: List[str] = Field(..., description="List of visual element types or descriptions to analyze")
    date_range: Optional[Dict[str, str]] = Field(None, description="Date range for campaign analysis")
    min_campaigns: int = Field(default=5, description="Minimum number of campaigns to include in analysis")


class VisualElementCorrelation(BaseModel):
    """Correlation between visual element and campaign performance."""
    element_type: str = Field(..., description="Type of visual element")
    element_description: str = Field(..., description="Description of the element")
    average_performance: Dict[str, float] = Field(..., description="Average performance metrics (e.g., open_rate, click_rate)")
    performance_impact: str = Field(..., description="Assessment of performance impact")
    recommendation: str = Field(..., description="Recommendation based on correlation")


class VisualElementCorrelationResponse(BaseModel):
    """Response with visual element correlations."""
    correlations: List[VisualElementCorrelation] = Field(default_factory=list)
    summary: str = Field(..., description="Summary of findings")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class CampaignImageBatchRequest(BaseModel):
    """Request to analyze multiple campaign images."""
    campaign_ids: List[str] = Field(..., description="List of campaign IDs to analyze")
    analysis_type: str = Field(default="full", description="Type of analysis to perform")


class CampaignImageBatchResponse(BaseModel):
    """Response from batch image analysis."""
    analyses: List[ImageAnalysisResponse] = Field(default_factory=list)
    total_analyzed: int = Field(..., description="Total number of images analyzed")
    completed_at: datetime = Field(default_factory=datetime.utcnow)

