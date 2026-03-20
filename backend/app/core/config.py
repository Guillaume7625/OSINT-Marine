from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Local Claude Assistant"
    app_env: Literal["dev", "test", "prod"] = "dev"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    frontend_origin: str = "http://localhost:3000"
    auto_migrate_on_startup: bool = True

    database_url: str = "postgresql+psycopg://assistant:assistant@localhost:5432/assistant"
    redis_url: str = "redis://localhost:6379/0"

    anthropic_api_key: str = ""
    anthropic_default_model: str = "claude-sonnet-4-6"
    anthropic_model_fast: str = "claude-haiku-4-5"
    anthropic_model_default: str = "claude-sonnet-4-6"
    anthropic_model_complex: str = "claude-opus-4-6"
    anthropic_timeout_seconds: float = 60.0
    anthropic_max_tokens: int = 2048

    default_provider: str = "anthropic"
    default_routing_mode: Literal["policy", "manual", "locked"] = "policy"
    default_context_window_messages: int = 20
    max_tool_iterations: int = 4

    upload_root: Path = Path("./backend_data/uploads")
    rag_chunk_size: int = 1000
    rag_chunk_overlap: int = 200
    rag_top_k: int = 4
    embedding_backend: Literal["sentence-transformers"] = "sentence-transformers"
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    embedding_batch_size: int = 32

    bootstrap_global_prompt: str = "You are a precise and helpful assistant."
    bootstrap_workspace_prompt: str = "You are running in a local-first MVP workspace."


@lru_cache
def get_settings() -> Settings:
    return Settings()
