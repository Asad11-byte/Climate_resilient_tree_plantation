"""
Centralized application configuration.

Rule: no service, repository, or router reads os.environ directly.
Everything comes through `get_settings()` so config has one source of truth
and can be overridden cleanly in tests.
"""
from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- App ---
    app_name: str = "Tree Plantation AI"
    environment: str = Field(default="development")
    debug: bool = Field(default=True)
    api_prefix: str = "/api"
    cors_origins: List[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    # --- Groq (LLM generation) ---
    groq_api_key: str = Field(default="")
    groq_base_url: str = Field(default="https://api.groq.com/openai/v1")
    groq_model: str = Field(default="openai/gpt-oss-120b")
    groq_fast_model: str = Field(default="openai/gpt-oss-20b")
    groq_temperature: float = Field(default=0.2)
    groq_max_tokens: int = Field(default=1500)
    groq_timeout_seconds: float = Field(default=30.0)

    # --- Jina (embeddings + reranker) ---
    jina_api_key: str = Field(default="")
    jina_embeddings_url: str = Field(default="https://api.jina.ai/v1/embeddings")
    jina_rerank_url: str = Field(default="https://api.jina.ai/v1/rerank")
    jina_embedding_model: str = Field(default="jina-embeddings-v3")
    jina_rerank_model: str = Field(default="jina-reranker-v2-base-multilingual")

    # --- Qdrant ---
    qdrant_url: str = Field(default="")
    qdrant_api_key: str = Field(default="")
    qdrant_collection: str = Field(default="mandi_tree_knowledge")
    qdrant_vector_size: int = Field(default=1024)
    qdrant_timeout_seconds: float = Field(default=10.0)

    # --- Supabase ---
    supabase_url: str = Field(default="")
    supabase_key: str = Field(default="")

    # --- Retrieval defaults ---
    retrieval_top_k_candidates: int = Field(default=20)
    retrieval_top_k_final: int = Field(default=5)
    retrieval_min_relevance_score: float = Field(
        default=0.05,
        description=(
            "Minimum rerank (or vector, if reranker is unavailable) score a "
            "chunk must clear to count as evidence. Prevents a weak top match "
            "on an off-topic query from being passed to the LLM as if it were "
            "relevant. Tune this after testing against the real Jina reranker "
            "— its score distribution differs from the fallback vector score."
        ),
    )
        # Google Earth Engine (shared by SoilGridsGEEProvider and SentinelProvider)
    gee_service_account_email: Optional[str] = None
    gee_service_account_key_path: Optional[str] = None  # path to the downloaded JSON key file
    gee_service_account_key_json: Optional[str] = None  # or the key JSON inline — use one or the other

    # --- Environmental data (Phase 5) ---
    soilgrids_base_url: str = Field(default="https://rest.isric.org/soilgrids/v2.0/properties/query")
    nasa_power_base_url: str = Field(default="https://power.larc.nasa.gov/api/temporal/climatology/point")
    environment_provider_timeout_seconds: float = Field(default=15.0)
    environment_cache_tolerance_degrees: float = Field(
        default=0.05,
        description="How close (in degrees) a cached environmental_data row must be to count as a match for a given coordinate — roughly a few km.",
    )


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — import this, not Settings() directly."""
    return Settings()
