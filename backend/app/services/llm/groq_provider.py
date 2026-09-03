"""
Groq implementation of LLMProvider.

Groq exposes an OpenAI-compatible /chat/completions endpoint, so this is a
thin httpx client rather than a bespoke SDK integration. Kept isolated here
so nothing outside this file knows the request/response shape is OpenAI-style.
"""
import time
from typing import Optional

import httpx

from app.core.config import Settings
from app.core.exceptions import ProviderUnavailableError
from app.core.logging import get_logger
from app.services.llm.base import LLMProvider, LLMResponse

logger = get_logger(__name__)


class GroqProvider(LLMProvider):
    def __init__(self, settings: Settings):
        self._settings = settings
        self._base_url = settings.groq_base_url.rstrip("/")
        self._api_key = settings.groq_api_key
        self._default_model = settings.groq_model
        self._timeout = settings.groq_timeout_seconds

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
    ) -> LLMResponse:
        payload = {
            "model": model or self._default_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature if temperature is not None else self._settings.groq_temperature,
            "max_tokens": max_tokens or self._settings.groq_max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        started = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    f"{self._base_url}/chat/completions", json=payload, headers=headers
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError as exc:
            logger.error("Groq returned HTTP %s", exc.response.status_code)
            raise ProviderUnavailableError(f"Groq request failed with status {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            logger.error("Groq request error: %s", type(exc).__name__)
            raise ProviderUnavailableError("Could not reach Groq API") from exc

        latency = time.monotonic() - started
        try:
            choice = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise ProviderUnavailableError("Groq response missing expected content") from exc

        usage = data.get("usage", {})
        return LLMResponse(
            text=choice,
            model=data.get("model", payload["model"]),
            input_tokens=usage.get("prompt_tokens"),
            output_tokens=usage.get("completion_tokens"),
            latency_seconds=latency,
            raw={},  # deliberately not storing the full raw payload (may embed prompt/keys)
        )

    async def health_check(self) -> bool:
        if not self._api_key:
            return False
        headers = {"Authorization": f"Bearer {self._api_key}"}
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self._base_url}/models", headers=headers)
                return resp.status_code == 200
        except httpx.RequestError:
            return False
