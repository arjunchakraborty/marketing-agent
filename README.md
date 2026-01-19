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
- **ChromaDB** (for vector search) - automatically installed with backend dependencies
- **Ollama** (optional, for local LLM) - https://ollama.ai - install if using local LLM instead of OpenAI/Anthropic

### Backend Setup

**Important:** Always run backend commands from the `backend` directory to ensure Python can find the `app` module.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn app.main:app --reload
```

**Note:** If you encounter `ModuleNotFoundError: No module named 'app'`, make sure you're running commands from the `backend` directory. The `app` module must be in Python's import path.

### Frontend Setup

```bash
cd web
npm install
npm run dev
```

Navigate to `http://localhost:3000` to explore the TripleWhale-inspired control center.

### Uploading Campaign Data

Campaign datasets can be uploaded directly through the web UI:

1. Navigate to `http://localhost:3000`
2. Use the data upload interface to upload CSV files containing campaign metrics
3. The system automatically:
   - Normalizes column names (handles variations like "Campaign ID" vs "campaign_id")
   - Creates database tables with normalized columns and calculated metrics
   - Processes campaign images and matches them to campaigns by ID
   - Analyzes visual elements (colors, composition, text, CTAs)
   - Correlates visual elements with campaign performance metrics

**Supported Campaign Data Formats:**
- Campaign metrics CSV with columns like: `Campaign ID`, `Campaign Name`, `Subject`, `Send Time`, `Total Recipients`, `Unique Opens`, `Open Rate`, `Unique Clicks`, `Click Rate`, `Unique Placed Order`, `Placed Order Rate`, `Revenue`, `Unsubscribes`, `Spam Complaints`
- Campaign images (automatically matched to campaigns by extracting campaign IDs from filenames)

### Campaign Strategy Analysis

The frontend includes a Campaign Strategy Experiment tool that combines SQL queries, image analysis, and visual element correlation:

1. Navigate to `http://localhost:3000` and click "Campaign Strategy" in the navigation
2. Adjust the SQL query to target specific campaigns (or use natural language prompt)
3. Upload campaign images if needed
4. Click "Run Campaign Strategy Analysis"
5. View results in tabs: Campaigns, Image Analysis, Visual Correlations

The system automatically:
- Limits analysis to top 5 performing campaigns
- Analyzes visual elements (colors, composition, text, CTAs)
- Correlates visual elements with campaign performance metrics
- Stores all results for future analysis and campaign generation

## Configuration

Configuration is managed through a cached `.env` file. The backend automatically loads settings from `backend/.env` on startup. The configuration includes:

- Database connection settings
- LLM provider configuration (OpenAI, Anthropic, or Ollama)
- Vector search settings (ChromaDB)
- API keys and service endpoints
- Logging configuration

A default `.env` file is created automatically on first run with sensible defaults. You can modify it to customize your setup.

## Key Features

The platform provides:

- **Metric tiles** for revenue, AOV, ROAS, and channel engagement
- **Prompt-to-SQL explorer** backed by uploaded datasets
- **Cohort performance table** and experiment planner backlog
- **Campaign Strategy Experiment** - Analyze campaigns and images with SQL query editor
- **Campaign recommendation board** and inventory alert feed
- **Email Feature Detection** - Automatically detects and catalogs key email features:
  - CTA buttons (text, position, color)
  - Promotions and discount badges
  - Product images
  - Headlines and content
  - Branding elements (logos)
  - Social proof (testimonials, reviews)
  - Urgency indicators (countdown timers, limited offers)
  - Email structure (header, footer, sections)

## API Endpoints

Key endpoints:

- `GET /api/v1/health` – service health metadata
- `POST /api/v1/ingestion/sources` – register data sources
- `POST /api/v1/ingestion/csv` – ingest CSV files into the analytics warehouse
- `POST /api/v1/ingestion/klaviyo` – Ingest Klaviyo campaign CSV
- `POST /api/v1/experiments/run` – Run campaign strategy experiment workflow
- `GET /api/v1/experiments/{experiment_run_id}` – Get stored experiment results
- `GET /api/v1/experiments/` – List all experiment runs
- `POST /api/v1/experiments/generate-campaigns` – Generate new campaigns based on analysis insights
- `POST /api/v1/analytics/kpi` – Real KPI computations (revenue, AOV, ROAS, conversion rate, sessions)
- `POST /api/v1/analytics/cohort` – Real cohort analysis grouping by dimensions
- `POST /api/v1/analytics/prompt-sql` – LLM-powered SQL generation from natural language
- `POST /api/v1/intelligence/insights` – LLM-generated narrative summaries from analytics signals
- `POST /api/v1/intelligence/campaigns` – LLM-generated campaign recommendations with expected uplift
- `POST /api/v1/image-analysis/detect-features` – Email feature detection (CTAs, promotions, products, etc.) - Note: Currently disabled
- `GET /api/v1/products/top` – Top performing products by sales
- `GET /api/v1/products/inventory/alerts` – Inventory alerts for low stock items

## Testing

```bash
cd backend
pytest
```

Frontend testing (to be added): `npm run lint` / `npm run test` once test harness is configured.

## Development Roadmap

The `agent-spec.md` document captures the full roadmap. Immediate focus areas:

1. **Data Ingestion** – Shopify API sync, CSV normalization jobs, event streaming via A2A.
2. **Analytics Engine** – KPI rollups, cohort/anomaly detection, prompt-to-SQL execution, forecasting.
3. **Intelligence Layer** – LLM-driven summaries, campaign plans, creative brief generation, protocol adapters.
4. **Frontend Experience** – Real APIs for dashboards, SQL explorer execution, collaborative workflows.
5. **Integrations & Guardrails** – Klaviyo publishing, social platform connectors, asset QA, approval flows.
6. **QA & DevOps** – Automated tests, CI/CD, monitoring, compliance and protocol conformance suites.

## Recent Enhancements (per agent-spec.md)

✅ **LLM Integration**: Prompt-to-SQL now uses OpenAI/Anthropic/Ollama for intelligent SQL generation  
✅ **Real Analytics**: KPI computations, cohort analysis, and forecasting from ingested datasets  
✅ **Intelligence Layer**: LLM-powered insight summaries and campaign recommendations  
✅ **Product Insights**: Top products API and inventory alert generation  
✅ **Protocol Adapters**: A2A and MCP-AGUI scaffolding for agent orchestration and UI embedding  
✅ **Klaviyo Integration**: Specialized CSV ingestion for Klaviyo campaign data with automatic column normalization  
✅ **Image Analysis Pipeline**: Visual element detection in email campaigns using OpenAI Vision API  
✅ **Email Feature Detection**: Framework for detecting and cataloging key email features (CTAs, promotions, products, branding, social proof, urgency indicators) - Currently disabled  
✅ **Campaign Strategy Workflow**: End-to-end experiment system for analyzing top 5 campaigns, processing images, detecting features, and correlating visual elements with performance metrics  
✅ **UI-Based Data Upload**: Simplified data ingestion through web interface

## Next Steps

- Enhanced vector search features for campaign recommendations
- Queue/orchestration layer for ingestion and automation (A2A messaging)
- Creative asset pipeline with brand QA and approval workflows
- Klaviyo integration for campaign publishing
- Secure credential vaulting and RBAC across automations
- Additional protocol adapters (OpenAI Realtime, LangChain ReAct, Vercel AI SDK)

Refer back to `agent-spec.md` for milestone sequencing and ensure new work aligns with the architecture plan.
