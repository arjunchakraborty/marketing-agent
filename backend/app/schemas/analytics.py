"""Schemas for analytics queries and responses."""
from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


Granularity = Literal["hour", "day", "week", "month"]


class KpiQueryRequest(BaseModel):
    metrics: List[str] = Field(..., description="List of KPI metric identifiers to compute")
    filters: Dict[str, str] = Field(default_factory=dict, description="Dimension filters to apply to the query")
    start_date: Optional[datetime] = Field(None, description="Start datetime for the KPI window")
    end_date: Optional[datetime] = Field(None, description="End datetime for the KPI window")
    granularity: Granularity = Field(default="day")


class KpiQueryResponse(BaseModel):
    kpis: Dict[str, float]
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class CohortDefinition(BaseModel):
    cohort_label: str
    member_count: int
    metrics: Dict[str, float]


class CohortAnalysisRequest(BaseModel):
    group_by: str = Field(..., description="Dimension to group cohort membership by")
    metric: str = Field(..., description="Metric evaluated per cohort")
    filters: Dict[str, str] = Field(default_factory=dict)


class CohortAnalysisResponse(BaseModel):
    group_key: str
    cohorts: List[CohortDefinition]
    generated_at: datetime = Field(default_factory=datetime.utcnow)
