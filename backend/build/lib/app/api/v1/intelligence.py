"""Intelligence and recommendation endpoints leveraging LLM workflows."""
from fastapi import APIRouter

from ...schemas.intelligence import (
    CampaignRecommendation,
    CampaignRecommendationRequest,
    CampaignRecommendationResponse,
    InsightSummaryRequest,
    InsightSummaryResponse,
)
from ...services.intelligence_service import IntelligenceService

router = APIRouter()
intelligence_service = IntelligenceService()


@router.post("/insights", response_model=InsightSummaryResponse, summary="Summarize analytics insights")
async def summarize_insights(payload: InsightSummaryRequest) -> InsightSummaryResponse:
    """Generate narrative summary from analytics signals using LLM."""
    summary = intelligence_service.summarize_insights(payload.signals, payload.context)
    follow_ups = ["Review campaign performance", "Analyze customer segments", "Optimize ad spend"]
    return InsightSummaryResponse(summary=summary, follow_up_actions=follow_ups)


@router.post("/campaigns", response_model=CampaignRecommendationResponse, summary="Generate campaign recommendations")
async def recommend_campaigns(payload: CampaignRecommendationRequest) -> CampaignRecommendationResponse:
    """Generate campaign recommendations using LLM workflows."""
    campaigns_data = intelligence_service.recommend_campaigns(
        payload.objectives, payload.audience_segments, payload.constraints
    )
    recommendations = []
    for c in campaigns_data:
        uplift_str = c.get("expected_uplift", "0%")
        if isinstance(uplift_str, str):
            uplift_value = float(uplift_str.rstrip("%")) if uplift_str.rstrip("%").replace(".", "").isdigit() else 0.0
        else:
            uplift_value = float(uplift_str) if uplift_str else 0.0

        recommendations.append(
            CampaignRecommendation(
                name=c.get("name", "Unnamed Campaign"),
                channel=c.get("channel", "Unknown"),
                expected_uplift=uplift_value,
                talking_points=c.get("talking_points", []),
            )
        )
    rationale = f"Generated {len(recommendations)} campaign recommendations based on {len(payload.objectives)} objectives and {len(payload.audience_segments)} audience segments."
    return CampaignRecommendationResponse(recommendations=recommendations, rationale=rationale)
