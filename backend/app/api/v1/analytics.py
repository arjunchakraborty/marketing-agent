"""Analytics endpoints for KPI, cohort, and anomaly insights."""
from typing import Optional

from fastapi import APIRouter

from ...schemas.analytics import (
    CohortAnalysisRequest,
    CohortAnalysisResponse,
    CohortDefinition,
    KpiQueryRequest,
    KpiQueryResponse,
    PrecomputedKpiItem,
    PrecomputedKpiListResponse,
    PrecomputeKpiRequest,
    PrecomputeKpiResponse,
    PromptToSqlRequest,
    PromptToSqlResponse,
)
from ...services.analytics_service import AnalyticsService
from ...services.kpi_precomputation_service import KpiPrecomputationService, STANDARD_KPI_PROMPTS
from ...services.prompt_sql_service import PromptToSqlService

router = APIRouter()
prompt_sql_service = PromptToSqlService()
analytics_service = AnalyticsService()
kpi_precomputation_service = KpiPrecomputationService()


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


@router.get("/kpi/precomputed", response_model=PrecomputedKpiListResponse, summary="List precomputed KPIs")
async def list_precomputed_kpis(business: Optional[str] = None) -> PrecomputedKpiListResponse:
    """List all precomputed KPI SQL queries."""
    kpis_data = kpi_precomputation_service.list_precomputed_kpis(business=business)
    kpis = [
        PrecomputedKpiItem(
            kpi_name=item["kpi_name"],
            prompt=item["prompt"],
            sql_query=item["sql_query"],
            business=item.get("business"),
            created_at=item["created_at"],
            updated_at=item["updated_at"],
            last_executed_at=item.get("last_executed_at"),
            execution_count=item.get("execution_count", 0),
        )
        for item in kpis_data
    ]
    return PrecomputedKpiListResponse(kpis=kpis)


@router.post("/kpi/precompute", response_model=PrecomputeKpiResponse, summary="Precompute KPI SQL queries")
async def precompute_kpis(payload: PrecomputeKpiRequest) -> PrecomputeKpiResponse:
    """Precompute SQL queries for standard KPIs or specific KPIs."""
    if payload.kpi_names:
        # Precompute specific KPIs
        results = []
        for kpi_name in payload.kpi_names:
            prompt = STANDARD_KPI_PROMPTS.get(kpi_name, "")
            if prompt:
                result = kpi_precomputation_service.precompute_kpi_sql(kpi_name, prompt, payload.business)
                results.append(result)
        status = "completed" if all(r.get("status") == "precomputed" for r in results) else "partial"
    else:
        # Precompute all standard KPIs
        results = kpi_precomputation_service.precompute_standard_kpis(business=payload.business)
        status = "completed" if all(r.get("status") == "precomputed" for r in results) else "partial"

    return PrecomputeKpiResponse(results=results, status=status)
