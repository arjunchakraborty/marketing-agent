# Marketing Agent Architecture Plan

## Scope

- Full-stack solution: Next.js UI + FastAPI backend orchestrating marketing intelligence workflows.
- Data ingestion pipeline for Shopify marketing/sales exports and APIs and direct CSV imports about eCommerce Store datasets (acquisition, behavior, customers, marketing, sales, BE Design Co.).
- Analytics layer mirroring TripleWhale capabilities: prompt-to-SQL exploration, cohort/flow analysis, product performance surfaces, inventory alerts, customizable insight widgets, and extensible plugin architecture for new data sources.
- Recommendation engine to generate campaign strategies and creative static/motion assets for marketing emails re-using report templates and branch assets and incorporating predictive uplift/forecast models.
- integration layer  with email gateways like Klaviyo for posting workflows with campaign calendar handoff, automated asset QA against brand guidelines, approval flows, and rollback guardrails.
- Native support for A2A and MCP-AGUI protocols across agent orchestration and UI embedding, with adapter layer prepared for additional AI standards (OpenAI Realtime, LangChain ReAct spec, Vercel AI SDK) pending confirmation.

## Approach

- Backend foundation in `backend/` for FastAPI services, analytics modules, shopify schema sync, predictive modeling, and CSV ingestion jobs for importing datasets about eCommerce Stores.
- Frontend workspace in `web/` using Next.js for dashboards, SQL-to-chart exploration, experiment planner, and campaign builders styled after TripleWhale UI patterns; expose MCP-AGUI endpoints for UI interoperability.
- Shared schema/contracts via OpenAPI + typed clients; persistent storage with PostgreSQL + SQLModel/SQLAlchemy; data lake staging for CSV ingestion; queue/orchestration for automations using A2A messaging.
- Modular agent workflow combining rule-based analytics, vector search, LLM planner-executor flows, compliance checks, and protocol adapters; adopt attachment-inspired prompt structures for consistent outputs.

## Milestones

- Define project scaffolding, core data contracts (Shopify/CSV schemas), plugin interfaces, and prompt/report template library; stand up baseline A2A/MCP-AGUI protocol contracts.
- Implement ingestion and normalization pipelines for batch CSV uploads from Avalon_Sunshine folders with protocol-aware event emission.
- Deliver analytics & predictive APIs for KPI rollups, cohort/anomaly detection, prompt-to-SQL execution, product/inventory insights, and forecasting; expose them via A2A actions and MCP-AGUI views.
- Build marketing insight dashboards, experiment planner, and recommendation flows using TripleWhale-inspired modules (email/SMS performance, product top lists, inventory alerts, customer segments) with real-time A2A updates.
- Integrate creative brief generator for static/motion content with brand guideline repository, automated asset QA, and protocol-driven collaboration/approval workflows.
- Enable social publishing automations with secure credential vaulting, approval flows, guardrails, rollback mechanisms, and protocol adapters for additional AI standards (OpenAI Realtime, LangChain ReAct, Vercel AI SDK) as they’re confirmed.

## Implementation Todos

- `setup-foundation`: Scaffold FastAPI backend, Next.js frontend, shared env/config, Postgres containers, plugin interfaces, and base A2A/MCP-AGUI contracts.
- `data-ingestion`: Implement CSV ingestion + normalization jobs into unified schemas with A2A event publishing.
- `analytics-engine`: Develop KPI computations, cohort/anomaly detection, prompt-to-SQL execution endpoints, product/inventory/customer insight views, forecasting models, reusable metric widgets, and A2A/MCP-AGUI exposure layers.
- `intelligence-layer`: Integrate LLM workflow for pattern summaries, campaign recommendations, visual analyses, experiment planning, and daily calendar generation using TripleWhale-style templates, backed by protocol adapters.
- `frontend-experience`: Implement dashboards, SQL explorer, experiment planner, campaign builder UX, and report templating in Next.js mirroring TripleWhale modules with collaboration features and MCP-AGUI compatibility.
- `social-integrations`: Build connectors for Klaviyo for campaign publishing with approval flows, asset QA, guardrails, rollback controls, and adapters for additional AI protocols.
- `qa-devops`: Establish automated tests, local orchestration, CI/CD, monitoring/logging, compliance checks for automations, and protocol conformance testing.

# Acceleration and Enhancements
- workflow processing for data files is to precompute the sql needed for calculate KPIs. And create an API that returns these KPIs to the UI
    Revenue: 'What is the total revenue for business  in the last 30 days?'
    AOV: 'What is the average order value (AOV) from all campaigns for business in the 30 days before the last 30 days?',
    Conversion Rate: 'What is the average conversion rate from all campaigns for business  in the last 30 days?',
    'Email CTR': 'What is the average email click-through rate (CTR) from all email campaigns in the 30 days before the last 30 days?',
- In general, all SQL except the one which accepts a SQL prompt should be generated ahead of time and stored in the database
- Implement caching layer for prompt-to-SQL conversion: store natural language prompt → SQL query mappings in database with hash-based lookup (normalize prompts via case-insensitive, whitespace-normalized hashing). Cache entries should include prompt hash, generated SQL, execution metadata (schema version, timestamp), and usage statistics. Cache population occurs in two phases: (1) initial population during data load/ingestion workflows where common KPI and analysis prompts are pre-generated and cached, (2) incremental population as users interact with the app—when a prompt-to-SQL request is made, check cache first before invoking LLM; if cache miss, generate SQL via LLM and store result in cache for future use. Invalidate cache entries when schema changes or after configurable TTL. This reduces LLM API costs and improves response latency for repeated or similar queries.