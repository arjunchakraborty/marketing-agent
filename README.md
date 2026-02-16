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

- Python 3.11+ (Python 3.12+ required for ChromaDB vector search)
- Node.js 20+
- npm (bundled with Node.js)
- PostgreSQL (local or container) if you plan to wire up persistence
- **ChromaDB** (optional, for vector search) - **Requires Python 3.12+**. See installation instructions below. The app can run without it, but vector search features will be unavailable.
- **Ollama** (optional, for local LLM) - https://ollama.ai - install if using local LLM instead of OpenAI/Anthropic

### Backend Setup

**Important:** Always run backend commands from the `backend` directory to ensure Python can find the `app` module.

**If using ChromaDB (vector search):** You need Python 3.12+. Install it first, then create the virtual environment:

```bash
# Check Python version (should be 3.12+ for ChromaDB)
python3.12 --version

# If Python 3.12 is not available, install it first:
# macOS: brew install python@3.12
# Linux: Use your distribution's package manager
# Or download from: https://www.python.org/downloads/

cd backend
mkdir -p storage
python3.12 -m venv .venv  # Creates .venv with Python 3.12
source .venv/bin/activate  # Activate the virtual environment
pip install -e '.[dev]'  # This installs all dependencies including chromadb

# Initialize SQLite database
python scripts/init_database.py

# Initialize ChromaDB (optional, for vector search)
python scripts/init_chromadb.py

uvicorn app.main:app --reload
```

**If NOT using ChromaDB:** Python 3.11+ is sufficient:

```bash
cd backend
mkdir -p storage
python -m venv .venv  # Creates .venv in the backend directory
source .venv/bin/activate  # Activate the virtual environment
pip install -e '.[dev]'  # This installs all dependencies (ChromaDB will fail but app will work)

# Initialize SQLite database
python scripts/init_database.py

uvicorn app.main:app --reload
```

**Important:** Make sure your virtual environment is activated (you should see `(.venv)` in your terminal prompt) before running the app. 

**If you see "ChromaDB not available" error:**

The error message will now show the actual exception type and details. Common causes:

1. **Python version too old** - ChromaDB requires Python 3.12+:
   ```bash
   python --version  # Should show Python 3.12.x or higher
   # If not, install Python 3.12 and recreate venv:
   python3.12 -m venv .venv
   source .venv/bin/activate
   pip install -e '.[dev]'
   ```

2. **Python environment mismatch** - uvicorn might be using a different Python than your venv:
   ```bash
   which python  # Should show: backend/.venv/bin/python
   python --version  # Should show Python 3.12.x
   echo $VIRTUAL_ENV  # Should show: backend/.venv
   # Make sure uvicorn uses the venv Python:
   which uvicorn  # Should also point to venv
   ```

3. **Verify ChromaDB can be imported directly:**
   ```bash
   python -c "import chromadb; print(chromadb.__version__)"
   ```
   If this fails, check Python version first (must be 3.12+).

4. **Check the actual error message** - The startup logs will show the exception type (e.g., `ImportError`, `ModuleNotFoundError`, `AttributeError`). This helps diagnose the root cause.

5. **Reinstall ChromaDB if needed (with Python 3.12):**
   ```bash
   pip install chromadb --force-reinstall
   # Or reinstall all dependencies:
   pip install -e '.[dev]' --force-reinstall --no-cache-dir
   ```

**Directory Structure:**
- `.venv/` - Virtual environment (created in `backend/` directory)
- `storage/` - Data storage directory for databases and files
  - `storage/marketing_agent.db` - SQLite database (created by `init_database.py`)
  - `storage/vectors/` - ChromaDB vector database (created by `init_chromadb.py`)

**Note:** If you encounter `ModuleNotFoundError: No module named 'app'`, make sure you're running commands from the `backend` directory. The `app` module must be in Python's import path.

#### Database Initialization

The SQLite database needs to be initialized before first use. Run:

```bash
cd backend
source .venv/bin/activate
python scripts/init_database.py
```

**Troubleshooting "Failed to import encodings module" error:**

This error usually means the virtual environment is corrupted. Recreate it:

**Quick fix (recommended):**
```bash
cd backend
bash scripts/fix_venv.sh
```

**Manual fix:**
```bash
cd backend
# Remove the corrupted venv
rm -rf .venv

# Recreate with Python 3.12
python3.12 -m venv .venv
source .venv/bin/activate

# Upgrade pip and install dependencies
pip install --upgrade pip setuptools wheel
pip install -e '.[dev]'

# Now try again
python scripts/init_database.py
```

This creates all required tables:
- Cache tables (KPI precomputed, prompt-to-SQL cache)
- Campaign analysis tables (campaign_analysis, image_analysis_results, etc.)
- Campaigns table (for Klaviyo data)
- Dataset registry (for CSV ingestion)
- Email campaigns table (for campaign generation)

**Options:**
- List existing tables: `python scripts/init_database.py --list`
- Overwrite existing database (WARNING: deletes all data): `python scripts/init_database.py --overwrite`

#### ChromaDB Installation (Optional)

**Important:** ChromaDB requires Python 3.12+. Make sure you have Python 3.12 installed and activated before installing ChromaDB.

ChromaDB is included in the project dependencies (`pyproject.toml`) and should be installed automatically when you run `pip install -e '.[dev]'` **with Python 3.12**. **ChromaDB is optional** - the app will start and run without it, but vector search features will be unavailable.

**Setup steps for ChromaDB:**

1. **Install Python 3.12** (if not already installed):
   ```bash
   # macOS
   brew install python@3.12
   
   # Linux (Ubuntu/Debian)
   sudo apt-get install python3.12 python3.12-venv
   
   # Or download from https://www.python.org/downloads/
   ```

2. **Create virtual environment with Python 3.12:**
   ```bash
   cd backend
   python3.12 -m venv .venv
   source .venv/bin/activate
   pip install -e '.[dev]'  # This will install ChromaDB successfully
   ```

3. **Initialize ChromaDB (recommended):**
   ```bash
   python scripts/init_chromadb.py
   ```

This creates the default collection `UCO_Gear_Campaigns`. You can also:
- Use a custom collection name: `python scripts/init_chromadb.py --collection my_campaigns`
- Overwrite existing collection: `python scripts/init_chromadb.py --overwrite`
- List all collections: `python scripts/init_chromadb.py --list`

**Note:** ChromaDB will also automatically create the database directory and collections when first used, so initialization is optional but recommended.

If you see "ChromaDB not available" errors when trying to use vector search features, follow these steps:

1. **Ensure virtual environment is activated:**
   ```bash
   cd backend
   source .venv/bin/activate
   # You should see (.venv) in your prompt
   ```

2. **Install ChromaDB explicitly:**
   ```bash
   pip install chromadb
   ```

3. **Verify installation:**
   ```bash
   python -c "import chromadb; print(f'ChromaDB version: {chromadb.__version__}')"
   ```

4. **If still not working, reinstall all dependencies:**
   ```bash
   pip install -e '.[dev]' --force-reinstall --no-cache-dir
   ```

**Note:** The "requirement already met" message often means ChromaDB is installed in a different Python environment (system Python instead of your venv). Always activate the virtual environment before installing packages or running the app.

If you plan to use Ollama for embeddings, you'll also need to pull the embedding model:

```bash
ollama pull nomic-embed-text
```

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
