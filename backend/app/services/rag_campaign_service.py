"""RAG service for retrieving insights from past campaigns."""
import json
import logging
from typing import Any, Dict, List, Optional

from ..core.config import settings
from .vector_db_service import VectorDBService

logger = logging.getLogger(__name__)


class RAGCampaignService:
    """Service for retrieving campaign insights using RAG."""

    def __init__(self) -> None:
        """Initialize the RAG campaign service."""
        self.vector_db_service = None
        if settings.enable_vector_search:
            try:
                self.vector_db_service = VectorDBService(collection_name="klaviyo_campaigns")
                logger.info("RAG Campaign Service initialized with vector DB")
            except Exception as e:
                logger.warning(f"Vector DB not available for RAG: {str(e)}")
        else:
            logger.info("Vector search disabled, RAG features will be limited")

    def retrieve_similar_campaigns(
        self,
        query: str,
        objective: Optional[str] = None,
        products: Optional[List[str]] = None,
        tone: Optional[str] = None,
        num_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve similar past campaigns using RAG.
        
        Args:
            query: Search query (objective, products, etc.)
            objective: Campaign objective
            products: List of products
            tone: Desired tone
            num_results: Number of results to return
            
        Returns:
            List of similar campaign analyses with insights
        """
        if not self.vector_db_service:
            logger.warning("Vector DB not available, returning empty results")
            return []

        # Build search query
        search_terms = [query]
        if objective:
            search_terms.append(f"objective: {objective}")
        if products:
            search_terms.append(f"products: {', '.join(products)}")
        if tone:
            search_terms.append(f"tone: {tone}")

        search_query = " ".join(search_terms)

        try:
            similar_campaigns = self.vector_db_service.search_similar_campaigns(
                query_text=search_query,
                n_results=num_results,
            )

            logger.info(f"Retrieved {len(similar_campaigns)} similar campaigns")
            return similar_campaigns
        except Exception as e:
            logger.error(f"Failed to retrieve similar campaigns: {str(e)}", exc_info=True)
            return []

    def extract_campaign_insights(
        self,
        campaign_analyses: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Extract insights from past campaign analyses.
        
        Args:
            campaign_analyses: List of campaign analysis dictionaries
            
        Returns:
            Dictionary with extracted insights (tone, colors, text patterns, etc.)
        """
        insights = {
            "tones": [],
            "color_palettes": [],
            "text_patterns": [],
            "cta_styles": [],
            "subject_line_patterns": [],
            "visual_elements": [],
            "successful_elements": [],
        }

        for campaign_data in campaign_analyses:
            analysis = campaign_data.get("analysis", {})
            metadata = campaign_data.get("metadata", {})

            # Extract from images
            images = analysis.get("images", [])
            for img_data in images:
                img_analysis = img_data.get("analysis", {}) if "analysis" in img_data else img_data

                # Extract colors
                if "dominant_colors" in img_analysis:
                    colors = img_analysis["dominant_colors"]
                    if isinstance(colors, list):
                        for color in colors[:3]:
                            if isinstance(color, dict):
                                insights["color_palettes"].append(color.get("color", str(color)))
                            else:
                                insights["color_palettes"].append(str(color))

                # Extract visual elements
                if "visual_elements" in img_analysis:
                    elements = img_analysis["visual_elements"]
                    if isinstance(elements, list):
                        for elem in elements:
                            if isinstance(elem, dict):
                                elem_type = elem.get("element_type", "")
                                if elem_type:
                                    insights["visual_elements"].append(elem_type)

                # Extract text content
                if "text_content" in img_analysis:
                    text = img_analysis["text_content"]
                    if text:
                        insights["text_patterns"].append(text[:200])

                # Extract CTA information
                if "call_to_action_button" in img_analysis:
                    cta = img_analysis["call_to_action_button"]
                    if isinstance(cta, dict):
                        insights["cta_styles"].append({
                            "text": cta.get("text", ""),
                            "color": cta.get("color", ""),
                            "position": cta.get("position", ""),
                        })

            # Extract from campaign metadata
            if "campaign_name" in analysis:
                insights["subject_line_patterns"].append(analysis["campaign_name"])

            # Extract performance indicators
            if "open_rate" in analysis or "conversion_rate" in analysis:
                open_rate = analysis.get("open_rate", 0)
                conversion_rate = analysis.get("conversion_rate", 0)
                if open_rate > 0.2 or conversion_rate > 0.05:
                    insights["successful_elements"].append({
                        "campaign_id": campaign_data.get("campaign_id"),
                        "open_rate": open_rate,
                        "conversion_rate": conversion_rate,
                    })

        # Deduplicate and limit
        insights["color_palettes"] = list(set(insights["color_palettes"]))[:10]
        insights["visual_elements"] = list(set(insights["visual_elements"]))[:10]
        insights["text_patterns"] = insights["text_patterns"][:5]
        insights["cta_styles"] = insights["cta_styles"][:5]
        insights["subject_line_patterns"] = insights["subject_line_patterns"][:5]

        return insights

    def get_campaign_text_samples(
        self,
        campaign_analyses: List[Dict[str, Any]],
        max_samples: int = 10,
    ) -> List[str]:
        """Extract text samples from past campaigns."""
        text_samples = []

        for campaign_data in campaign_analyses:
            analysis = campaign_data.get("analysis", {})
            images = analysis.get("images", [])

            for img_data in images:
                img_analysis = img_data.get("analysis", {}) if "analysis" in img_data else img_data

                # Extract text content
                if "text_content" in img_analysis:
                    text = img_analysis["text_content"]
                    if text and len(text) > 20:
                        text_samples.append(text[:500])

                # Extract from header/logo
                if "header" in img_analysis:
                    header = img_analysis["header"]
                    if isinstance(header, dict) and "logo" in header:
                        logo = header["logo"]
                        if isinstance(logo, dict):
                            if logo.get("text"):
                                text_samples.append(logo["text"])
                            if logo.get("tagline"):
                                text_samples.append(logo["tagline"])

                if len(text_samples) >= max_samples:
                    break

            if len(text_samples) >= max_samples:
                break

        return text_samples[:max_samples]

    def get_campaign_image_references(
        self,
        campaign_analyses: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Extract image references from past campaigns."""
        image_refs = []

        for campaign_data in campaign_analyses:
            analysis = campaign_data.get("analysis", {})
            images = analysis.get("images", [])

            for img_data in images:
                img_analysis = img_data.get("analysis", {}) if "analysis" in img_data else img_data

                image_ref = {
                    "campaign_id": campaign_data.get("campaign_id"),
                    "image_path": img_data.get("image_path") or img_data.get("image_url"),
                    "image_id": img_data.get("image_id"),
                    "description": img_analysis.get("overall_description"),
                    "visual_elements": img_analysis.get("visual_elements", []),
                    "dominant_colors": img_analysis.get("dominant_colors", []),
                }

                image_refs.append(image_ref)

        return image_refs



