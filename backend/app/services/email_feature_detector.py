"""Email feature detection service for detecting key email elements."""
from __future__ import annotations

import base64
import json
import logging
from io import BytesIO
from typing import Any, Dict, List, Optional



from ..core.config import settings

logger = logging.getLogger(__name__)

# Key email features to detect
EMAIL_FEATURE_PROMPTS = [
    "call to action button",
    "CTA button",
    "shop now button",
    "buy now button",
    "discount badge",
    "sale badge",
    "promotion badge",
    "percentage off",
    "product image",
    "product photo",
    "headline",
    "main headline",
    "subject line",
    "email header",
    "email footer",
    "logo",
    "company logo",
    "brand logo",
    "social media icon",
    "social proof",
    "testimonial",
    "customer review",
    "star rating",
    "countdown timer",
    "limited time offer",
    "urgency indicator",
    "price",
    "discount price",
    "original price",
    "navigation menu",
    "email body text",
    "email section",
]


class EmailFeatureDetector:
    """Service for detecting and cataloging key email features."""

    def __init__(self):
        """Initialize feature detector (currently disabled - no model initialization)."""
        self.model = None
        logger.info("EmailFeatureDetector initialized (feature detection disabled)")

    def detect_features(
        self,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
        image_path: Optional[str] = None,
        custom_prompts: Optional[List[str]] = None,
        campaign_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Detect email features in an image (currently disabled - returns empty results).
        
        Args:
            image_url: URL of the image to analyze
            image_base64: Base64-encoded image data
            image_path: Local file path to image
            custom_prompts: Additional text prompts for detection
            campaign_id: Campaign ID for context
            
        Returns:
            Dictionary containing detected features with bounding boxes, confidence scores, and metadata
        """
        # Feature detection is currently disabled
        logger.debug("Email feature detection is disabled - returning empty results")
        return {
            "features": [],
            "feature_catalog": {
                "cta_buttons": [],
                "promotions": [],
                "products": [],
                "content": [],
                "branding": [],
                "social_proof": [],
                "urgency": [],
                "structure": [],
                "summary": {
                    "total_cta_buttons": 0,
                    "total_promotions": 0,
                    "total_products": 0,
                    "total_content_elements": 0,
                    "total_branding_elements": 0,
                    "total_social_proof": 0,
                    "total_urgency_indicators": 0,
                    "total_structure_elements": 0,
                },
            },
            "total_features_detected": 0,
        }

    def _load_image(
        self,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
        image_path: Optional[str] = None,
    ) -> Optional[Image.Image]:
        """Load image from URL, base64, or file path."""
        try:
            if image_path:
                return Image.open(image_path).convert("RGB")
            elif image_base64:
                # Remove data URL prefix if present
                if image_base64.startswith("data:image"):
                    image_base64 = image_base64.split(",", 1)[1] if "," in image_base64 else image_base64
                image_data = base64.b64decode(image_base64)
                return Image.open(BytesIO(image_data)).convert("RGB")
            elif image_url:
                response = httpx.get(image_url, timeout=30.0)
                response.raise_for_status()
                return Image.open(BytesIO(response.content)).convert("RGB")
            return None
        except Exception as e:
            logger.error(f"Failed to load image: {str(e)}")
            return None

    def _detect_with_model(self, image: Image.Image, prompts: List[str]) -> List[Dict[str, Any]]:
        """Detect features using model (currently unused - feature detection disabled)."""
        try:
            # Convert PIL image to format expected by model
            # This method is not currently used as feature detection is disabled
            if hasattr(self.model, "infer"):
                # Roboflow Inference API format
                import io

                img_bytes = io.BytesIO()
                image.save(img_bytes, format="PNG")
                img_bytes.seek(0)

                results = self.model.infer(
                    {
                        "image": {
                            "type": "base64",
                            "value": base64.b64encode(img_bytes.read()).decode("utf-8"),
                        },
                        "text": prompts,
                    }
                )
                return self._parse_inference_results(results, prompts)
            else:
                # Direct model format (not currently used)
                return self._detect_with_direct_model(image, prompts)
        except Exception as e:
            logger.error(f"Model detection failed: {str(e)}", exc_info=True)
            raise

    def _detect_with_direct_model(self, image: Image.Image, prompts: List[str]) -> List[Dict[str, Any]]:
        """Detect features using direct model (currently unused - feature detection disabled)."""
        # This method is not currently used as feature detection is disabled
        logger.debug("Direct model detection not used (feature detection disabled)")
        return []

    def _detect_with_api(self, image: Image.Image, prompts: List[str]) -> List[Dict[str, Any]]:
        """
        Fallback detection using LLM-based analysis (currently unused - feature detection disabled).
        Uses vision models to detect features based on prompts.
        """
        logger.info("Using LLM-based fallback for feature detection")
        
        try:
            from ..services.llm_service import LLMService
            from ..core.config import settings
            
            # Try to use vision-capable LLM
            llm_service = None
            for provider in ["ollama", "openai"]:
                try:
                    llm_service = LLMService(provider=provider)
                    if provider == "ollama" or (provider == "openai" and settings.openai_api_key):
                        break
                except Exception:
                    continue
            
            if not llm_service:
                logger.warning("No LLM service available for feature detection")
                return []
            
            # Convert image to base64
            import io
            img_bytes = io.BytesIO()
            image.save(img_bytes, format="PNG")
            img_bytes.seek(0)
            image_base64 = base64.b64encode(img_bytes.read()).decode("utf-8")
            
            # Create prompt for feature detection
            prompt = f"""Analyze this email campaign image and detect the following features with their positions and details:

Features to detect: {', '.join(prompts[:10])}

For each detected feature, provide:
1. Feature type (from the list above)
2. Approximate position (top-left, top-center, top-right, middle-left, middle-center, middle-right, bottom-left, bottom-center, bottom-right)
3. Bounding box coordinates (x_min, y_min, x_max, y_max as percentages 0-100)
4. Confidence level (0-1)
5. Text content if applicable
6. Color if applicable

Return as JSON array with structure:
[
  {{
    "feature_type": "call to action button",
    "position": "middle-center",
    "bbox": {{"x_min": 30, "y_min": 50, "x_max": 70, "y_max": 60}},
    "confidence": 0.9,
    "text_content": "Shop Now",
    "color": "#FF5733"
  }}
]"""
            
            # Use vision model
            if llm_service.provider == "ollama":
                client = llm_service._get_ollama_client()
                response = client.post(
                    "/api/chat",
                    json={
                        "model": settings.ollama_vision_model,
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt,
                                "images": [image_base64],
                            }
                        ],
                        "stream": False,
                        "options": {
                            "temperature": 0.3,
                            "num_predict": 2000,
                        },
                    },
                )
                response.raise_for_status()
                result = response.json()
                content = result["message"]["content"].strip()
            elif llm_service.provider == "openai":
                from openai import OpenAI
                client = OpenAI(api_key=settings.openai_api_key)
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}},
                            ],
                        }
                    ],
                    max_tokens=2000,
                    temperature=0.3,
                )
                content = response.choices[0].message.content.strip()
            else:
                return []
            
            # Parse JSON response
            try:
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                features = json.loads(content)
                if isinstance(features, list):
                    return features
                elif isinstance(features, dict) and "features" in features:
                    return features["features"]
                return []
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse LLM feature detection response: {content[:200]}")
                return []
                
        except Exception as e:
            logger.error(f"LLM-based feature detection failed: {str(e)}", exc_info=True)
            return []

    def _parse_inference_results(self, results: Any, prompts: List[str]) -> List[Dict[str, Any]]:
        """Parse inference results into structured format."""
        features = []
        
        if isinstance(results, dict):
            # Roboflow Inference format
            predictions = results.get("predictions", [])
            for pred in predictions:
                features.append({
                    "feature_type": pred.get("class", "unknown"),
                    "confidence": pred.get("confidence", 0.0),
                    "bbox": pred.get("bbox", {}),
                    "prompt_matched": pred.get("text", ""),
                })
        elif isinstance(results, list):
            # Direct format
            for result in results:
                if isinstance(result, dict):
                    features.append(result)
        
        return features

    def _catalog_features(self, features: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Catalog detected features into structured categories.
        
        Categories:
        - cta_buttons: Call-to-action buttons
        - promotions: Discount badges, sale indicators
        - products: Product images
        - content: Headlines, text content
        - branding: Logos, brand elements
        - social_proof: Testimonials, reviews, ratings
        - urgency: Countdown timers, limited offers
        - structure: Header, footer, sections
        """
        catalog = {
            "cta_buttons": [],
            "promotions": [],
            "products": [],
            "content": [],
            "branding": [],
            "social_proof": [],
            "urgency": [],
            "structure": [],
        }

        for feature in features:
            feature_type = feature.get("feature_type", "").lower()
            prompt_matched = feature.get("prompt_matched", "").lower()
            
            # Categorize based on feature type and prompt
            if any(keyword in feature_type or keyword in prompt_matched for keyword in ["button", "cta", "shop now", "buy now"]):
                catalog["cta_buttons"].append(feature)
            elif any(keyword in feature_type or keyword in prompt_matched for keyword in ["discount", "sale", "badge", "promotion", "percentage"]):
                catalog["promotions"].append(feature)
            elif any(keyword in feature_type or keyword in prompt_matched for keyword in ["product", "item"]):
                catalog["products"].append(feature)
            elif any(keyword in feature_type or keyword in prompt_matched for keyword in ["headline", "text", "subject", "body"]):
                catalog["content"].append(feature)
            elif any(keyword in feature_type or keyword in prompt_matched for keyword in ["logo", "brand"]):
                catalog["branding"].append(feature)
            elif any(keyword in feature_type or keyword in prompt_matched for keyword in ["testimonial", "review", "rating", "social proof"]):
                catalog["social_proof"].append(feature)
            elif any(keyword in feature_type or keyword in prompt_matched for keyword in ["timer", "countdown", "urgency", "limited time"]):
                catalog["urgency"].append(feature)
            elif any(keyword in feature_type or keyword in prompt_matched for keyword in ["header", "footer", "section", "navigation"]):
                catalog["structure"].append(feature)
            else:
                # Default to content if unclear
                catalog["content"].append(feature)

        # Add summary statistics
        catalog["summary"] = {
            "total_cta_buttons": len(catalog["cta_buttons"]),
            "total_promotions": len(catalog["promotions"]),
            "total_products": len(catalog["products"]),
            "total_content_elements": len(catalog["content"]),
            "total_branding_elements": len(catalog["branding"]),
            "total_social_proof": len(catalog["social_proof"]),
            "total_urgency_indicators": len(catalog["urgency"]),
            "total_structure_elements": len(catalog["structure"]),
        }

        return catalog

