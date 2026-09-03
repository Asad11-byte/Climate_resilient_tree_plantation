"""
Hybrid retrieval orchestration.

Architecture (matches master prompt section 10):
  query -> embed -> Qdrant vector search (with optional metadata filter)
        -> Jina rerank -> final top-k chunks

This module coordinates providers; it does not talk to Groq, and it does
not know about HTTP/FastAPI. If retrieval finds nothing, it raises
InsufficientEvidenceError rather than returning an empty-but-ok result —
callers (the chat service, in Phase 3) must treat that as "say evidence is
unavailable", not silently proceed to the LLM with no context.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.core.exceptions import InsufficientEvidenceError
from app.core.logging import get_logger
from app.services.embeddings.base import EmbeddingProvider
from app.services.rerank.base import RerankerProvider
from app.services.vectorstore.base import VectorStore

logger = get_logger(__name__)


@dataclass
class RetrievedChunk:
    id: str
    text: str
    vector_score: float
    rerank_score: Optional[float]
    payload: Dict[str, Any] = field(default_factory=dict)


class RetrievalService:
    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
        reranker: RerankerProvider,
        top_k_candidates: int = 20,
        top_k_final: int = 5,
        min_relevance_score: Optional[float] = None,
    ):
        self._embeddings = embedding_provider
        self._vector_store = vector_store
        self._reranker = reranker
        self._top_k_candidates = top_k_candidates
        self._top_k_final = top_k_final
        self._min_relevance_score = min_relevance_score

    def _above_threshold(self, chunk: "RetrievedChunk") -> bool:
        if self._min_relevance_score is None:
            return True
        score = chunk.rerank_score if chunk.rerank_score is not None else chunk.vector_score
        return score >= self._min_relevance_score

    async def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievedChunk]:
        final_k = top_k or self._top_k_final

        query_vector = await self._embeddings.embed_query(query)
        candidates = await self._vector_store.search(
            query_vector=query_vector,
            top_k=self._top_k_candidates,
            metadata_filter=metadata_filter,
        )

        if not candidates:
            raise InsufficientEvidenceError(
                "No relevant evidence found in the knowledge base for this query."
            )

        candidate_texts = [c.payload.get("text", "") for c in candidates]
        try:
            reranked = await self._reranker.rerank(query, candidate_texts, top_k=final_k)
        except Exception:  # noqa: BLE001
            # Reranking is an enhancement, not a hard dependency for retrieval
            # to function — fall back to vector-score ordering rather than
            # failing the whole request.
            logger.warning("Reranker unavailable, falling back to vector-score ordering")
            top = sorted(candidates, key=lambda c: c.score, reverse=True)[:final_k]
            results = [
                RetrievedChunk(
                    id=c.id, text=c.payload.get("text", ""), vector_score=c.score,
                    rerank_score=None, payload=c.payload,
                )
                for c in top
            ]
            results = [r for r in results if self._above_threshold(r)]
            if not results:
                raise InsufficientEvidenceError(
                    "No sufficiently relevant evidence found for this query."
                )
            return results

        results: List[RetrievedChunk] = []
        for r in reranked:
            c = candidates[r.index]
            results.append(
                RetrievedChunk(
                    id=c.id,
                    text=c.payload.get("text", ""),
                    vector_score=c.score,
                    rerank_score=r.score,
                    payload=c.payload,
                )
            )
        results = [r for r in results if self._above_threshold(r)]
        if not results:
            raise InsufficientEvidenceError(
                "No sufficiently relevant evidence found for this query."
            )
        return results
