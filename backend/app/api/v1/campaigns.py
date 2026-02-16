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
# Import VectorDBService lazily to avoid import errors at startup
try:
    from ...services.vector_db_service import (
        VectorDBService,
        list_all_collections,
        get_product_images_by_names,
    )
    VECTOR_DB_AVAILABLE = True
except Exception:
    VECTOR_DB_AVAILABLE = False
    VectorDBService = None
    list_all_collections = None
    get_product_images_by_names = None

logger = logging.getLogger(__name__)
router = APIRouter()


class VectorSearchRequest(BaseModel):
    """Request to search campaigns in vector database."""
    query: Optional[str] = Field(default="", description="Natural language query to search for campaigns. If empty, returns all documents.")
    collection_name: Optional[str] = Field(default=None, description="Optional collection name (default: UCO_Gear_Campaigns)")
    num_results: int = Field(default=10, description="Number of results to return (only used when query is provided)", ge=1, le=50)
    show_all: bool = Field(default=False, description="If true, return all documents regardless of query")


class VectorSearchResponse(BaseModel):
    """Response from vector database search."""
    campaigns: List[Dict[str, Any]] = Field(default_factory=list, description="List of matching campaigns")
    total_found: int = Field(0, description="Total number of campaigns found")
    query: str = Field(..., description="The search query used")


@router.get("/collections", response_model=List[str], summary="List all available vector database collections")
async def list_collections() -> List[str]:
    """Get a list of all available collections in the vector database."""
    logger.info("Listing all vector database collections")
    
    if not VECTOR_DB_AVAILABLE or list_all_collections is None:
        raise HTTPException(status_code=503, detail="Vector database (ChromaDB) is not available. Please install ChromaDB: pip install chromadb")
    
    try:
        collections = list_all_collections()
        return collections
    except Exception as e:
        logger.exception(f"Failed to list collections: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list collections: {str(e)}")


@router.post("/search", response_model=VectorSearchResponse, summary="Search campaigns in vector database")
async def search_campaigns(payload: VectorSearchRequest) -> VectorSearchResponse:
    """
    Search for campaigns in the vector database using natural language.
    
    If query is empty or show_all is true, returns all documents from the vector database.
    Otherwise, uses semantic similarity to find campaigns that match your query.
    
    Examples:
    - "high performing email campaigns"
    - "campaigns with high conversion rates"
    - "product launch campaigns"
    - "campaigns promoting outdoor gear"
    - "" (empty query) - returns all documents
    """
    query = payload.query or ""
    logger.info(f"Searching campaigns: query={query[:100] if query else '(all documents)'}, collection={payload.collection_name}, show_all={payload.show_all}, num_results={payload.num_results}")
    
    if not VECTOR_DB_AVAILABLE or VectorDBService is None:
        raise HTTPException(status_code=503, detail="Vector database (ChromaDB) is not available. Please install ChromaDB: pip install chromadb")
    
    try:
        collection_name = payload.collection_name or "UCO_Gear_Campaigns"
        vector_db_service = VectorDBService(collection_name=collection_name)
        
        # If show_all is true or query is empty, return all documents
        if payload.show_all or not query.strip():
            all_campaigns = vector_db_service.get_all_campaigns()
            logger.info(f"Retrieved {len(all_campaigns)} campaigns from vector database (all documents)")
        else:
            # Perform semantic search
            all_campaigns = vector_db_service.search_similar_campaigns(
                query_text=query,
                n_results=payload.num_results,
            )
            logger.info(f"Found {len(all_campaigns)} campaigns matching query")
        
        # Promote image analysis info from metadata to top-level for easy frontend access
        for campaign in all_campaigns:
            metadata = campaign.get("metadata") or {}
            campaign["has_image_analysis"] = bool(metadata.get("has_image_analysis", False))
            campaign["image_analysis_count"] = int(metadata.get("total_image_analyses", 0))
        
        return VectorSearchResponse(
            campaigns=all_campaigns,
            total_found=len(all_campaigns),
            query=query or "(all documents)" if (payload.show_all or not query.strip()) else query,
        )
    except Exception as e:
        logger.exception(f"Failed to search campaigns: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Campaign search failed: {str(e)}")


def _derive_generation_inputs_from_experiment(exp: Any) -> Dict[str, Any]:
    """Build campaign generation inputs from experiment details and associated product (text + image). No campaign search."""
    results = exp.experiment_run.results_summary or {}
    if not isinstance(results, dict):
        results = {}

    # Products: from campaign_analyses.products_promoted and results_summary
    products_set = set()
    for ca in exp.campaign_analyses or []:
        for p in (ca.products_promoted or []):
            if p and isinstance(p, str):
                products_set.add(p.strip())
    for p in (results.get("products_promoted") or []):
        if p and isinstance(p, str):
            products_set.add(p.strip())
    products = list(products_set)[:10]

    # Product images: from image_analyses
    product_images = []
    for ia in exp.image_analyses or []:
        path = getattr(ia, "image_path", None)
        if path and path not in product_images:
            product_images.append(path)
    product_images = product_images[:10]

    # Objective, key_message, design_guidance: from experiment insights (recommendations, prompts, key_features, patterns)
    parts = []
    if results.get("summary"):
        parts.append(str(results["summary"]))
    for key in ("recommendations", "hero_image_prompts", "text_prompts", "call_to_action_prompts"):
        vals = results.get(key)
        if isinstance(vals, list) and vals:
            parts.append("\n".join(f"• {v}" for v in vals[:5]))
    key_features = results.get("key_features") or []
    if isinstance(key_features, list) and key_features:
        parts.append("Key features: " + ", ".join(str(f) for f in key_features[:7]))
    patterns = results.get("patterns") or {}
    if isinstance(patterns, dict) and patterns:
        pattern_strs = [f"{k}: {v}" for k, v in patterns.items() if v]
        if pattern_strs:
            parts.append("Patterns: " + "; ".join(pattern_strs))
    context = "\n\n".join(p for p in parts if p).strip() or "Generate email campaign based on experiment insights."
    objective = context[:2000]
    key_message = context[:1500]
    design_guidance = context[:1500]

    # product_context is not derived here; it is looked up inside generate_email_campaign from the user-selected products only
    return {
        "objective": objective,
        "products": products if products else None,
        "product_images": product_images if product_images else None,
        "key_message": key_message,
        "design_guidance": design_guidance,
        "use_past_campaigns": False,
    }


@router.post("/generate", response_model=EmailCampaignResponse, summary="Generate a new email campaign")
async def generate_email_campaign(payload: EmailCampaignGenerationRequest) -> EmailCampaignResponse:
    """
    Generate a new email campaign.

    When experiment_run_id is set: fetch that experiment's details and associated product (text and image),
    then create campaign content from that only (no campaign search).

    Otherwise: generate using provided fields and optional RAG from past campaigns.
    """
    logger.info(f"Generating email campaign: objective={payload.objective[:80] if payload.objective else 'N/A'}, experiment_run_id={payload.experiment_run_id}, use_past_campaigns={payload.use_past_campaigns}")

    try:
        campaign_name = payload.campaign_name
        objective = payload.objective
        audience_segment = payload.audience_segment
        products = payload.products
        product_context = payload.product_context
        product_images = payload.product_images
        tone = payload.tone or "professional"
        key_message = payload.key_message
        call_to_action = payload.call_to_action
        include_promotion = payload.include_promotion
        promotion_details = payload.promotion_details
        subject_line_suggestions = payload.subject_line_suggestions
        include_preview_text = payload.include_preview_text
        design_guidance = payload.design_guidance
        use_past_campaigns = payload.use_past_campaigns
        num_similar_campaigns = payload.num_similar_campaigns
        generate_hero_image = payload.generate_hero_image
        hero_image_prompt = payload.hero_image_prompt

        if payload.experiment_run_id:
            from .experiments import get_experiment_results
            exp = await get_experiment_results(payload.experiment_run_id)
            derived = _derive_generation_inputs_from_experiment(exp)
            # Use user-provided objective if they typed one; otherwise fall back to experiment-derived
            if not objective or not objective.strip():
                objective = derived["objective"]
            if not products and derived.get("products") is not None:
                products = derived["products"]
            if not key_message and derived.get("key_message"):
                key_message = derived["key_message"]
            if not design_guidance and derived.get("design_guidance"):
                design_guidance = derived["design_guidance"]
            use_past_campaigns = False
        else:
            if not objective or not objective.strip():
                raise HTTPException(status_code=400, detail="objective is required when not using experiment_run_id")

        # product_context is looked up inside the campaign generation service from the selected products only

        # Pull product images from vector DB based on selected product names
        if products and get_product_images_by_names:
            product_images = get_product_images_by_names(products)
            logger.info(f"Pulled {len(product_images)} product images from vector DB for {len(products)} products")
        else:
            product_images = product_images or []

        logger.info(f"Generating campaign: products={len(products or [])}, product_images={len(product_images)}")

        service = CampaignGenerationService()
        campaign = service.generate_email_campaign(
            campaign_name=campaign_name,
            objective=objective,
            audience_segment=audience_segment,
            products=products,
            product_context=product_context,
            product_images=product_images,
            tone=tone,
            key_message=key_message,
            call_to_action=call_to_action,
            include_promotion=include_promotion,
            promotion_details=promotion_details,
            subject_line_suggestions=subject_line_suggestions,
            include_preview_text=include_preview_text,
            design_guidance=design_guidance,
            use_past_campaigns=use_past_campaigns,
            num_similar_campaigns=num_similar_campaigns,
            generate_hero_image=generate_hero_image,
            hero_image_prompt=hero_image_prompt,
        )

        logger.info(f"Successfully generated campaign: campaign_id={campaign.campaign_id}")
        return campaign
    except HTTPException:
        raise
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

