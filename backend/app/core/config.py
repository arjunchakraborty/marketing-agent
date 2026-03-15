"""Centralized application configuration and settings management."""
from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Sequence

from pydantic import AliasChoices, Field, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env from backend root (backend/.env) or app/core; missing file is ignored (e.g. on Vercel)
_THIS_DIR = Path(__file__).resolve().parent
_ENV_FILE = _THIS_DIR / ".env"
_BACKEND_ENV = _THIS_DIR.parent.parent / ".env"
_ENV_FILE_RESOLVED = _BACKEND_ENV if _BACKEND_ENV.exists() else _ENV_FILE


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE_RESOLVED),
        env_file_encoding="utf-8",
        extra="allow",
    )

    app_name: str = "Marketing Agent Backend"
    version: str = "0.1.0"
    api_prefix: str = "/api"

    database_url: str = "sqlite:///../storage/marketing_agent.db"
    analytics_schema: str = "analytics"
    ingestion_data_root: str = "/Users/kerrief/projects/mappe/data"

    # MongoDB (replaces PostgreSQL for document/NoSQL storage). On Vercel, set VERCEL_MONGODB_URI.
    mongodb_uri: str = Field(
        default="mongodb://localhost:27017",
        description="MongoDB connection URI (use Atlas SRV for Atlas)",
        validation_alias=AliasChoices("VERCEL_MONGODB_URI", "MONGODB_URI"),
    )
    mongodb_database: str = Field(default="marketing_agent", description="MongoDB database name")
    use_mongodb: bool = Field(default=False, description="Use MongoDB for document storage instead of PostgreSQL/SQLite")

    # Env read as string (comma-separated); parsed to list via computed field to avoid JSON parse errors
    _allowed_origins_env: str = Field(
        default="http://localhost:3000,http://localhost:2222",
        description="CORS allowed origins, comma-separated.",
        validation_alias=AliasChoices("ALLOWED_ORIGINS"),
    )

    @computed_field
    @property
    def allowed_origins(self) -> List[str]:
        if not self._allowed_origins_env or not self._allowed_origins_env.strip():
            return ["http://localhost:3000", "http://localhost:2222"]
        return [o.strip() for o in self._allowed_origins_env.split(",") if o.strip()]

    # Security Configuration (env read as string to support comma-separated list; parsed to list via computed field)
    _api_keys_env: str = Field(
        default="",
        description="API keys: set API_KEYS env var as comma-separated list (e.g. key1,key2). Empty = auth disabled.",
        validation_alias=AliasChoices("API_KEYS"),
    )

    @computed_field
    @property
    def api_keys(self) -> List[str]:
        if not self._api_keys_env or not self._api_keys_env.strip():
            return []
        return [k.strip() for k in self._api_keys_env.split(",") if k.strip()]

    # LLM Configuration
    openai_api_key: str = Field(default="", description="OpenAI API key for LLM workflows")
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI model for prompt-to-SQL and intelligence")
    anthropic_api_key: str = Field(default="", description="Anthropic API key (alternative LLM provider)")
    ollama_base_url: str = Field(default="http://localhost:11434", description="Ollama API base URL")
    ollama_model: str = Field(default="llama3.2", description="Ollama model name for prompt-to-SQL and intelligence")
    ollama_embedding_model: str = Field(default="nomic-embed-text", description="Ollama embedding model name for vector search")
    ollama_max_tables: int = Field(default=6, description="Maximum number of tables to include in Ollama prompt")
    ollama_max_columns: int = Field(default=15, description="Maximum number of columns per table to show in Ollama prompt")
    default_llm_provider: str = Field(default="ollama", description="Default LLM provider: openai, anthropic, or ollama")
    use_llm_for_sql: bool = Field(default=True, description="Use LLM for prompt-to-SQL generation")

    # Vector Search Configuration (MongoDB Atlas Vector Search replaces ChromaDB)
    enable_vector_search: bool = Field(default=True, description="Enable vector search for semantic discovery")
    vector_db_path: str = Field(default="storage/vectors", description="Path for ChromaDB fallback (when not using Atlas)")
    use_atlas_vector_search: bool = Field(default=False, description="Use MongoDB Atlas Vector Search instead of ChromaDB")
    mongodb_vector_index_name: str = Field(default="vector_index", description="Atlas Vector Search index name (create in Atlas UI with path 'embedding')")

    # ComfyUI Configuration
    comfyui_base_url: str = Field(default="http://localhost:8188", description="ComfyUI API base URL")
    comfyui_workflow_path: Optional[str] = Field(default="storage/Flux-Dev-ComfyUI-Workflow-api.json", description="Path to default ComfyUI workflow JSON file (relative to backend directory)")
    comfyui_model: str = Field(default="sd_xl_base_1.0.safetensors", description="ComfyUI model name for image generation")
    comfyui_timeout: int = Field(default=300, description="Timeout in seconds for ComfyUI image generation")
    comfyui_hero_image_size: str = Field(default="1200x600", description="Default size for hero images (format: WIDTHxHEIGHT)")
    
    # ComfyUI Cloud Configuration
    comfyui_cloud_api_key: str = Field(default="", description="ComfyUI Cloud API key for cloud workflows")
    comfyui_cloud_base_url: str = Field(default="", description="ComfyUI Cloud API base URL")
    comfyui_cloud_timeout: int = Field(default=300, description="Timeout in seconds for ComfyUI Cloud workflow execution")

    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL")
    log_experiments_debug: bool = Field(default=True, description="Enable DEBUG level logging for experiments and workflows")

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def _coerce_allowed_origins(cls, value: Sequence[str] | str) -> List[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return list(value)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
