"""Application configuration via Pydantic Settings."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_ENV_FILE = _BACKEND_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM (OpenAI-compatible — set OPENAI_BASE_URL for OpenRouter)
    openai_api_key: str = ""
    openai_model: str = "openai/gpt-4o-mini"
    openai_base_url: str | None = None

    # Embeddings & re-ranking (local, no API key)
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # Chunking
    chunk_size: int = 700
    chunk_overlap: int = 100

    # Retrieval
    faiss_top_k: int = 20
    rerank_top_n: int = 5

    # Startup — preload embedding model so first upload is fast
    preload_models: bool = True

    # Paths
    data_dir: Path = Path(__file__).resolve().parent.parent / "data"
    upload_dir: Path = data_dir / "uploads"
    faiss_dir: Path = data_dir / "faiss_index"
    eval_log_path: Path = data_dir / "eval_logs" / "ragas_metrics.jsonl"

    # CORS
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.faiss_dir.mkdir(parents=True, exist_ok=True)
    settings.eval_log_path.parent.mkdir(parents=True, exist_ok=True)
    return settings


def reload_settings() -> Settings:
    """Clear cached settings (e.g. after editing .env)."""
    get_settings.cache_clear()
    return get_settings()
