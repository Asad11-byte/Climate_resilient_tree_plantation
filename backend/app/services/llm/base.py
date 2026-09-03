"""
LLM provider interface.

Every caller (context assembly, chat route, evaluation harness) depends on
this ABC, never on a concrete provider. To swap Groq for something else,
implement this interface once and change the single wiring point in
core/dependencies.py — nothing else changes.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LLMResponse:
    text: str
    model: str
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    latency_seconds: Optional[float] = None
    raw: dict = field(default_factory=dict)


class LLMProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
    ) -> LLMResponse:
        """Generate a grounded completion. Implementations must raise
        app.core.exceptions.ProviderUnavailableError on failure — never
        swallow errors and return a fabricated string."""
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> bool:
        """Cheap connectivity check used by /health. Should not raise."""
        raise NotImplementedError
