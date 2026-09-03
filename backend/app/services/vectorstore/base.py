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
    async def health_check(self) -> bool:
        raise NotImplementedError
