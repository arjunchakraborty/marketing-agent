# Marketing Agent

Full-stack marketing intelligence platform combining a FastAPI backend and a Next.js frontend. The solution mirrors TripleWhale-style analytics while embracing the agent protocols outlined in `agent-spec.md` (A2A, MCP-AGUI, OpenAI Realtime adapters) and prepares the groundwork for data ingestion, analytics, and automated campaign orchestration.

## Project Structure

```
backend/    FastAPI services, schemas, and workflow scaffolding
web/        Next.js analytics and orchestration dashboard
agent-spec.md      Product and architecture blueprint used to drive implementation
strategy-agent-spec.md  Supplemental strategy guidance for future milestones
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- npm (bundled with Node.js)
- PostgreSQL (local or container) if you plan to wire up persistence

### Backend Setup

```bash
cd /Users/kerrief/projects/marketing-agent/backend
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn app.main:app --reload
```

Key endpoints (stubs today):

- `GET /api/v1/health` – service health metadata
- `POST /api/v1/ingestion/sources` – register data sources
- `POST /api/v1/ingestion/csv` – submit CSV ingestion jobs
- `POST /api/v1/analytics/kpi` – placeholder KPI aggregates
- `POST /api/v1/analytics/cohort` – placeholder cohort analysis
- `POST /api/v1/intelligence/insights` – stubbed narrative summary
- `POST /api/v1/intelligence/campaigns` – placeholder campaign recommendations

### Frontend Setup

```bash
cd /Users/kerrief/projects/marketing-agent/web
npm install
npm run dev
```

Navigate to `http://localhost:3000` to explore the TripleWhale-inspired control center with:

- Metric tiles for revenue, AOV, ROAS, and channel engagement
- Prompt-to-SQL exploration canvas with generated SQL preview
- Cohort performance table and experiment planner backlog
- Campaign recommendation board and inventory alert feed
- Protocol readiness status and upcoming integration callouts

## Development Roadmap

The `agent-spec.md` document captures the full roadmap. Immediate focus areas:

1. **Data Ingestion** – Shopify API sync, CSV normalization jobs, event streaming via A2A.
2. **Analytics Engine** – KPI rollups, cohort/anomaly detection, prompt-to-SQL execution, forecasting.
3. **Intelligence Layer** – LLM-driven summaries, campaign plans, creative brief generation, protocol adapters.
4. **Frontend Experience** – Real APIs for dashboards, SQL explorer execution, collaborative workflows.
5. **Integrations & Guardrails** – Klaviyo publishing, social platform connectors, asset QA, approval flows.
6. **QA & DevOps** – Automated tests, CI/CD, monitoring, compliance and protocol conformance suites.

## Testing

```bash
cd /Users/kerrief/projects/marketing-agent/backend
pytest
```

Frontend testing (to be added): `npm run lint` / `npm run test` once test harness is configured.

## Environment & Configuration

Backend configuration lives in `backend/app/core/config.py` using `pydantic-settings`. Override defaults with a `.env` file (database URL, allowed origins, storage buckets, etc.). Frontend environment variables can be added via `.env.local` (e.g., `NEXT_PUBLIC_API_BASE=http://localhost:8000`).

## Contributing & Next Steps

- OpenAPI schemas + typed clients for frontend integration
- Queue/orchestration layer for ingestion and automation
- Protocol adapters (A2A, MCP-AGUI, OpenAI Realtime, LangChain ReAct)
- Creative asset pipeline with brand QA and approval workflows
- Secure credential vaulting and RBAC across automations

Refer back to `agent-spec.md` for milestone sequencing and ensure new work aligns with the architecture plan.
