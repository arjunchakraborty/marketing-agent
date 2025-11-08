"""Analytics endpoints for KPI, cohort, and anomaly insights."""
from fastapi import APIRouter

from ..schemas.analytics import (
    CohortAnalysisRequest,
    CohortAnalysisResponse,
    KpiQueryRequest,
    KpiQueryResponse,
)

router = APIRouter()


@router.post("/kpi", response_model=KpiQueryResponse, summary="Execute KPI query")
async def query_kpis(payload: KpiQueryRequest) -> KpiQueryResponse:
    """Return placeholder KPI aggregates until analytics engine is implemented."""
    return KpiQueryResponse(kpis={metric: 0.0 for metric in payload.metrics})


@router.post("/cohort", response_model=CohortAnalysisResponse, summary="Run cohort analysis")
async def run_cohort(payload: CohortAnalysisRequest) -> CohortAnalysisResponse:
    """Return stub cohort response for future implementation."""
    return CohortAnalysisResponse(group_key=payload.group_by, cohorts=[])
