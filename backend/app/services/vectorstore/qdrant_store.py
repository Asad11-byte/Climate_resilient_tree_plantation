from typing import Any, Dict, List, Optional

from qdrant_client import AsyncQdrantClient, models

from app.core.config import Settings
from app.core.exceptions import ProviderUnavailableError
from app.core.logging import get_logger
from app.services.vectorstore.base import VectorRecord, VectorSearchResult, VectorStore

logger = get_logger(__name__)


class QdrantVectorStore(VectorStore):
    def __init__(self, settings: Settings):
        self._settings = settings
        self._collection = settings.qdrant_collection
        self._client = AsyncQdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key or None,
            timeout=settings.qdrant_timeout_seconds,
        )

    async def ensure_collection(self) -> None:
        try:
            exists = await self._client.collection_exists(self._collection)
            if not exists:
                await self._client.create_collection(
                    collection_name=self._collection,
                    vectors_config=models.VectorParams(
                        size=self._settings.qdrant_vector_size,
                        distance=models.Distance.COSINE,
                    ),
                )
                logger.info("Created Qdrant collection '%s'", self._collection)
        except Exception as exc:  # noqa: BLE001 - translate any client error uniformly
            raise ProviderUnavailableError("Could not reach or configure Qdrant") from exc

    async def upsert(self, records: List[VectorRecord]) -> None:
        try:
            await self._client.upsert(
                collection_name=self._collection,
                points=[
                    models.PointStruct(id=r.id, vector=r.vector, payload=r.payload)
                    for r in records
                ],
            )
        except Exception as exc:  # noqa: BLE001
            raise ProviderUnavailableError("Qdrant upsert failed") from exc

    async def search(
        self,
        query_vector: List[float],
        top_k: int,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[VectorSearchResult]:
        qfilter = None
        if metadata_filter:
            qfilter = models.Filter(
                must=[
                    models.FieldCondition(key=k, match=models.MatchValue(value=v))
                    for k, v in metadata_filter.items()
                ]
            )
        try:
            results = await self._client.query_points(
                collection_name=self._collection,
                query=query_vector,
                limit=top_k,
                query_filter=qfilter,
                with_payload=True,
            )
        except Exception as exc:  # noqa: BLE001
            raise ProviderUnavailableError("Qdrant search failed") from exc

        return [
            VectorSearchResult(id=str(p.id), score=p.score, payload=p.payload or {})
            for p in results.points
        ]

    async def delete(self, ids: List[str]) -> None:
        try:
            await self._client.delete(
                collection_name=self._collection,
                points_selector=models.PointIdsList(points=ids),
            )
        except Exception as exc:  # noqa: BLE001
            raise ProviderUnavailableError("Qdrant delete failed") from exc

    async def health_check(self) -> bool:
        try:
            await self._client.get_collections()
            return True
        except Exception:  # noqa: BLE001
            return False
