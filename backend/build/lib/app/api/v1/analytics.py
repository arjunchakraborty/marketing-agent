"""Analytics endpoints for KPI, cohort, and anomaly insights."""
from fastapi import APIRouter

from ...schemas.analytics import (
    CohortAnalysisRequest,
    CohortAnalysisResponse,
    CohortDefinition,
    KpiQueryRequest,
    KpiQueryResponse,
    PromptToSqlRequest,
    PromptToSqlResponse,
)
from ...services.analytics_service import AnalyticsService
from ...services.prompt_sql_service import PromptToSqlService

router = APIRouter()
prompt_sql_service = PromptToSqlService()
analytics_service = AnalyticsService()


@router.post("/kpi", response_model=KpiQueryResponse, summary="Execute KPI query")
async def query_kpis(payload: KpiQueryRequest) -> KpiQueryResponse:
    """Compute real KPI aggregates from ingested datasets."""
    kpis = analytics_service.query_kpis(payload.metrics, payload.filters)
    return KpiQueryResponse(kpis=kpis)


@router.post("/cohort", response_model=CohortAnalysisResponse, summary="Run cohort analysis")
async def run_cohort(payload: CohortAnalysisRequest) -> CohortAnalysisResponse:
    """Perform cohort analysis grouping by specified dimension."""
    cohorts_data = analytics_service.cohort_analysis(payload.group_by, payload.metric, payload.filters)
    cohorts = [
        CohortDefinition(cohort_label=key, member_count=int(data.get("count", 0)), metrics=data)
        for key, data in cohorts_data.items()
    ]
    return CohortAnalysisResponse(group_key=payload.group_by, cohorts=cohorts)


@router.post("/prompt-sql", response_model=PromptToSqlResponse, summary="Generate SQL from natural language")
async def prompt_sql(payload: PromptToSqlRequest) -> PromptToSqlResponse:
    """Generate and execute SQL for the provided prompt."""
    result = prompt_sql_service.execute_prompt(payload.prompt)
    return PromptToSqlResponse(**result)
