"""Centralized application configuration and settings management."""
from functools import lru_cache
from typing import List, Sequence

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
    use_llm_for_sql: bool = Field(default=True, description="Use LLM for prompt-to-SQL generation")

    # Vector Search Configuration
    enable_vector_search: bool = Field(default=False, description="Enable vector search for semantic discovery")
    vector_db_path: str = Field(default="../storage/vectors", description="Path for vector database storage")

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
