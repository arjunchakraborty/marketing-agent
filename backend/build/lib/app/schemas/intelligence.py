"""Schemas for intelligence and recommendation workflows."""
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class InsightSummaryRequest(BaseModel):
    signals: List[str] = Field(..., description="List of signal identifiers or KPI keys to summarize")
    context: Dict[str, str] = Field(default_factory=dict, description="Additional context such as campaign or segment")


class InsightSummaryResponse(BaseModel):
    summary: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    follow_up_actions: List[str] = Field(default_factory=list)


class CampaignRecommendationRequest(BaseModel):
    objectives: List[str] = Field(..., description="Marketing objectives to target")
    audience_segments: List[str] = Field(default_factory=list)
    constraints: Dict[str, str] = Field(default_factory=dict)
    existing_assets: Optional[List[str]] = None


class CampaignRecommendation(BaseModel):
    name: str
    channel: str
    expected_uplift: Optional[float] = None
    talking_points: List[str] = Field(default_factory=list)


class CampaignRecommendationResponse(BaseModel):
    recommendations: List[CampaignRecommendation]
    rationale: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
