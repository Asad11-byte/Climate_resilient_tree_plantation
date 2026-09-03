from typing import Dict

from pydantic import BaseModel


class ServiceStatus(BaseModel):
    groq: bool
    jina_embeddings: bool
    jina_reranker: bool
    qdrant: bool
    supabase: bool


class HealthResponse(BaseModel):
    status: str  # "ok" | "degraded"
    services: ServiceStatus
    details: Dict[str, str] = {}
