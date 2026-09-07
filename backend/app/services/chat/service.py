"""
Chat orchestration: this is the "Query -> Retrieval -> Reranking -> Groq"
pipeline from master prompt section 2/16, wired together as a single
callable service so app/api/chat.py stays a thin router.

Rule enforced here: if retrieval finds no evidence, Groq is never called.
The answer is an honest "evidence unavailable" message built locally —
never a model guess dressed up as a grounded answer.
"""
from dataclasses import dataclass, field
from typing import List, Optional

from app.core.exceptions import InsufficientEvidenceError, ProviderUnavailableError
from app.core.logging import get_logger
from app.services.citations.builder import Source, build_sources
from app.services.context.assembler import format_environmental_context, format_evidence
from app.services.environment.service import EnvironmentDataService
from app.services.llm.base import LLMProvider
from app.services.llm.prompts import GROUNDED_SYSTEM_PROMPT, build_user_prompt
from app.services.query.classifier import classify_query, is_greeting
from app.services.retrieval.service import RetrievalService

logger = get_logger(__name__)

NO_EVIDENCE_MESSAGE = (
    "I couldn't find sufficient evidence in the knowledge base to answer this "
    "question. Evidence unavailable — try rephrasing, or this topic may not "
    "yet be covered by the indexed documents."
)


@dataclass
class ChatResult:
    query_category: str
    evidence_available: bool
    answer: str
    sources: List[Source] = field(default_factory=list)
    model: Optional[str] = None


class ChatService:
    def __init__(
        self,
        retrieval_service: RetrievalService,
        llm_provider: LLMProvider,
        environment_service: Optional[EnvironmentDataService] = None,
    ):
        self._retrieval = retrieval_service
        self._llm = llm_provider
        self._environment = environment_service

    async def _build_environmental_context(
        self, latitude: Optional[float], longitude: Optional[float]
    ) -> str:
        if latitude is None or longitude is None or self._environment is None:
            return format_environmental_context(latitude, longitude)

        try:
            result = await self._environment.get_environment(latitude, longitude)
        except ProviderUnavailableError:
            # A broken environment provider shouldn't take down the whole
            # chat request — fall back to the "not available" framing, same
            # as a genuine cache+live miss.
            logger.warning("Environment lookup failed for chat request, degrading gracefully")
            return format_environmental_context(latitude, longitude, environmental_available=False)

        return format_environmental_context(
            latitude, longitude,
            environmental_record=result.record,
            environmental_available=result.available,
        )

    async def chat(
        self,
        query: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        top_k: Optional[int] = None,
    ) -> ChatResult:
        category = classify_query(query)

        if is_greeting(query):
            # Skip retrieval entirely for greetings/small talk — there's no
            # evidence question to answer, and running retrieval would just
            # hit InsufficientEvidenceError and return the generic
            # "no evidence" message instead of a proper introduction. The
            # system prompt's "Greetings and small talk" section handles the
            # actual response; we still call Groq so the wording is natural
            # and consistent, just with no retrieved evidence in context.
            environmental_text = await self._build_environmental_context(latitude, longitude)
            user_prompt = build_user_prompt(query, environmental_text, "No evidence retrieved.")
            response = await self._llm.generate(GROUNDED_SYSTEM_PROMPT, user_prompt)
            return ChatResult(
                query_category=category,
                evidence_available=True,
                answer=response.text,
                sources=[],
                model=response.model,
            )

        try:
            chunks = await self._retrieval.retrieve(query, top_k=top_k)
        except InsufficientEvidenceError:
            logger.info("No evidence found for query, skipping Groq call: %r", query)
            return ChatResult(
                query_category=category, evidence_available=False, answer=NO_EVIDENCE_MESSAGE
            )

        evidence_text = format_evidence(chunks)
        environmental_text = await self._build_environmental_context(latitude, longitude)
        user_prompt = build_user_prompt(query, environmental_text, evidence_text)

        response = await self._llm.generate(GROUNDED_SYSTEM_PROMPT, user_prompt)
        sources = build_sources(chunks)

        return ChatResult(
            query_category=category,
            evidence_available=True,
            answer=response.text,
            sources=sources,
            model=response.model,
        )