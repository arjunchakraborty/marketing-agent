Marketing Agent Architecture Plan
Scope
Full-stack solution: Next.js UI + FastAPI backend orchestrating marketing intelligence workflows.
Data ingestion pipeline for Shopify marketing/sales exports and APIs, TripleWhale-style data sync, and direct CSV imports from the provided Avalon_Sunshine datasets (acquisition, behavior, customers, marketing, sales, BE Design Co.).
Analytics layer mirroring TripleWhale capabilities: prompt-to-SQL exploration, cohort/flow analysis, product performance surfaces, inventory alerts, customizable insight widgets, and extensible plugin architecture for new data sources.
Recommendation engine to generate campaign strategies and creative briefs for static/motion assets, re-using report templates inspired by the provided workflows (email/SMS strategy briefs, visual analysis buckets, daily calendars) and incorporating predictive uplift/forecast models.
Social media integration layer covering Meta, LinkedIn, TikTok, and Twitter/X posting workflows with campaign calendar handoff, automated asset QA against brand guidelines, approval flows, and rollback guardrails.
Native support for A2A and MCP-AGUI protocols across agent orchestration and UI embedding, with adapter layer prepared for additional AI standards (OpenAI Realtime, LangChain ReAct spec, Vercel AI SDK) pending confirmation.
Secure workspace management with Google Sign-In, user provisioning, and role-based access control across data, analytics, and publishing features.
Approach
Backend foundation in backend/ for FastAPI services, analytics modules, TripleWhale-compatible schema sync, predictive modeling, CSV ingestion jobs referencing the Avalon_Sunshine sources, and Google OAuth-based identity service.
Frontend workspace in web/ using Next.js for dashboards, SQL-to-chart exploration, experiment planner, and campaign builders styled after TripleWhale UI patterns; expose MCP-AGUI endpoints for UI interoperability and integrate Google login flows.
Shared schema/contracts via OpenAPI + typed clients; persistent storage with PostgreSQL + SQLModel/SQLAlchemy; data lake staging for CSV ingestion; queue/orchestration for automations using A2A messaging.
Modular agent workflow combining rule-based analytics, vector search, LLM planner-executor flows, compliance checks, and protocol adapters; adopt attachment-inspired prompt structures for consistent outputs.
Milestones
Define project scaffolding, core data contracts (Shopify/TripleWhale/Avalon CSV schemas), plugin interfaces, prompt/report template library, and identity architecture (Google OAuth + RBAC) with baseline A2A/MCP-AGUI protocol contracts.
Implement ingestion and normalization pipelines for Shopify API, TripleWhale datasets, and batch CSV uploads from Avalon_Sunshine folders with protocol-aware event emission and user access controls.
Deliver analytics & predictive APIs for KPI rollups, cohort/anomaly detection, prompt-to-SQL execution, product/inventory insights, and forecasting; expose them via A2A actions, MCP-AGUI views, and secured user roles.
Build marketing insight dashboards, experiment planner, and recommendation flows using TripleWhale-inspired modules (email/SMS performance, product top lists, inventory alerts, customer segments) with real-time A2A updates and Google-authenticated collaboration.
Integrate creative brief generator for static/motion content with brand guideline repository, automated asset QA, protocol-driven collaboration/approval workflows, and role-aware access.
Enable social publishing automations with secure credential vaulting, approval flows, guardrails, rollback mechanisms, adapters for additional AI standards, and user-specific permissions.
Implementation Todos
setup-foundation: Scaffold FastAPI backend, Next.js frontend, shared env/config, Postgres containers, plugin interfaces, base A2A/MCP-AGUI contracts, and Google OAuth authentication.
data-ingestion: Implement Shopify API, TripleWhale connectors, and Avalon_Sunshine CSV ingestion + normalization jobs into unified schemas with A2A event publishing and permission scoping.
analytics-engine: Develop KPI computations, cohort/anomaly detection, prompt-to-SQL execution endpoints, product/inventory/customer insight views, forecasting models, reusable metric widgets, and A2A/MCP-AGUI exposure layers respecting RBAC.
intelligence-layer: Integrate LLM workflow for pattern summaries, campaign recommendations, visual analyses, experiment planning, and daily calendar generation using TripleWhale-style templates, backed by protocol adapters and user context.
frontend-experience: Implement dashboards, SQL explorer, experiment planner, campaign builder UX, and report templating in Next.js mirroring TripleWhale modules with collaboration features, Google-authenticated sessions, and MCP-AGUI compatibility.
social-integrations: Build connectors for Meta, LinkedIn, TikTok, and Twitter/X for campaign publishing with approval flows, asset QA, guardrails, rollback controls, adapters for additional AI protocols, and permission-aware access.
qa-devops: Establish automated tests, local orchestration, CI/CD, monitoring/logging, compliance checks for automations, identity/protocol conformance testing, and incident response playbooks.
# marketing-agent
