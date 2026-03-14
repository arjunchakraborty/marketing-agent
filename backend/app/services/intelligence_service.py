"""Intelligence service to drive recommendations and summaries."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..core.config import settings
from .llm_service import LLMService


class IntelligenceService:
    """Coordinate LLM-backed workflows for insights and campaign planning."""

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

    def summarize_insights(self, signals: List[str], context: Dict[str, Any]) -> str:
        """Generate narrative summary from analytics signals using LLM."""
        if not self.llm_service:
            return "LLM service not available. Please configure API keys in environment."

        try:
            return self.llm_service.generate_insight_summary(signals, context)
        except Exception as e:
            return f"Summary generation failed: {str(e)}"

    def recommend_campaigns(
        self, objectives: List[str], audience_segments: List[str], constraints: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate campaign recommendations using LLM."""
        if not self.llm_service:
            return [
                {
                    "name": "LLM Not Available",
                    "channel": "N/A",
                    "objective": "Configure LLM API keys",
                    "expected_uplift": "0%",
                    "summary": "Please set OPENAI_API_KEY, ANTHROPIC_API_KEY, or ensure Ollama is running at http://localhost:11434",
                    "talking_points": [],
                }
            ]

        try:
            campaigns = self.llm_service.generate_campaign_recommendations(objectives, audience_segments, constraints)
            return campaigns if isinstance(campaigns, list) else [campaigns]
        except Exception as e:
            return [
                {
                    "name": "Error",
                    "channel": "N/A",
                    "objective": "Campaign generation failed",
                    "expected_uplift": "0%",
                    "summary": str(e),
                    "talking_points": [],
                }
            ]
