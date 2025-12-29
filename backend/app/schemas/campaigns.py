"""Schemas for campaign targeting endpoints."""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AudienceSegment(BaseModel):
    """Audience segment definition."""
    
    segment_id: str = Field(..., description="Unique segment identifier")
    name: str = Field(..., description="Segment name")
    description: Optional[str] = Field(None, description="Segment description")
    criteria: Dict[str, Any] = Field(..., description="Targeting criteria")
    size: Optional[int] = Field(None, description="Estimated segment size")


class TargetCampaignRequest(BaseModel):
    """Request schema for creating a targeted campaign."""
    
    campaign_name: str = Field(..., description="Campaign name")
    segment_ids: List[str] = Field(..., description="List of audience segment IDs to target")
    channel: str = Field("email", description="Campaign channel (email, sms, etc.)")
    objective: str = Field(..., description="Campaign objective")
    constraints: Optional[Dict[str, Any]] = Field(None, description="Additional targeting constraints")
    products: Optional[List[str]] = Field(None, description="Products to promote")
    product_images: Optional[List[Dict[str, str]]] = Field(None, description="Product images with URLs and product IDs")


class TargetCampaignResponse(BaseModel):
    """Response schema for targeted campaign creation."""
    
    campaign_id: str = Field(..., description="Created campaign ID")
    campaign_name: str = Field(..., description="Campaign name")
    segments: List[AudienceSegment] = Field(..., description="Targeted segments")
    estimated_reach: int = Field(..., description="Estimated audience reach")
    status: str = Field(..., description="Campaign status")
    created_at: str = Field(..., description="Creation timestamp")
    product_images: Optional[List[Dict[str, str]]] = Field(None, description="Product images associated with campaign")


class TargetingAnalysisRequest(BaseModel):
    """Request schema for analyzing targeting effectiveness."""
    
    campaign_id: Optional[str] = Field(None, description="Campaign ID to analyze")
    segment_ids: Optional[List[str]] = Field(None, description="Segments to analyze")
    date_range: Optional[Dict[str, str]] = Field(None, description="Date range for analysis")


class TargetingAnalysisResponse(BaseModel):
    """Response schema for targeting analysis."""
    
    campaign_id: Optional[str] = Field(None, description="Analyzed campaign ID")
    segment_performance: List[Dict[str, Any]] = Field(..., description="Performance by segment")
    recommendations: List[str] = Field(..., description="Optimization recommendations")
    summary: str = Field(..., description="Analysis summary")


class CampaignPerformanceResponse(BaseModel):
    """Response schema for campaign performance by segment."""
    
    campaign_id: str = Field(..., description="Campaign ID")
    overall_performance: Dict[str, Any] = Field(..., description="Overall campaign metrics")
    segment_performance: List[Dict[str, Any]] = Field(..., description="Performance breakdown by segment")
    top_performing_segments: List[str] = Field(..., description="Top performing segment IDs")

