"""Centralized application configuration and settings management."""
from functools import lru_cache
from typing import List, Optional, Sequence

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")

    app_name: str = "Marketing Agent Backend"
    version: str = "0.1.0"
    api_prefix: str = "/api"

    database_url: str = "sqlite:///../storage/marketing_agent.db"
    analytics_schema: str = "analytics"
    ingestion_data_root: str = "/Users/kerrief/projects/mappe/data"

    allowed_origins: List[str] = Field(default_factory=lambda: ["http://localhost:3000"])

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

    # Vector Search Configuration
    enable_vector_search: bool = Field(default=True, description="Enable vector search for semantic discovery")
    vector_db_path: str = Field(default="storage/vectors", description="Path for vector database storage (relative to backend directory)")

    # ComfyUI Configuration
    comfyui_base_url: str = Field(default="http://localhost:8188", description="ComfyUI API base URL")
    comfyui_workflow_path: Optional[str] = Field(default="/Users/a0c1fjt/work/marketing-agent/backend/storage/Flux-Dev-ComfyUI-Workflow-api.json", description="Path to default ComfyUI workflow JSON file")
    comfyui_model: str = Field(default="sd_xl_base_1.0.safetensors", description="ComfyUI model name for image generation")
    comfyui_timeout: int = Field(default=300, description="Timeout in seconds for ComfyUI image generation")
    comfyui_hero_image_size: str = Field(default="1200x600", description="Default size for hero images (format: WIDTHxHEIGHT)")

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
