"""Image analysis endpoints for detecting visual elements in email campaigns."""
import base64
from typing import List, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from ...schemas.email_features import (
    EmailFeatureDetectionRequest,
    EmailFeatureDetectionResponse,
)
from ...schemas.image_analysis import (
    CampaignImageBatchRequest,
    CampaignImageBatchResponse,
    ImageAnalysisRequest,
    ImageAnalysisResponse,
    VisualElementCorrelationRequest,
    VisualElementCorrelationResponse,
)
from ...services.bulk_image_analysis_service import analyze_all_images_in_directory
from ...services.email_feature_detector import EmailFeatureDetector
from ...services.image_analysis_service import ImageAnalysisService

router = APIRouter()
image_analysis_service = ImageAnalysisService()
feature_detector = EmailFeatureDetector()


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


@router.post(
    "/detect-features",
    response_model=EmailFeatureDetectionResponse,
    summary="Detect and catalog email features",
)
async def detect_email_features(payload: EmailFeatureDetectionRequest) -> EmailFeatureDetectionResponse:
    """
    Detect key email features (CTAs, promotions, products, etc.).
    Features are cataloged by category for correlation with campaign performance.
    Note: Feature detection is currently disabled and returns empty results.
    """
    try:
        result = feature_detector.detect_features(
            image_url=payload.image_url,
            image_base64=payload.image_base64,
            image_path=payload.image_path,
            custom_prompts=payload.custom_prompts,
            campaign_id=payload.campaign_id,
        )

        from ...schemas.email_features import EmailFeature, FeatureCatalog

        # Convert features to schema format
        features = []
        for f in result.get("features", []):
            from ...schemas.email_features import BoundingBox

            bbox = None
            if f.get("bbox"):
                bbox_data = f["bbox"]
                if isinstance(bbox_data, dict):
                    bbox = BoundingBox(
                        x_min=bbox_data.get("x_min", 0),
                        y_min=bbox_data.get("y_min", 0),
                        x_max=bbox_data.get("x_max", 0),
                        y_max=bbox_data.get("y_max", 0),
                        width=bbox_data.get("width"),
                        height=bbox_data.get("height"),
                    )

            features.append(
                EmailFeature(
                    feature_type=f.get("feature_type", "unknown"),
                    feature_category=f.get("feature_category", "content"),
                    confidence=f.get("confidence", 0.0),
                    bbox=bbox,
                    position=f.get("position"),
                    text_content=f.get("text_content"),
                    color=f.get("color"),
                    metadata=f.get("metadata"),
                )
            )

        # Convert catalog - features in catalog are already dictionaries, convert them properly
        catalog_data = result.get("feature_catalog", {})
        
        def convert_feature_dict(f: dict) -> EmailFeature:
            """Convert feature dictionary to EmailFeature schema."""
            bbox = None
            if f.get("bbox"):
                bbox_data = f["bbox"]
                if isinstance(bbox_data, dict):
                    bbox = BoundingBox(
                        x_min=bbox_data.get("x_min", 0),
                        y_min=bbox_data.get("y_min", 0),
                        x_max=bbox_data.get("x_max", 0),
                        y_max=bbox_data.get("y_max", 0),
                        width=bbox_data.get("width"),
                        height=bbox_data.get("height"),
                    )
            
            return EmailFeature(
                feature_type=f.get("feature_type", "unknown"),
                feature_category=f.get("feature_category", "content"),
                confidence=f.get("confidence", 0.0),
                bbox=bbox,
                position=f.get("position"),
                text_content=f.get("text_content"),
                color=f.get("color"),
                metadata=f.get("metadata"),
            )
        
        catalog = FeatureCatalog(
            cta_buttons=[convert_feature_dict(f) for f in catalog_data.get("cta_buttons", [])],
            promotions=[convert_feature_dict(f) for f in catalog_data.get("promotions", [])],
            products=[convert_feature_dict(f) for f in catalog_data.get("products", [])],
            content=[convert_feature_dict(f) for f in catalog_data.get("content", [])],
            branding=[convert_feature_dict(f) for f in catalog_data.get("branding", [])],
            social_proof=[convert_feature_dict(f) for f in catalog_data.get("social_proof", [])],
            urgency=[convert_feature_dict(f) for f in catalog_data.get("urgency", [])],
            structure=[convert_feature_dict(f) for f in catalog_data.get("structure", [])],
            summary=catalog_data.get("summary", {}),
        )

        return EmailFeatureDetectionResponse(
            campaign_id=payload.campaign_id,
            features=features,
            feature_catalog=catalog,
            total_features_detected=result.get("total_features_detected", 0),
            error=result.get("error"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feature detection failed: {str(e)}")


@router.post("/bulk-analyze", summary="Bulk analyze all images in a directory")
async def bulk_analyze_images(
    directory_path: str,
    experiment_run_id: Optional[str] = None,
    skip_existing: bool = True,
) -> JSONResponse:
    """
    Analyze all images in a directory and store results in database.
    
    Images are matched to campaigns based on campaign_id extracted from filenames.
    Results are stored in the database and can be reused in experiments.
    """
    try:
        summary = analyze_all_images_in_directory(
            directory_path=directory_path,
            experiment_run_id=experiment_run_id,
            skip_existing=skip_existing,
        )
        
        return JSONResponse(content=summary)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk analysis failed: {str(e)}")


@router.post("/batch-upload", summary="Batch upload multiple images")
async def batch_upload_images(
    files: List[UploadFile] = File(...),
    campaign_id: Optional[str] = None,
    campaign_name: Optional[str] = None,
) -> JSONResponse:
    """
    Upload and analyze multiple campaign images in a single batch operation.
    """
    results = []
    errors = []
    
    for file in files:
        if not file.content_type or not file.content_type.startswith("image/"):
            errors.append(f"{file.filename}: Not an image file")
            continue
        
        try:
            image_data = await file.read()
            image_base64 = base64.b64encode(image_data).decode("utf-8")
            
            result = image_analysis_service.analyze_image(
                image_base64=image_base64,
                campaign_id=campaign_id,
                campaign_name=campaign_name,
                analysis_type="full",
            )
            
            results.append({
                "filename": file.filename,
                "image_id": result["image_id"],
                "campaign_id": result.get("campaign_id"),
                "visual_elements_count": len(result.get("visual_elements", [])),
            })
        except Exception as e:
            errors.append(f"{file.filename}: {str(e)}")
    
    return JSONResponse(content={
        "total_uploaded": len(files),
        "successful": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors if errors else None,
    })


@router.post("/generate", summary="Generate campaign image based on insights")
async def generate_campaign_image(
    prompt: str,
    campaign_id: Optional[str] = None,
    style_reference: Optional[str] = None,
) -> JSONResponse:
    """
    Generate a new campaign image using LLM insights and design specifications.
    
    This endpoint uses LLM to generate image specifications based on successful campaign patterns.
    """
    try:
        from ...services.intelligence_service import IntelligenceService
        
        intelligence_service = IntelligenceService()
        
        # Generate image description/specs using LLM
        # In production, this would integrate with image generation APIs
        image_spec = {
            "description": f"Campaign image: {prompt}",
            "style": style_reference or "modern marketing",
            "colors": ["#3B82F6", "#8B5CF6"],
            "elements": ["CTA button", "product showcase", "promotional text"],
            "layout": "centered",
        }
        
        # For now, return the specification
        # In production, this would call an image generation service
        return JSONResponse(content={
            "image_spec": image_spec,
            "message": "Image specification generated. In production, this would generate the actual image.",
            "campaign_id": campaign_id,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")

