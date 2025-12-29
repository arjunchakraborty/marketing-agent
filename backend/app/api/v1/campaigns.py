"""Email campaign generation endpoints."""
import logging
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException

from ...schemas.campaigns import (
    EmailCampaignGenerationRequest,
    EmailCampaignResponse,
    EmailCampaignsListResponse,
)
from ...services.campaign_generation_service import CampaignGenerationService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/generate", response_model=EmailCampaignResponse, summary="Generate a new email campaign")
async def generate_email_campaign(payload: EmailCampaignGenerationRequest) -> EmailCampaignResponse:
    """
    Generate a new email campaign with HTML template, RAG-based content, and optional image generation.
    
    This endpoint uses AI and RAG to generate complete email campaign content including:
    - HTML email template with hero images and product images
    - Subject line variations based on past successful campaigns
    - Email body with greeting, content, CTA, and closing (inspired by past campaigns)
    - Design recommendations from successful past campaigns
    - Talking points
    - Optional AI-generated hero images
    - Expected performance metrics
    - References to past campaigns used as inspiration
    """
    logger.info(f"Generating email campaign: objective={payload.objective}, audience={payload.audience_segment}, use_past_campaigns={payload.use_past_campaigns}")
    
    try:
        service = CampaignGenerationService()
        campaign = service.generate_email_campaign(
            campaign_name=payload.campaign_name,
            objective=payload.objective,
            audience_segment=payload.audience_segment,
            products=payload.products,
            product_images=payload.product_images,
            tone=payload.tone,
            key_message=payload.key_message,
            call_to_action=payload.call_to_action,
            include_promotion=payload.include_promotion,
            promotion_details=payload.promotion_details,
            subject_line_suggestions=payload.subject_line_suggestions,
            include_preview_text=payload.include_preview_text,
            design_guidance=payload.design_guidance,
            use_past_campaigns=payload.use_past_campaigns,
            num_similar_campaigns=payload.num_similar_campaigns,
            generate_hero_image=payload.generate_hero_image,
            hero_image_prompt=payload.hero_image_prompt,
        )
        
        logger.info(f"Successfully generated campaign: campaign_id={campaign.campaign_id}")
        return campaign
    except Exception as e:
        logger.exception(f"Failed to generate email campaign: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Campaign generation failed: {str(e)}")


@router.get("/", response_model=EmailCampaignsListResponse, summary="List all generated campaigns")
async def list_campaigns(limit: int = 20, offset: int = 0) -> EmailCampaignsListResponse:
    """Retrieve a list of all generated email campaigns."""
    logger.info(f"Listing campaigns: limit={limit}, offset={offset}")
    
    try:
        service = CampaignGenerationService()
        campaigns = service.list_campaigns(limit=limit, offset=offset)
        
        logger.info(f"Retrieved {len(campaigns)} campaigns")
        return EmailCampaignsListResponse(
            campaigns=campaigns,
            total=len(campaigns),
        )
    except Exception as e:
        logger.exception(f"Failed to list campaigns: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list campaigns: {str(e)}")


@router.get("/{campaign_id}", response_model=EmailCampaignResponse, summary="Get a specific campaign")
async def get_campaign(campaign_id: str) -> EmailCampaignResponse:
    """Retrieve a specific generated email campaign by ID."""
    logger.info(f"Retrieving campaign: campaign_id={campaign_id}")
    
    try:
        service = CampaignGenerationService()
        campaign = service.get_campaign(campaign_id)
        
        if not campaign:
            raise HTTPException(status_code=404, detail=f"Campaign not found: {campaign_id}")
        
        return campaign
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to retrieve campaign: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve campaign: {str(e)}")

