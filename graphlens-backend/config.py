"""Centralised application configuration, loaded from environment / .env."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- LLM / embeddings ---
    openai_api_key: str = ""
    embedding_model: str = "text-embedding-3-large"
    llm_model: str = "gpt-4o"
    # text-embedding-3-large default is 3072; trim to 1536 to halve storage.
    embedding_dimensions: int = 3072

    # --- Vector store ---
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    qdrant_collection: str = "graphlens_docs"

    # --- Datastores ---
    database_url: str = "postgresql+psycopg2://graphlens:graphlens@localhost:5432/graphlens"
    redis_url: str = "redis://localhost:6379"

    # --- Auth ---
    jwt_secret: str = "change-me-in-prod"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24

    # --- Uploads ---
    max_upload_mb: int = 10

    # --- CORS ---
    cors_origins: list[str] = ["http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
