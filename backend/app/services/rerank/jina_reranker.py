from typing import List

import httpx

from app.core.config import Settings
from app.core.exceptions import ProviderUnavailableError
from app.services.rerank.base import RerankedResult, RerankerProvider


class JinaReranker(RerankerProvider):
    def __init__(self, settings: Settings):
        self._url = settings.jina_rerank_url
        self._api_key = settings.jina_api_key
        self._model = settings.jina_rerank_model

    async def rerank(self, query: str, documents: List[str], top_k: int) -> List[RerankedResult]:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model,
            "query": query,
            "documents": documents,
            "top_n": top_k,
        }
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(self._url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError as exc:
            raise ProviderUnavailableError(f"Jina rerank failed: {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            raise ProviderUnavailableError("Could not reach Jina rerank API") from exc

        try:
            return [
                RerankedResult(index=r["index"], score=r["relevance_score"])
                for r in data["results"]
            ]
        except (KeyError, IndexError) as exc:
            raise ProviderUnavailableError("Unexpected Jina rerank response shape") from exc

    async def health_check(self) -> bool:
        return bool(self._api_key)
