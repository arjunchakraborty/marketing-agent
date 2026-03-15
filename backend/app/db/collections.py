"""MongoDB collection names (replaces SQL table names when use_mongodb=True)."""
# Document / NoSQL collections (replacing PostgreSQL tables)
COLL_CAMPAIGNS = "campaigns"
COLL_DATASET_REGISTRY = "dataset_registry"
COLL_EMAIL_CAMPAIGNS = "email_campaigns"
COLL_CAMPAIGN_ANALYSIS = "campaign_analysis"
COLL_IMAGE_ANALYSIS_RESULTS = "image_analysis_results"
COLL_EMAIL_FEATURE_CATALOG = "email_feature_catalog"
COLL_VISUAL_ELEMENT_CORRELATIONS = "visual_element_correlations"
COLL_EXPERIMENT_RUNS = "experiment_runs"
COLL_KPI_PRECOMPUTED = "kpi_precomputed_sql"
COLL_PROMPT_SQL_CACHE = "prompt_sql_cache"
COLL_TARGETED_CAMPAIGNS = "targeted_campaigns"

# Dynamic dataset collections: use table_name from dataset_registry as collection name
# (e.g. "avalon_sunshine_acquisition_sessions_over_time__avalon_sunshine_acquisition")

# Vector search: default collection for campaign/product embeddings (Atlas Vector Search)
DEFAULT_VECTOR_COLLECTION = "campaign_analyses"
