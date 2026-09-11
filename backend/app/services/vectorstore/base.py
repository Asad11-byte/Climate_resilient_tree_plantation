from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class VectorRecord:
    id: str
    vector: List[float]
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VectorSearchResult:
    id: str
    score: float
    payload: Dict[str, Any] = field(default_factory=dict)


class VectorStore(ABC):
    @abstractmethod
    async def ensure_collection(self) -> None:
        """Create the collection if it doesn't exist. Idempotent."""
        raise NotImplementedError

    @abstractmethod
    async def upsert(self, records: List[VectorRecord]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def search(
        self,
        query_vector: List[float],
        top_k: int,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[VectorSearchResult]:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, ids: List[str]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete_by_metadata(self, metadata_filter: Dict[str, Any]) -> None:
        """Delete every point matching the given payload filter (e.g.
        {"document_id": "..."}). Used by the ingestion pipeline to purge a
        document's old chunks before upserting its new ones — necessary
        because chunk count can change between re-ingestions (e.g. a
        chunking-strategy change), which point-ID-based upsert alone can't
        clean up: point IDs are derived from chunk_index, so if a document
        goes from N chunks to M < N chunks, the old chunks at indices
        M..N-1 would otherwise never be touched by the new upsert."""
        raise NotImplementedError

    @abstractmethod
    async def scroll_all(
        self, metadata_filter: Optional[Dict[str, Any]] = None, limit: int = 5000
    ) -> List[VectorSearchResult]:
        """Returns every point's id + payload (no vectors) matching the
        optional filter. Used to build the in-memory BM25 lexical index for
        hybrid search — BM25 needs the full text corpus (or a
        metadata-scoped slice of it), not a vector-similarity-ranked
        subset."""
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> bool:
        raise NotImplementedError