"""
In-memory BM25 lexical index, built from whatever's currently in the
vector store (via VectorStore.scroll_all()). This is the "sparse"/keyword
half of hybrid search — it complements dense vector search by catching
exact-term matches (species names, specific numbers, abbreviations like
"D. sissoo") that an embedding can under-weight.

Deliberately simple for FYP scale: no persistent index, no incremental
updates — the whole corpus is small enough (a handful of research papers)
that rebuilding on a cache-miss is cheap. If the corpus grows much larger,
this would need a real inverted-index store instead of an in-memory
rebuild, but that's not a problem this project has yet.
"""
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from rank_bm25 import BM25Okapi

from app.core.logging import get_logger
from app.services.vectorstore.base import VectorStore

logger = get_logger(__name__)

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> List[str]:
    return _TOKEN_RE.findall(text.lower())


@dataclass
class BM25Hit:
    id: str
    score: float
    payload: Dict[str, Any]


class BM25Index:
    def __init__(self, vector_store: VectorStore):
        self._vector_store = vector_store
        self._bm25: Optional[BM25Okapi] = None
        self._ids: List[str] = []
        self._payloads: List[Dict[str, Any]] = []
        self._built_for_filter: Any = "__unbuilt__"  # sentinel, never a real filter value

    async def _ensure_built(self, metadata_filter: Optional[Dict[str, Any]]) -> None:
        if self._bm25 is not None and self._built_for_filter == metadata_filter:
            return
        await self.rebuild(metadata_filter)

    async def rebuild(self, metadata_filter: Optional[Dict[str, Any]] = None) -> None:
        """Re-fetches chunks matching `metadata_filter` from the vector
        store and rebuilds the index from scratch. Call this after
        ingestion changes the corpus — the index doesn't auto-refresh on
        its own, since ingestion and retrieval are separate
        processes/requests. Also rebuilds automatically (via
        _ensure_built) whenever a query's filter differs from the one this
        index was last built for — a filtered query needs a filtered
        corpus, otherwise BM25's term-frequency statistics would be skewed
        by out-of-scope documents."""
        points = await self._vector_store.scroll_all(metadata_filter=metadata_filter)
        self._ids = []
        self._payloads = []
        corpus_tokens: List[List[str]] = []

        for point in points:
            text = point.payload.get("text", "")
            if not text.strip():
                continue
            self._ids.append(point.id)
            self._payloads.append(point.payload)
            corpus_tokens.append(_tokenize(text))

        self._built_for_filter = metadata_filter
        if not corpus_tokens:
            self._bm25 = None
            logger.warning("BM25 index rebuild found no chunks to index (filter=%s)", metadata_filter)
            return

        self._bm25 = BM25Okapi(corpus_tokens)
        logger.info("BM25 index built over %d chunks (filter=%s)", len(corpus_tokens), metadata_filter)

    async def query(
        self, text: str, top_k: int, metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[BM25Hit]:
        await self._ensure_built(metadata_filter)
        if self._bm25 is None:
            return []

        query_tokens = _tokenize(text)
        if not query_tokens:
            return []

        scores = self._bm25.get_scores(query_tokens)
        ranked: List[Tuple[int, float]] = sorted(
            enumerate(scores), key=lambda pair: pair[1], reverse=True
        )[:top_k]

        return [
            BM25Hit(id=self._ids[i], score=score, payload=self._payloads[i])
            for i, score in ranked
            if score > 0  # a zero BM25 score means no query term matched at all
        ]