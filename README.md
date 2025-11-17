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
cd /Users/kerrief/projects/marketing-agent/backend
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn app.main:app --reload
```

**Note:** If you encounter `ModuleNotFoundError: No module named 'app'`, make sure you're running commands from the `backend` directory. The `app` module must be in Python's import path.

#### ChromaDB Setup (for Vector Search)

ChromaDB is automatically installed with the backend dependencies. To enable vector search:

1. **Pull the embedding model** (if using Ollama for embeddings):
   ```bash
   ollama pull nomic-embed-text
   ```

2. **Enable in configuration** - Add to `backend/.env`:
   ```env
   ENABLE_VECTOR_SEARCH=true
   VECTOR_DB_PATH=storage/vectors
   OLLAMA_EMBEDDING_MODEL=nomic-embed-text
   ```

The vector database will be automatically created at `backend/storage/vectors` on first use. See the [Vector Search Setup](#vector-search-setup-chromadb) section below for more details.

#### Ingest local CSV data

Point the backend at the provided marketing data directory (default is `/Users/kerrief/projects/mappe/data`) and trigger ingestion:

**Via Python module (from backend directory):**
```bash
cd /Users/kerrief/projects/marketing-agent/backend
source .venv/bin/activate
python -m app.workflows.local_csv_ingestion
```

**Alternative (using PYTHONPATH):**
```bash
cd /Users/kerrief/projects/marketing-agent
source backend/.venv/bin/activate
PYTHONPATH=backend python -m app.workflows.local_csv_ingestion
```

**Via API:**

```bash
curl -X POST http://localhost:8000/api/v1/ingestion/csv \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_name": "initial_bootstrap",
    "file_path": "/Users/kerrief/projects/mappe/data"
  }'
```

This loads all CSVs into the SQLite database in `backend/storage/marketing_agent.db` and registers metadata for Prompt-to-SQL exploration.

#### Import Klaviyo Campaign Data

The system includes specialized workflows for importing and analyzing Klaviyo campaign data. This includes both campaign metrics (CSV) and campaign images.

**1. Import Klaviyo Campaign CSV**

The CSV file should contain campaign metrics with columns like:
- `Campaign ID`, `Campaign Name`, `Subject`
- `Send Time`, `Total Recipients`
- `Unique Opens`, `Open Rate`, `Unique Clicks`, `Click Rate`
- `Unique Placed Order`, `Placed Order Rate`, `Revenue`
- `Unsubscribes`, `Spam Complaints`

Column names are automatically normalized, so variations like "Campaign ID" vs "campaign_id" are handled.

**Via API:**
```bash
curl -X POST http://localhost:8000/api/v1/ingestion/klaviyo \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/Users/kerrief/projects/klyaviyo/Klaviyo Campaigns.csv",
    "table_name": "campaigns"
  }'
```

**Via Python:**
```bash
source /Users/kerrief/projects/marketing-agent/backend/.venv/bin/activate
python -c "
from app.workflows.klaviyo_ingestion import ingest_klaviyo_csv
result = ingest_klaviyo_csv('/Users/kerrief/projects/klyaviyo/Klaviyo Campaigns.csv')
print(f'Imported {result[\"inserted\"]} campaigns, updated {result[\"updated\"]} existing')
"
```

This creates a `campaigns` table in the database with normalized columns and calculated metrics.

**3. Import Campaign Data into Vector Database**

After ingesting Klaviyo CSV data and running image analyses, you can import the data into ChromaDB for semantic search:

```bash
source /Users/kerrief/projects/marketing-agent/backend/.venv/bin/activate
python backend/scripts/load_klaviyo_to_vector_db.py \
  --csv /Users/kerrief/projects/marketing-agent/backend/storage/email_campaigns.csv \
  --image-folder /Users/kerrief/projects/marketing-agent/backend/image-analysis-extract \
  --collection klaviyo_campaigns \
  --overwrite
```

**Search for similar campaigns:**
```bash
python backend/scripts/load_klaviyo_to_vector_db.py \
  --search "bright colorful campaigns with high conversion rates" \
  --n-results 5
```

**Run Campaign Strategy Experiment:**

The experiment workflow combines SQL queries, image analysis, and visual element correlation:

**Via API:**
```bash
curl -X POST http://localhost:8000/api/v1/experiments/run \
  -H "Content-Type: application/json" \
  -d '{
    "sql_query": "SELECT campaign_id, campaign_name, open_rate, conversion_rate, revenue FROM campaigns WHERE open_rate > 0.3 ORDER BY conversion_rate DESC LIMIT 20",
    "image_directory": "/Users/kerrief/projects/klyaviyo",
    "experiment_name": "Top Performing Campaigns Analysis"
  }'
```

**Via Frontend:**
1. Navigate to `http://localhost:3000` and click "Campaign Strategy" in the navigation
2. Adjust the SQL query to target specific campaigns (or use natural language prompt)
3. Set the image directory path (default: `/Users/kerrief/projects/klyaviyo`)
4. Click "Run Campaign Strategy Analysis"
5. View results in tabs: Campaigns, Image Analysis, Visual Correlations

**Complete Workflow Example:**

```bash
# Step 1: Import Klaviyo CSV data
curl -X POST http://localhost:8000/api/v1/ingestion/klaviyo \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/Users/kerrief/projects/klyaviyo/Klaviyo Campaigns.csv"}'

# Step 2: Run experiment with SQL query and image analysis
curl -X POST http://localhost:8000/api/v1/experiments/run \
  -H "Content-Type: application/json" \
  -d '{
    "sql_query": "SELECT campaign_id, campaign_name, open_rate, click_rate, conversion_rate, revenue FROM campaigns WHERE open_rate > 0.3 OR conversion_rate > 0.01 ORDER BY conversion_rate DESC, revenue DESC LIMIT 20",
    "image_directory": "/Users/kerrief/projects/klyaviyo",
    "experiment_name": "High Performance Campaign Analysis"
  }'

# Step 3: Retrieve experiment results
curl http://localhost:8000/api/v1/experiments/{experiment_run_id}

# Step 4: Generate new campaigns based on insights
curl -X POST http://localhost:8000/api/v1/experiments/generate-campaigns \
  -H "Content-Type: application/json" \
  -d '{
    "experiment_run_id": "{experiment_run_id}",
    "use_top_products": true,
    "num_campaigns": 5
  }'
```

**Expected File Structure:**
```
/Users/kerrief/projects/klyaviyo/
├── Klaviyo Campaigns.csv          # Campaign metrics CSV
├── www.klaviyo.com_campaign_*.png # Campaign images (with campaign IDs in filenames)
└── ...
```

The system automatically:
- Matches images to campaigns by extracting campaign IDs from filenames
- Analyzes visual elements (colors, composition, text, CTAs)
- Correlates visual elements with campaign performance metrics
- Stores all results for future analysis and campaign generation

Key endpoints:

- `GET /api/v1/health` – service health metadata
- `POST /api/v1/ingestion/sources` – register data sources
- `POST /api/v1/ingestion/csv` – ingest local CSV directories into the analytics warehouse
- `POST /api/v1/ingestion/klaviyo` – **Ingest Klaviyo campaign CSV** from file path (creates `campaigns` table)
- `POST /api/v1/experiments/run` – **Run campaign strategy experiment** workflow (SQL query → image analysis → correlation)
- `GET /api/v1/experiments/{experiment_run_id}` – **Get stored experiment results** (campaigns, images, correlations)
- `GET /api/v1/experiments/` – **List all experiment runs**
- `POST /api/v1/experiments/generate-campaigns` – **Generate new campaigns** based on analysis insights
- `POST /api/v1/analytics/kpi` – **Real KPI computations** (revenue, AOV, ROAS, conversion rate, sessions)
- `POST /api/v1/analytics/cohort` – **Real cohort analysis** grouping by dimensions
- `POST /api/v1/analytics/prompt-sql` – **LLM-powered SQL generation** from natural language (OpenAI/Anthropic)
- `POST /api/v1/intelligence/insights` – **LLM-generated narrative summaries** from analytics signals
- `POST /api/v1/intelligence/campaigns` – **LLM-generated campaign recommendations** with expected uplift
- `POST /api/v1/image-analysis/detect-features` – **Email feature detection** (CTAs, promotions, products, etc.) - Note: Currently disabled
- `GET /api/v1/products/top` – **Top performing products** by sales
- `GET /api/v1/products/inventory/alerts` – **Inventory alerts** for low stock items

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
- **Campaign Strategy Experiment** - Analyze Klaviyo campaigns and images with SQL query editor
- Campaign recommendation board and inventory alert feed
- Protocol readiness status and upcoming integration callouts

**Campaign Strategy Analysis:**
- SQL query editor for finding impactful campaigns (editable)
- Natural language prompt → SQL generation
- Image directory input for campaign visual analysis
- **Email Feature Detection** - Automatically detects and catalogs key email features:
  - CTA buttons (text, position, color)
  - Promotions and discount badges
  - Product images
  - Headlines and content
  - Branding elements (logos)
  - Social proof (testimonials, reviews)
  - Urgency indicators (countdown timers, limited offers)
  - Email structure (header, footer, sections)
- Results display: campaigns analyzed, image insights, visual correlations, feature catalog
- Rerun capability with adjusted queries
- **Top 5 campaigns only** - Automatically limits analysis to top 5 performing campaigns

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

# OpenAI Configuration (optional, fallback for image analysis)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini  # Use gpt-4o for image analysis (automatically used for vision tasks)

# Anthropic Configuration (alternative provider)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Ollama Configuration (local LLM, no API key needed)
# Make sure Ollama is installed and running: https://ollama.ai
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2  # or any model you have installed (llama3.2, mistral, codellama, etc.)
OLLAMA_MAX_TABLES=6  # Maximum tables in prompt (reduce for smaller context windows)
OLLAMA_MAX_COLUMNS=15  # Maximum columns per table in prompt

# ChromaDB Configuration (for vector search and semantic dataset discovery)
# ChromaDB is automatically installed with the backend dependencies
# Vector database will be created at: backend/storage/vectors (relative to backend directory)
ENABLE_VECTOR_SEARCH=false  # Set to true to enable vector search features
VECTOR_DB_PATH=storage/vectors  # Path relative to backend directory
OLLAMA_EMBEDDING_MODEL=nomic-embed-text  # Embedding model for vector search (default: nomic-embed-text)
# To use embeddings, ensure Ollama is running and pull the model:
# ollama pull nomic-embed-text


# Logging Configuration
LOG_LEVEL=INFO  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_EXPERIMENTS_DEBUG=true  # Enable detailed DEBUG logging for experiments and workflows
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
✅ **Klaviyo Integration**: Specialized CSV ingestion for Klaviyo campaign data with automatic column normalization  
✅ **Image Analysis Pipeline**: Visual element detection in email campaigns using OpenAI Vision API  
✅ **Email Feature Detection**: Framework for detecting and cataloging key email features (CTAs, promotions, products, branding, social proof, urgency indicators) - Currently disabled  
✅ **Campaign Strategy Workflow**: End-to-end experiment system for analyzing top 5 campaigns, processing images, detecting features, and correlating visual elements with performance metrics  

## Vector Search Setup (ChromaDB)

The system includes ChromaDB integration for vector search and semantic dataset discovery. This enables finding relevant datasets and insights based on semantic similarity rather than exact keyword matching.

### Prerequisites

1. **Install ChromaDB** (already included in dependencies):
   ```bash
   cd backend
   pip install chromadb
   ```

2. **Set up Ollama Embedding Model** (for generating embeddings):
   ```bash
   # Make sure Ollama is running
   ollama pull nomic-embed-text
   ```

### Configuration

Enable vector search in your `backend/.env`:
```env
ENABLE_VECTOR_SEARCH=true
VECTOR_DB_PATH=storage/vectors
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

### Importing Data into Vector Database

**Import Klaviyo Campaign Data:**

After ingesting Klaviyo CSV data and running image analyses, import into ChromaDB:

```bash
cd /Users/kerrief/projects/marketing-agent/backend
source .venv/bin/activate

# Import campaigns with image analyses
python scripts/load_klaviyo_to_vector_db.py \
  --csv storage/email_campaigns.csv \
  --image-folder image-analysis-extract \
  --collection klaviyo_campaigns \
  --overwrite
```

**Script Options:**
- `--csv`: Path to email_campaigns.csv file (default: `backend/storage/email_campaigns.csv`)
- `--image-folder`: Path to image-analysis-extract folder containing JSON files (default: `backend/image-analysis-extract`)
- `--collection`: Vector database collection name (default: `klaviyo_campaigns`)
- `--overwrite`: Overwrite existing campaigns
- `--search`: Search for similar campaigns (e.g., `--search "bright colorful campaigns"`)
- `--n-results`: Number of search results (default: 5)
- `--verbose` or `-v`: Verbose output

**Search Examples:**
```bash
# Find campaigns similar to a query
python scripts/load_klaviyo_to_vector_db.py \
  --search "high performing campaigns with dark themes" \
  --n-results 10

# Find campaigns with specific visual elements
python scripts/load_klaviyo_to_vector_db.py \
  --search "campaigns with product images and clear CTAs" \
  --n-results 5
```

### Usage

Once enabled and data is imported, the system will:
- Automatically generate embeddings for ingested datasets
- Store vectors in ChromaDB at `backend/storage/vectors`
- Enable semantic search across datasets, campaigns, and insights
- Support finding similar campaigns, products, or customer segments

The vector database is automatically created on first use and persists between sessions.

## Next Steps

- Enhanced vector search features for campaign recommendations
- Queue/orchestration layer for ingestion and automation (A2A messaging)
- Creative asset pipeline with brand QA and approval workflows
- Klaviyo integration for campaign publishing
- Secure credential vaulting and RBAC across automations
- Additional protocol adapters (OpenAI Realtime, LangChain ReAct, Vercel AI SDK)

Refer back to `agent-spec.md` for milestone sequencing and ensure new work aligns with the architecture plan.
