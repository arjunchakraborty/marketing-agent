"""Image analysis endpoints for detecting visual elements in email campaigns."""
import base64
from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from ...schemas.image_analysis import (
    CampaignImageBatchRequest,
    CampaignImageBatchResponse,
    ImageAnalysisRequest,
    ImageAnalysisResponse,
    VisualElementCorrelationRequest,
    VisualElementCorrelationResponse,
)
from ...services.image_analysis_service import ImageAnalysisService

router = APIRouter()
image_analysis_service = ImageAnalysisService()


@router.post("/analyze", response_model=ImageAnalysisResponse, summary="Analyze an image for visual elements")
async def analyze_image(payload: ImageAnalysisRequest) -> ImageAnalysisResponse:
    """Analyze an image URL or base64 data to detect visual elements, colors, and composition."""
    try:
        result = image_analysis_service.analyze_image(
            image_url=payload.image_url,
            image_base64=payload.image_base64,
            campaign_id=payload.campaign_id,
            campaign_name=payload.campaign_name,
            analysis_type=payload.analysis_type,
        )

        # Convert visual elements to schema format
        from ...schemas.image_analysis import VisualElement

        visual_elements = [
            VisualElement(
                element_type=e.get("element_type", "unknown"),
                description=e.get("description", ""),
                position=e.get("position"),
                confidence=e.get("confidence"),
                color_palette=e.get("color_palette"),
                text_content=e.get("text_content"),
            )
            for e in result.get("visual_elements", [])
        ]

        return ImageAnalysisResponse(
            image_id=result["image_id"],
            campaign_id=result.get("campaign_id"),
            visual_elements=visual_elements,
            dominant_colors=result.get("dominant_colors", []),
            composition_analysis=result.get("composition_analysis"),
            text_content=result.get("text_content"),
            overall_description=result.get("overall_description", "Analysis completed"),
            marketing_relevance=result.get("marketing_relevance"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {str(e)}")


@router.post("/analyze/upload", response_model=ImageAnalysisResponse, summary="Upload and analyze an image file")
async def analyze_uploaded_image(
    file: UploadFile = File(...),
    campaign_id: Optional[str] = None,
    campaign_name: Optional[str] = None,
    analysis_type: str = "full",
) -> ImageAnalysisResponse:
    """Upload an image file and analyze it for visual elements."""
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    try:
        # Read file content
        image_data = await file.read()
        # Encode to base64
        image_base64 = base64.b64encode(image_data).decode("utf-8")

        result = image_analysis_service.analyze_image(
            image_base64=image_base64,
            campaign_id=campaign_id,
            campaign_name=campaign_name,
            analysis_type=analysis_type,
        )

        from ...schemas.image_analysis import VisualElement

        visual_elements = [
            VisualElement(
                element_type=e.get("element_type", "unknown"),
                description=e.get("description", ""),
                position=e.get("position"),
                confidence=e.get("confidence"),
                color_palette=e.get("color_palette"),
                text_content=e.get("text_content"),
            )
            for e in result.get("visual_elements", [])
        ]

        return ImageAnalysisResponse(
            image_id=result["image_id"],
            campaign_id=result.get("campaign_id"),
            visual_elements=visual_elements,
            dominant_colors=result.get("dominant_colors", []),
            composition_analysis=result.get("composition_analysis"),
            text_content=result.get("text_content"),
            overall_description=result.get("overall_description", "Analysis completed"),
            marketing_relevance=result.get("marketing_relevance"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {str(e)}")


@router.post(
    "/correlate",
    response_model=VisualElementCorrelationResponse,
    summary="Correlate visual elements with campaign performance",
)
async def correlate_visual_elements(payload: VisualElementCorrelationRequest) -> VisualElementCorrelationResponse:
    """Correlate visual elements with campaign performance metrics to identify impactful elements."""
    try:
        result = image_analysis_service.correlate_visual_elements_with_performance(
            visual_elements=payload.visual_elements,
            date_range=payload.date_range,
            min_campaigns=payload.min_campaigns,
        )

        from ...schemas.image_analysis import VisualElementCorrelation

        correlations = [
            VisualElementCorrelation(
                element_type=c.get("element_type", "unknown"),
                element_description=c.get("element_description", ""),
                average_performance=c.get("average_performance", {}),
                performance_impact=c.get("performance_impact", ""),
                recommendation=c.get("recommendation", ""),
            )
            for c in result.get("correlations", [])
        ]

        return VisualElementCorrelationResponse(
            correlations=correlations,
            summary=result.get("summary", "Correlation analysis completed"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Correlation analysis failed: {str(e)}")


@router.post(
    "/batch",
    response_model=CampaignImageBatchResponse,
    summary="Analyze multiple campaign images in batch",
)
async def analyze_campaign_images_batch(payload: CampaignImageBatchRequest) -> CampaignImageBatchResponse:
    """Analyze multiple campaign images in a batch operation."""
    # This is a placeholder - in production, you'd fetch image URLs from campaign data
    # For now, return a response indicating batch processing would be implemented
    return CampaignImageBatchResponse(
        analyses=[],
        total_analyzed=0,
    )

