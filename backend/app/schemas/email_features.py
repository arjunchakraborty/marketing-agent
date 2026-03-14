"""Schemas for email feature detection and cataloging."""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Bounding box coordinates for detected features."""

    x_min: float = Field(description="Minimum x coordinate")
    y_min: float = Field(description="Minimum y coordinate")
    x_max: float = Field(description="Maximum x coordinate")
    y_max: float = Field(description="Maximum y coordinate")
    width: Optional[float] = Field(None, description="Width of bounding box")
    height: Optional[float] = Field(None, description="Height of bounding box")


class EmailFeature(BaseModel):
    """Detected email feature with metadata."""

    feature_type: str = Field(description="Type of feature (e.g., 'CTA button', 'discount badge')")
    feature_category: str = Field(description="Category: cta_buttons, promotions, products, content, branding, social_proof, urgency, structure")
    confidence: float = Field(description="Detection confidence score (0-1)")
    bbox: Optional[BoundingBox] = Field(None, description="Bounding box coordinates")
    position: Optional[str] = Field(None, description="Position in email: top, middle, bottom, left, right, center")
    text_content: Optional[str] = Field(None, description="Text content if applicable")
    color: Optional[str] = Field(None, description="Dominant color of the feature")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional feature metadata")


class FeatureCatalog(BaseModel):
    """Catalog of features organized by category."""

    cta_buttons: List[EmailFeature] = Field(default_factory=list)
    promotions: List[EmailFeature] = Field(default_factory=list)
    products: List[EmailFeature] = Field(default_factory=list)
    content: List[EmailFeature] = Field(default_factory=list)
    branding: List[EmailFeature] = Field(default_factory=list)
    social_proof: List[EmailFeature] = Field(default_factory=list)
    urgency: List[EmailFeature] = Field(default_factory=list)
    structure: List[EmailFeature] = Field(default_factory=list)
    summary: Dict[str, int] = Field(default_factory=dict, description="Summary statistics by category")


class EmailFeatureDetectionRequest(BaseModel):
    """Request for email feature detection."""

    image_url: Optional[str] = Field(None, description="URL of email image")
    image_base64: Optional[str] = Field(None, description="Base64-encoded image data")
    image_path: Optional[str] = Field(None, description="Local file path to image")
    campaign_id: Optional[str] = Field(None, description="Campaign ID for context")
    custom_prompts: Optional[List[str]] = Field(None, description="Additional detection prompts")


class EmailFeatureDetectionResponse(BaseModel):
    """Response from email feature detection."""

    campaign_id: Optional[str] = None
    image_id: Optional[str] = None
    features: List[EmailFeature] = Field(default_factory=list)
    feature_catalog: FeatureCatalog = Field(default_factory=FeatureCatalog)
    total_features_detected: int = 0
    error: Optional[str] = None


class FeatureCorrelationRequest(BaseModel):
    """Request for correlating features with campaign performance."""

    feature_category: Optional[str] = Field(None, description="Filter by feature category")
    campaign_ids: Optional[List[str]] = Field(None, description="Filter by campaign IDs")
    min_confidence: float = Field(0.5, description="Minimum confidence threshold")
    date_range: Optional[Dict[str, str]] = Field(None, description="Date range for performance analysis")


class FeatureCorrelationResponse(BaseModel):
    """Correlation analysis between features and campaign performance."""

    feature_category: str
    feature_type: str
    campaigns_analyzed: int
    average_performance: Dict[str, float] = Field(default_factory=dict)
    performance_impact: str
    recommendations: List[str] = Field(default_factory=list)
    success_indicators: List[str] = Field(default_factory=list)

