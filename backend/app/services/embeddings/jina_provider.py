"""
Jina AI embeddings implementation of EmbeddingProvider.
Full batching/retry logic belongs here — Phase 2 will flesh out batching,
but the public interface below is stable now so retrieval can be built
against it without waiting.
"""
from typing import List

import httpx

from app.core.config import Settings
from app.core.exceptions import ProviderUnavailableError
from app.core.logging import get_logger
from app.services.embeddings.base import EmbeddingProvider

logger = get_logger(__name__)


class JinaEmbeddingProvider(EmbeddingProvider):
    def __init__(self, settings: Settings):
        self._settings = settings
        self._url = settings.jina_embeddings_url
        self._api_key = settings.jina_api_key
        self._model = settings.jina_embedding_model

    async def _embed(self, texts: List[str], task: str) -> List[List[float]]:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": self._model, "input": texts, "task": task}
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(self._url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError as exc:
            raise ProviderUnavailableError(f"Jina embeddings failed: {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            raise ProviderUnavailableError("Could not reach Jina embeddings API") from exc

        try:
            return [item["embedding"] for item in data["data"]]
        except (KeyError, IndexError) as exc:
            raise ProviderUnavailableError("Unexpected Jina embeddings response shape") from exc

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return await self._embed(texts, task="retrieval.passage")

    async def embed_query(self, text: str) -> List[float]:
        result = await self._embed([text], task="retrieval.query")
        return result[0]

    async def health_check(self) -> bool:
        return bool(self._api_key)
