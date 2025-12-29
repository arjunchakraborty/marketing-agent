"""Campaign targeting endpoints."""
from fastapi import APIRouter, HTTPException

from ...schemas.campaigns import (
    CampaignPerformanceResponse,
    TargetCampaignRequest,
    TargetCampaignResponse,
    TargetingAnalysisRequest,
    TargetingAnalysisResponse,
)
from ...services.campaign_targeting_service import CampaignTargetingService

router = APIRouter()
targeting_service = CampaignTargetingService()


@router.get("/segments", summary="Get available audience segments")
async def get_segments():
    """Get list of available audience segments for targeting."""
    segments = targeting_service.get_available_segments()
    return {"segments": [seg.model_dump() for seg in segments]}


@router.post("/target", response_model=TargetCampaignResponse, summary="Create targeted campaign")
async def create_targeted_campaign(payload: TargetCampaignRequest) -> TargetCampaignResponse:
    """
    Create a targeted campaign for specific audience segments.
    
    The campaign will be created with the specified segments and targeting criteria.
    """
    try:
        result = targeting_service.create_targeted_campaign(
            campaign_name=payload.campaign_name,
            segment_ids=payload.segment_ids,
            channel=payload.channel,
            objective=payload.objective,
            constraints=payload.constraints,
            products=payload.products,
            product_images=payload.product_images,
        )

        from ...schemas.campaigns import AudienceSegment

        segments = [AudienceSegment(**seg) for seg in result["segments"]]

        return TargetCampaignResponse(
            campaign_id=result["campaign_id"],
            campaign_name=result["campaign_name"],
            segments=segments,
            estimated_reach=result["estimated_reach"],
            status=result["status"],
            created_at=result["created_at"],
            product_images=result.get("product_images"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Campaign creation failed: {str(e)}")


@router.post("/analyze-targeting", response_model=TargetingAnalysisResponse, summary="Analyze targeting effectiveness")
async def analyze_targeting(payload: TargetingAnalysisRequest) -> TargetingAnalysisResponse:
    """
    Analyze the effectiveness of campaign targeting.
    
    Returns performance metrics by segment and optimization recommendations.
    """
    try:
        result = targeting_service.analyze_targeting(
            campaign_id=payload.campaign_id,
            segment_ids=payload.segment_ids,
            date_range=payload.date_range,
        )

        return TargetingAnalysisResponse(
            campaign_id=result.get("campaign_id"),
            segment_performance=result["segment_performance"],
            recommendations=result["recommendations"],
            summary=result["summary"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Targeting analysis failed: {str(e)}")


@router.get("/{campaign_id}/performance", response_model=CampaignPerformanceResponse, summary="Get campaign performance by segment")
async def get_campaign_performance(campaign_id: str) -> CampaignPerformanceResponse:
    """
    Get detailed performance metrics for a campaign, broken down by audience segment.
    """
    try:
        result = targeting_service.get_campaign_performance(campaign_id)

        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])

        return CampaignPerformanceResponse(
            campaign_id=result["campaign_id"],
            overall_performance=result["overall_performance"],
            segment_performance=result["segment_performance"],
            top_performing_segments=result["top_performing_segments"],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get campaign performance: {str(e)}")

