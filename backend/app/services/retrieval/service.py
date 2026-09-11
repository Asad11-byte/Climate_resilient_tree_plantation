"""
Hybrid retrieval orchestration.

"Hybrid" here means what it's supposed to mean: dense vector search (Jina
embeddings -> Qdrant cosine similarity) fused with sparse/lexical search
(BM25 over the same chunks), combined via Reciprocal Rank Fusion (RRF) —
not just vector search + metadata filtering. BM25 catches exact-term
matches (species names, abbreviations like "D. sissoo", specific numbers)
that a dense embedding can under-weight; vector search catches paraphrases
and conceptual matches BM25 can't. Fusing by rank position (not raw score)
avoids having to normalize two scores that live on completely different
scales (cosine similarity vs. BM25).

Full pipeline:
  query -> embed -> Qdrant vector search (with optional metadata filter)
        -> BM25 lexical search (same filter applied)
        -> Reciprocal Rank Fusion
        -> Jina rerank -> final top-k chunks

This module coordinates providers; it does not talk to Groq, and it does
not know about HTTP/FastAPI. If retrieval finds nothing, it raises
InsufficientEvidenceError rather than returning an empty-but-ok result —
callers (the chat service) must treat that as "say evidence is
unavailable", not silently proceed to the LLM with no context.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.core.exceptions import InsufficientEvidenceError
from app.core.logging import get_logger
from app.services.embeddings.base import EmbeddingProvider
from app.services.rerank.base import RerankerProvider
from app.services.retrieval.bm25_index import BM25Index
from app.services.vectorstore.base import VectorSearchResult, VectorStore

logger = get_logger(__name__)

# Reciprocal Rank Fusion constant. 60 is the standard value from the
# original RRF paper (Cormack et al.) and is not sensitive to tuning —
# it just controls how quickly a lower rank position's contribution decays.
RRF_K = 60


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
        bm25_index: Optional[BM25Index] = None,
        top_k_candidates: int = 35,
        top_k_final: int = 5,
        min_relevance_score: Optional[float] = None,
    ):
        self._embeddings = embedding_provider
        self._vector_store = vector_store
        self._reranker = reranker
        self._bm25_index = bm25_index
        self._top_k_candidates = top_k_candidates
        self._top_k_final = top_k_final
        self._min_relevance_score = min_relevance_score

    def _above_threshold(self, chunk: "RetrievedChunk") -> bool:
        if self._min_relevance_score is None:
            return True
        score = chunk.rerank_score if chunk.rerank_score is not None else chunk.vector_score
        return score >= self._min_relevance_score

    async def _fuse_dense_and_bm25(
        self,
        query: str,
        dense_candidates: List[VectorSearchResult],
        metadata_filter: Optional[Dict[str, Any]],
    ) -> List[VectorSearchResult]:
        if self._bm25_index is None:
            return dense_candidates

        try:
            bm25_hits = await self._bm25_index.query(
                query, top_k=self._top_k_candidates, metadata_filter=metadata_filter
            )
        except Exception:  # noqa: BLE001
            # BM25 is an enhancement layer, same philosophy as the reranker
            # fallback below — a broken lexical index shouldn't take down
            # retrieval, it should just degrade to dense-only.
            logger.warning("BM25 index unavailable, falling back to dense-only candidates")
            return dense_candidates

        if not bm25_hits:
            return dense_candidates

        fused_scores: Dict[str, float] = {}
        payload_by_id: Dict[str, Dict[str, Any]] = {}

        for rank, c in enumerate(dense_candidates):
            fused_scores[c.id] = fused_scores.get(c.id, 0.0) + 1.0 / (RRF_K + rank + 1)
            payload_by_id[c.id] = c.payload

        for rank, hit in enumerate(bm25_hits):
            fused_scores[hit.id] = fused_scores.get(hit.id, 0.0) + 1.0 / (RRF_K + rank + 1)
            payload_by_id.setdefault(hit.id, hit.payload)

        fused_ids = sorted(fused_scores, key=lambda i: fused_scores[i], reverse=True)
        fused_ids = fused_ids[: self._top_k_candidates]

        return [
            VectorSearchResult(id=i, score=fused_scores[i], payload=payload_by_id[i])
            for i in fused_ids
        ]

    async def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievedChunk]:
        final_k = top_k or self._top_k_final

        query_vector = await self._embeddings.embed_query(query)
        dense_candidates = await self._vector_store.search(
            query_vector=query_vector,
            top_k=self._top_k_candidates,
            metadata_filter=metadata_filter,
        )

        # Fusing happens even when dense search comes back empty — a query
        # that's mostly exact terminology (a species name, an acronym) can
        # legitimately score near-zero on embedding similarity but still
        # have a real BM25 match. Raising InsufficientEvidenceError before
        # trying BM25 would throw away exactly the case hybrid search
        # exists to catch.
        candidates = await self._fuse_dense_and_bm25(query, dense_candidates, metadata_filter)

        if not candidates:
            raise InsufficientEvidenceError(
                "No relevant evidence found in the knowledge base for this query."
            )

        candidate_texts = [c.payload.get("text", "") for c in candidates]
        try:
            reranked = await self._reranker.rerank(query, candidate_texts, top_k=final_k)
        except Exception:  # noqa: BLE001
            # Reranking is an enhancement, not a hard dependency for retrieval
            # to function — fall back to fused-score ordering rather than
            # failing the whole request.
            logger.warning("Reranker unavailable, falling back to fused-score ordering")
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