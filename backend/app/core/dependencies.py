"""
Dependency wiring.

This is the ONE place that maps an interface to a concrete provider.
Every router/service asks FastAPI for the *interface* type via Depends();
this module decides which implementation actually gets constructed.

To swap Groq for another LLM provider later: implement LLMProvider in a new
file, change `get_llm_provider` below to construct it instead. Nothing else
in the codebase needs to change.
"""
from functools import lru_cache

from fastapi import Depends
from supabase import Client

from app.core.config import Settings, get_settings
from app.repositories.base import build_supabase_client
from app.repositories.environmental_repository import EnvironmentalRepository
from app.repositories.species_repository import SpeciesRepository
from app.services.embeddings.base import EmbeddingProvider
from app.services.embeddings.jina_provider import JinaEmbeddingProvider
from app.services.llm.base import LLMProvider
from app.services.llm.groq_provider import GroqProvider
from app.services.rerank.base import RerankerProvider
from app.services.rerank.jina_reranker import JinaReranker
from app.services.chat.service import ChatService
from app.services.ingestion.pipeline import IngestionPipeline
from app.services.environment.nasa_power_provider import NasaPowerProvider
from app.services.environment.service import EnvironmentDataService
from app.services.environment.soilgrids_provider import SoilGridsProvider
from app.services.environment.soilgrids_gee_provider import SoilGridsGEEProvider
from app.services.environment.sentinel_provider import SentinelProvider
from app.services.retrieval.bm25_index import BM25Index
from app.services.retrieval.service import RetrievalService
from app.services.vectorstore.base import VectorStore
from app.services.vectorstore.qdrant_store import QdrantVectorStore


@lru_cache
def get_llm_provider() -> LLMProvider:
    return GroqProvider(get_settings())


@lru_cache
def get_embedding_provider() -> EmbeddingProvider:
    return JinaEmbeddingProvider(get_settings())


@lru_cache
def get_reranker_provider() -> RerankerProvider:
    return JinaReranker(get_settings())


@lru_cache
def get_vector_store() -> VectorStore:
    return QdrantVectorStore(get_settings())


@lru_cache
def get_supabase_client() -> Client:
    settings: Settings = get_settings()
    return build_supabase_client(settings)


def get_species_repository() -> SpeciesRepository:
    return SpeciesRepository(get_supabase_client())


def get_environmental_repository() -> EnvironmentalRepository:
    return EnvironmentalRepository(get_supabase_client())


@lru_cache
def get_bm25_index() -> BM25Index:
    """One BM25Index per process, shared across requests — it lazily
    builds/rebuilds itself per metadata filter (see BM25Index._ensure_built),
    so this doesn't need its own cache-invalidation logic here."""
    return BM25Index(get_vector_store())


@lru_cache
def get_retrieval_service() -> RetrievalService:
    settings: Settings = get_settings()
    return RetrievalService(
        embedding_provider=get_embedding_provider(),
        vector_store=get_vector_store(),
        reranker=get_reranker_provider(),
        bm25_index=get_bm25_index(),
        top_k_candidates=settings.retrieval_top_k_candidates,
        top_k_final=settings.retrieval_top_k_final,
        min_relevance_score=settings.retrieval_min_relevance_score,
    )


@lru_cache
def get_ingestion_pipeline() -> IngestionPipeline:
    return IngestionPipeline(
        embedding_provider=get_embedding_provider(),
        vector_store=get_vector_store(),
    )


@lru_cache
def get_soilgrids_provider() -> SoilGridsProvider:
    return SoilGridsProvider(get_settings())


@lru_cache
def get_soilgrids_gee_provider() -> SoilGridsGEEProvider:
    return SoilGridsGEEProvider(get_settings())


@lru_cache
def get_sentinel_provider() -> SentinelProvider:
    return SentinelProvider(get_settings())


@lru_cache
def get_nasa_power_provider() -> NasaPowerProvider:
    return NasaPowerProvider(get_settings())


@lru_cache
def get_environment_service() -> EnvironmentDataService:
    settings: Settings = get_settings()
    # soilgrids_gee is listed ahead of soilgrids (REST): ISRIC has paused
    # the REST service (see soilgrids_provider.py's module docstring), so
    # the Earth-Engine-backed provider is the one that actually returns
    # data right now. The REST provider stays in the list so it resumes
    # contributing automatically once ISRIC restores it.
    return EnvironmentDataService(
        repository=get_environmental_repository(),
        providers=[
            get_soilgrids_gee_provider(),
            get_soilgrids_provider(),
            get_sentinel_provider(),
            get_nasa_power_provider(),
        ],
        cache_tolerance=settings.environment_cache_tolerance_degrees,
    )


@lru_cache
def get_chat_service() -> ChatService:
    return ChatService(
        retrieval_service=get_retrieval_service(),
        llm_provider=get_llm_provider(),
        environment_service=get_environment_service(),
    )