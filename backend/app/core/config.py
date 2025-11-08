"""Centralized application configuration and settings management."""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")

    app_name: str = "Marketing Agent Backend"
    version: str = "0.1.0"
    api_prefix: str = "/api"

    database_url: str = "postgresql+psycopg://marketing_agent:marketing_agent@localhost:5432/marketing_agent"
    analytics_schema: str = "analytics"
    ingestion_bucket: str = "local-data-ingestion"

    allowed_origins: List[str] = ["http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
