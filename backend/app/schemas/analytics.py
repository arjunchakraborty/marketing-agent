"""Schemas for analytics queries and responses."""
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

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


class PromptToSqlRequest(BaseModel):
    prompt: str = Field(..., description="Natural language prompt to translate into SQL")


class PromptToSqlResponse(BaseModel):
    table_name: str
    business: str
    dataset_name: str
    sql: str
    columns: List[str]
    rows: List[Dict[str, Any]]


class PrecomputedKpiItem(BaseModel):
    kpi_name: str
    prompt: str
    sql_query: str
    business: Optional[str] = None
    created_at: str
    updated_at: str
    last_executed_at: Optional[str] = None
    execution_count: int


class PrecomputedKpiListResponse(BaseModel):
    kpis: List[PrecomputedKpiItem]


class PrecomputeKpiRequest(BaseModel):
    business: Optional[str] = Field(None, description="Business name to precompute KPIs for")
    kpi_names: Optional[List[str]] = Field(None, description="Specific KPI names to precompute. If None, precomputes all standard KPIs")


class PrecomputeKpiResponse(BaseModel):
    results: List[Dict[str, Any]]
    status: str
