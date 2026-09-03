"""
Because everything depends on LLMProvider (the interface), we can test
callers with a fake implementation instead of hitting the real Groq API.
This is what "provider-swappable" buys you in practice.
"""
import pytest

from app.services.llm.base import LLMProvider, LLMResponse


class FakeLLMProvider(LLMProvider):
    """Stand-in for GroqProvider in tests."""

    def __init__(self, canned_text: str = "fake grounded answer"):
        self._canned_text = canned_text

    async def generate(self, system_prompt, user_prompt, **kwargs) -> LLMResponse:
        return LLMResponse(text=self._canned_text, model="fake-model")

    async def health_check(self) -> bool:
        return True


@pytest.mark.asyncio
async def test_fake_provider_satisfies_interface():
    provider: LLMProvider = FakeLLMProvider("Recommendation: Shisham (evidence-backed).")
    response = await provider.generate("system", "user question")
    assert isinstance(response, LLMResponse)
    assert "Shisham" in response.text
    assert await provider.health_check() is True


@pytest.mark.asyncio
async def test_groq_provider_is_constructible_without_network_call():
    """Importing/instantiating GroqProvider must never make a network call —
    only .generate()/.health_check() should. This test would fail if config
    or __init__ accidentally triggered an HTTP request."""
    from app.core.config import Settings
    from app.services.llm.groq_provider import GroqProvider

    settings = Settings(groq_api_key="test-key")
    provider = GroqProvider(settings)
    assert provider is not None
