from fastapi import APIRouter

from app.core.dependencies import (
    get_embedding_provider,
    get_llm_provider,
    get_reranker_provider,
    get_species_repository,
    get_vector_store,
)
from app.schemas.health import HealthResponse, ServiceStatus

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """
    Checks connectivity to every external dependency independently.
    Both *constructing* a provider (e.g. missing credentials) and *calling*
    it are wrapped together, so a misconfigured or unreachable service shows
    up as "degraded" in the response instead of a 500 for the whole endpoint.
    """
    details = {}

    async def safe_check(name: str, factory, call) -> bool:
        try:
            instance = factory()
            return await call(instance)
        except Exception as exc:  # noqa: BLE001
            details[name] = type(exc).__name__
            return False

    groq_ok = await safe_check("groq", get_llm_provider, lambda p: p.health_check())
    jina_embed_ok = await safe_check(
        "jina_embeddings", get_embedding_provider, lambda p: p.health_check()
    )
    jina_rerank_ok = await safe_check(
        "jina_reranker", get_reranker_provider, lambda p: p.health_check()
    )
    qdrant_ok = await safe_check("qdrant", get_vector_store, lambda p: p.health_check())
    supabase_ok = await safe_check(
        "supabase", get_species_repository, lambda p: p.health_check()
    )

    statuses = ServiceStatus(
        groq=groq_ok,
        jina_embeddings=jina_embed_ok,
        jina_reranker=jina_rerank_ok,
        qdrant=qdrant_ok,
        supabase=supabase_ok,
    )
    overall = "ok" if all(statuses.model_dump().values()) else "degraded"
    return HealthResponse(status=overall, services=statuses, details=details)
