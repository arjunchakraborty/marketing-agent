"""Email campaign generation endpoints."""
import logging
import uuid
from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field

from fastapi import APIRouter, HTTPException

from ...schemas.campaigns import (
    EmailCampaignGenerationRequest,
    EmailCampaignResponse,
    EmailCampaignsListResponse,
)
from ...services.campaign_generation_service import CampaignGenerationService
from ...services.vector_db_service import VectorDBService

logger = logging.getLogger(__name__)
router = APIRouter()


class VectorSearchRequest(BaseModel):
    """Request to search campaigns in vector database."""
    query: str = Field(..., description="Natural language query to search for campaigns")
    collection_name: Optional[str] = Field(None, description="Optional collection name (default: klaviyo_campaigns)")
    num_results: int = Field(10, description="Number of results to return", ge=1, le=50)


class VectorSearchResponse(BaseModel):
    """Response from vector database search."""
    campaigns: List[Dict[str, Any]] = Field(default_factory=list, description="List of matching campaigns")
    total_found: int = Field(0, description="Total number of campaigns found")
    query: str = Field(..., description="The search query used")


@router.get("/collections", response_model=List[str], summary="List all available vector database collections")
async def list_collections() -> List[str]:
    """Get a list of all available collections in the vector database."""
    logger.info("Listing all vector database collections")
    
    try:
        from ...services.vector_db_service import list_all_collections
        collections = list_all_collections()
        return collections
    except Exception as e:
        logger.exception(f"Failed to list collections: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list collections: {str(e)}")


@router.post("/search", response_model=VectorSearchResponse, summary="Search campaigns in vector database")
async def search_campaigns(payload: VectorSearchRequest) -> VectorSearchResponse:
    """
    Search for campaigns in the vector database using natural language.
    
    This endpoint uses semantic similarity to find campaigns that match your query.
    Examples:
    - "high performing email campaigns"
    - "campaigns with high conversion rates"
    - "product launch campaigns"
    - "campaigns promoting outdoor gear"
    """
    logger.info(f"Searching campaigns: query={payload.query[:100]}, collection={payload.collection_name}, num_results={payload.num_results}")
    
    try:
        collection_name = payload.collection_name or "klaviyo_campaigns"
        vector_db_service = VectorDBService(collection_name=collection_name)
        
        similar_campaigns = vector_db_service.search_similar_campaigns(
            query_text=payload.query,
            n_results=payload.num_results,
        )
        
        logger.info(f"Found {len(similar_campaigns)} campaigns matching query")
        
        return VectorSearchResponse(
            campaigns=similar_campaigns,
            total_found=len(similar_campaigns),
            query=payload.query,
        )
    except Exception as e:
        logger.exception(f"Failed to search campaigns: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Campaign search failed: {str(e)}")


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

