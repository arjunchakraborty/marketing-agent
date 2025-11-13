"""Image analysis service for detecting and understanding visual elements in email campaigns."""
from __future__ import annotations

import base64
import json
import uuid
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx

from ..core.config import settings
from .llm_service import LLMService


class ImageAnalysisService:
    """Service for analyzing marketing email images and detecting visual elements."""

    def __init__(self, llm_provider: Optional[str] = None) -> None:
        self.llm_service: Optional[LLMService] = None
        provider = llm_provider or settings.default_llm_provider
        
        # Try providers in order: specified/configured, then ollama (local), then openai, then anthropic
        providers_to_try = [provider]
        if provider != "ollama":
            providers_to_try.append("ollama")
        if provider != "openai" and settings.openai_api_key:
            providers_to_try.append("openai")
        if provider != "anthropic" and settings.anthropic_api_key:
            providers_to_try.append("anthropic")

        for p in providers_to_try:
            try:
                self.llm_service = LLMService(provider=p)
                break
            except Exception:
                continue

    def analyze_image(
        self,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
        campaign_id: Optional[str] = None,
        campaign_name: Optional[str] = None,
        analysis_type: str = "full",
    ) -> Dict[str, Any]:
        """Analyze an image and detect visual elements."""
        if not image_url and not image_base64:
            raise ValueError("Either image_url or image_base64 must be provided")

        image_id = str(uuid.uuid4())

        # Use OpenAI vision API if available, otherwise fall back to LLM-based analysis
        if self.llm_service and self.llm_service.provider == "openai" and settings.openai_api_key:
            return self._analyze_with_openai_vision(
                image_url, image_base64, image_id, campaign_id, campaign_name, analysis_type
            )
        elif self.llm_service:
            return self._analyze_with_llm(
                image_url, image_base64, image_id, campaign_id, campaign_name, analysis_type
            )
        else:
            return self._analyze_basic(image_url, image_base64, image_id, campaign_id, campaign_name)

    def _analyze_with_openai_vision(
        self,
        image_url: Optional[str],
        image_base64: Optional[str],
        image_id: str,
        campaign_id: Optional[str],
        campaign_name: Optional[str],
        analysis_type: str,
    ) -> Dict[str, Any]:
        """Analyze image using OpenAI Vision API."""
        try:
            from openai import OpenAI

            client = OpenAI(api_key=settings.openai_api_key)

            # Prepare image content
            image_content = []
            if image_url:
                image_content.append({"type": "image_url", "image_url": {"url": image_url}})
            elif image_base64:
                # Ensure base64 data has proper prefix
                if not image_base64.startswith("data:image"):
                    image_content.append(
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                    )
                else:
                    image_content.append({"type": "image_url", "image_url": {"url": image_base64}})

            # Build analysis prompt based on type
            if analysis_type == "visual_elements":
                prompt = """Analyze this marketing email image and identify all visual elements. For each element, provide:
1. Element type (product, text, CTA button, logo, background, etc.)
2. Description
3. Position (if discernible)
4. Dominant colors
5. Text content (if any)

Return as structured JSON with a 'visual_elements' array."""
            elif analysis_type == "colors":
                prompt = """Identify the dominant colors in this marketing email image. List the top 5-7 colors as hex codes or color names. Also analyze the color palette and how it relates to marketing effectiveness."""
            elif analysis_type == "text":
                prompt = """Extract all text content from this marketing email image. Include headlines, body text, CTAs, and any other text elements."""
            elif analysis_type == "composition":
                prompt = """Analyze the composition and layout of this marketing email image. Describe the visual hierarchy, balance, focal points, and overall design structure."""
            else:  # full
                prompt = """Perform a comprehensive analysis of this marketing email image. Include:
1. Overall description
2. All visual elements (products, text, CTAs, logos, etc.) with positions and colors
3. Dominant color palette
4. Composition and layout analysis
5. Extracted text content
6. Marketing-specific insights and recommendations

Return structured JSON with fields: visual_elements (array), dominant_colors (array), composition_analysis (string), text_content (string), overall_description (string), marketing_relevance (string)."""

            if campaign_name:
                prompt += f"\n\nContext: This image is from campaign '{campaign_name}'."

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        *image_content,
                    ],
                }
            ]

            response = client.chat.completions.create(
                model="gpt-4o",  # Use vision-capable model
                messages=messages,
                max_tokens=2000,
                temperature=0.3,
            )

            content = response.choices[0].message.content.strip()

            # Try to parse JSON response
            try:
                if content.startswith("```json"):
                    content = content.split("```json")[1].split("```")[0].strip()
                elif content.startswith("```"):
                    content = content.split("```")[1].split("```")[0].strip()
                
                parsed = json.loads(content)
            except json.JSONDecodeError:
                # If not JSON, create structured response from text
                parsed = {
                    "overall_description": content,
                    "visual_elements": [],
                    "dominant_colors": [],
                    "composition_analysis": None,
                    "text_content": None,
                    "marketing_relevance": None,
                }

            # Normalize response structure
            result = {
                "image_id": image_id,
                "campaign_id": campaign_id,
                "visual_elements": parsed.get("visual_elements", []),
                "dominant_colors": parsed.get("dominant_colors", []),
                "composition_analysis": parsed.get("composition_analysis"),
                "text_content": parsed.get("text_content"),
                "overall_description": parsed.get("overall_description", content),
                "marketing_relevance": parsed.get("marketing_relevance"),
            }

            return result

        except Exception as e:
            return {
                "image_id": image_id,
                "campaign_id": campaign_id,
                "error": f"OpenAI Vision API error: {str(e)}",
                "visual_elements": [],
                "dominant_colors": [],
                "overall_description": "Analysis failed",
            }

    def _analyze_with_llm(
        self,
        image_url: Optional[str],
        image_base64: Optional[str],
        image_id: str,
        campaign_id: Optional[str],
        campaign_name: Optional[str],
        analysis_type: str,
    ) -> Dict[str, Any]:
        """Fallback analysis using LLM text description (for non-vision models)."""
        # For non-vision models, we'd need to describe the image first
        # This is a placeholder - in production, you might use a separate vision service
        return {
            "image_id": image_id,
            "campaign_id": campaign_id,
            "visual_elements": [],
            "dominant_colors": [],
            "overall_description": "Image analysis requires vision-capable model. Please configure OpenAI API key for full analysis.",
            "marketing_relevance": None,
        }

    def _analyze_basic(
        self,
        image_url: Optional[str],
        image_base64: Optional[str],
        image_id: str,
        campaign_id: Optional[str],
        campaign_name: Optional[str],
    ) -> Dict[str, Any]:
        """Basic analysis without LLM (metadata only)."""
        return {
            "image_id": image_id,
            "campaign_id": campaign_id,
            "visual_elements": [],
            "dominant_colors": [],
            "overall_description": "Basic analysis: Image URL/base64 provided but LLM service not configured.",
            "marketing_relevance": None,
        }

    def correlate_visual_elements_with_performance(
        self, visual_elements: List[str], date_range: Optional[Dict[str, str]] = None, min_campaigns: int = 5
    ) -> Dict[str, Any]:
        """Correlate visual elements with campaign performance metrics."""
        if not self.llm_service:
            return {
                "correlations": [],
                "summary": "LLM service not available for correlation analysis.",
            }

        # This would typically query the analytics database to get campaign performance
        # For now, we'll use LLM to generate insights based on the visual elements
        try:
            prompt = f"""Analyze the correlation between these visual elements and marketing campaign performance:

Visual Elements: {', '.join(visual_elements)}

Based on marketing best practices and common patterns, provide:
1. Expected performance impact for each element
2. Recommendations for optimizing campaigns
3. Summary of findings

Return as JSON with correlations array, each containing: element_type, element_description, average_performance (dict), performance_impact (string), recommendation (string)."""

            if date_range:
                prompt += f"\nDate Range: {date_range.get('start')} to {date_range.get('end')}"

            if self.llm_service.provider == "openai":
                client = self.llm_service._get_openai_client()
                response = client.chat.completions.create(
                    model=settings.openai_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.5,
                    max_tokens=1500,
                )
                content = response.choices[0].message.content.strip()
            elif self.llm_service.provider == "anthropic":
                client = self.llm_service._get_anthropic_client()
                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1500,
                    messages=[{"role": "user", "content": prompt}],
                )
                content = response.content[0].text.strip()
            else:  # ollama
                client = self.llm_service._get_ollama_client()
                response = client.post(
                    "/api/chat",
                    json={
                        "model": settings.ollama_model,
                        "messages": [{"role": "user", "content": prompt}],
                        "stream": False,
                        "options": {"temperature": 0.5, "num_predict": 1500},
                    },
                )
                response.raise_for_status()
                result = response.json()
                content = result["message"]["content"].strip()

            # Parse JSON response
            try:
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                parsed = json.loads(content)
            except json.JSONDecodeError:
                parsed = {"correlations": [], "summary": content}

            return {
                "correlations": parsed.get("correlations", []),
                "summary": parsed.get("summary", "Correlation analysis completed."),
            }

        except Exception as e:
            return {
                "correlations": [],
                "summary": f"Correlation analysis failed: {str(e)}",
            }

