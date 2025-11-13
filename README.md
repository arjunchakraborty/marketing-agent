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

#### Ingest local CSV data

Point the backend at the provided marketing data directory (default is `/Users/kerrief/projects/mappe/data`) and trigger ingestion:

```bash
source /Users/kerrief/projects/marketing-agent/backend/.venv/bin/activate
python -m app.workflows.local_csv_ingestion
```

or via the API:

```bash
curl -X POST http://localhost:8000/api/v1/ingestion/csv \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_name": "initial_bootstrap",
    "file_path": "/Users/kerrief/projects/mappe/data"
  }'
```

This loads all CSVs into the SQLite database in `backend/storage/marketing_agent.db` and registers metadata for Prompt-to-SQL exploration.

Key endpoints:

- `GET /api/v1/health` – service health metadata
- `POST /api/v1/ingestion/sources` – register data sources
- `POST /api/v1/ingestion/csv` – ingest local CSV directories into the analytics warehouse
- `POST /api/v1/analytics/kpi` – **Real KPI computations** (revenue, AOV, ROAS, conversion rate, sessions)
- `POST /api/v1/analytics/cohort` – **Real cohort analysis** grouping by dimensions
- `POST /api/v1/analytics/prompt-sql` – **LLM-powered SQL generation** from natural language (OpenAI/Anthropic)
- `POST /api/v1/intelligence/insights` – **LLM-generated narrative summaries** from analytics signals
- `POST /api/v1/intelligence/campaigns` – **LLM-generated campaign recommendations** with expected uplift
- `GET /api/v1/products/top` – **Top performing products** by sales
- `GET /api/v1/products/inventory/alerts` – **Inventory alerts** for low stock items
- `POST /api/v1/image-analysis/analyze` – **Image analysis** for detecting visual elements in email campaigns (URL or base64)
- `POST /api/v1/image-analysis/analyze/upload` – **Upload and analyze** image files for visual element detection
- `POST /api/v1/image-analysis/correlate` – **Correlate visual elements** with campaign performance metrics
- `POST /api/v1/image-analysis/cross-index` – **Cross-index visual elements** with campaign analytics to identify impactful elements

### Frontend Setup

```bash
cd /Users/kerrief/projects/marketing-agent/web
npm install
npm run dev
```

Navigate to `http://localhost:3000` to explore the TripleWhale-inspired control center with:

- Metric tiles for revenue, AOV, ROAS, and channel engagement
- Prompt-to-SQL explorer backed by the ingested datasets
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

Backend configuration lives in `backend/app/core/config.py` using `pydantic-settings`. Create a `backend/.env` file with:

```env
DATABASE_URL=sqlite:///../storage/marketing_agent.db
INGESTION_DATA_ROOT=/Users/kerrief/projects/mappe/data
ALLOWED_ORIGINS=http://localhost:3000

# LLM Configuration (required for prompt-to-SQL and intelligence features)
# Choose one or more providers:
DEFAULT_LLM_PROVIDER=ollama  # Options: openai, anthropic, ollama
USE_LLM_FOR_SQL=true

# OpenAI Configuration (required for image analysis with vision capabilities)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini  # Use gpt-4o for image analysis (automatically used for vision tasks)

# Anthropic Configuration (alternative provider)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Ollama Configuration (local LLM, no API key needed)
# Make sure Ollama is installed and running: https://ollama.ai
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2  # or any model you have installed (llama3.2, mistral, codellama, etc.)
```

Frontend environment variables via `web/.env.local`:
```env
NEXT_PUBLIC_API_BASE=http://localhost:8000/api
```

## Recent Enhancements (per agent-spec.md)

✅ **LLM Integration**: Prompt-to-SQL now uses OpenAI/Anthropic/Ollama for intelligent SQL generation  
✅ **Real Analytics**: KPI computations, cohort analysis, and forecasting from ingested datasets  
✅ **Intelligence Layer**: LLM-powered insight summaries and campaign recommendations  
✅ **Product Insights**: Top products API and inventory alert generation  
✅ **Protocol Adapters**: A2A and MCP-AGUI scaffolding for agent orchestration and UI embedding  
✅ **Image Analysis Pipeline**: Visual element detection in email campaigns using OpenAI Vision API, with cross-indexing to campaign performance analytics  

## Next Steps

- Vector search for semantic dataset discovery
- Queue/orchestration layer for ingestion and automation (A2A messaging)
- Creative asset pipeline with brand QA and approval workflows
- Klaviyo integration for campaign publishing
- Secure credential vaulting and RBAC across automations
- Additional protocol adapters (OpenAI Realtime, LangChain ReAct, Vercel AI SDK)

Refer back to `agent-spec.md` for milestone sequencing and ensure new work aligns with the architecture plan.
