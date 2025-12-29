"""Schemas for email campaign generation."""
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class EmailCampaignGenerationRequest(BaseModel):
    """Request to generate a new email campaign."""
    campaign_name: Optional[str] = Field(None, description="Name for the campaign")
    objective: str = Field(..., description="Campaign objective (e.g., 'Increase sales', 'Promote new product', 'Re-engage customers')")
    audience_segment: Optional[str] = Field(None, description="Target audience segment")
    products: Optional[List[str]] = Field(None, description="Products to promote in the campaign")
    product_images: Optional[List[str]] = Field(None, description="URLs or paths to product images")
    tone: Optional[str] = Field("professional", description="Email tone (e.g., 'professional', 'casual', 'urgent', 'friendly')")
    key_message: Optional[str] = Field(None, description="Key message or value proposition")
    call_to_action: Optional[str] = Field(None, description="Desired call-to-action text")
    include_promotion: bool = Field(False, description="Whether to include promotional offers")
    promotion_details: Optional[str] = Field(None, description="Details about the promotion (discount, offer, etc.)")
    subject_line_suggestions: int = Field(3, description="Number of subject line variations to generate")
    include_preview_text: bool = Field(True, description="Whether to generate preview text")
    design_guidance: Optional[str] = Field(None, description="Design preferences or constraints")
    use_past_campaigns: bool = Field(True, description="Use RAG to retrieve insights from past successful campaigns")
    num_similar_campaigns: int = Field(5, description="Number of similar past campaigns to retrieve for reference")
    generate_hero_image: bool = Field(False, description="Generate a new hero image using AI")
    hero_image_prompt: Optional[str] = Field(None, description="Custom prompt for hero image generation")


class EmailContent(BaseModel):
    """Email content components."""
    subject_line: str
    preview_text: Optional[str] = None
    greeting: str
    body: str
    call_to_action: str
    closing: str
    footer: Optional[str] = None
    html_template: Optional[str] = Field(None, description="Complete HTML email template")
    hero_image_url: Optional[str] = Field(None, description="URL or path to hero image")
    product_image_urls: Optional[List[str]] = Field(None, description="URLs or paths to product images")


class PastCampaignReference(BaseModel):
    """Reference to a past campaign used in generation."""
    campaign_id: str
    campaign_name: Optional[str] = None
    similarity_score: float
    insights_used: List[str] = Field(default_factory=list)


class EmailCampaignResponse(BaseModel):
    """Response with generated email campaign."""
    campaign_id: str
    campaign_name: str
    objective: str
    audience_segment: Optional[str] = None
    email_content: EmailContent
    subject_line_variations: List[str] = Field(default_factory=list)
    design_recommendations: List[str] = Field(default_factory=list)
    talking_points: List[str] = Field(default_factory=list)
    expected_metrics: Optional[Dict[str, str]] = None
    past_campaign_references: List[PastCampaignReference] = Field(default_factory=list, description="Past campaigns used as reference")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class EmailCampaignsListResponse(BaseModel):
    """Response with list of generated campaigns."""
    campaigns: List[EmailCampaignResponse]
    total: int
