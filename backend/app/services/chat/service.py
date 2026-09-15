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
from app.repositories.species_repository import SpeciesRepository
from app.services.citations.builder import Source, build_sources
from app.services.context.assembler import format_environmental_context, format_evidence
from app.services.environment.service import EnvironmentDataService
from app.services.llm.base import LLMProvider
from app.services.llm.prompts import GROUNDED_SYSTEM_PROMPT, build_user_prompt
from app.services.query.classifier import classify_query, is_greeting
from app.services.retrieval.service import RetrievalService
from app.services.species_linking.matcher import SpeciesMention, find_mentioned_species

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
    mentioned_species: List[SpeciesMention] = field(default_factory=list)


class ChatService:
    def __init__(
        self,
        retrieval_service: RetrievalService,
        llm_provider: LLMProvider,
        environment_service: Optional[EnvironmentDataService] = None,
        species_repository: Optional[SpeciesRepository] = None,
    ):
        self._retrieval = retrieval_service
        self._llm = llm_provider
        self._environment = environment_service
        self._species_repository = species_repository

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

    async def _find_mentioned_species(self, answer_text: str) -> List[SpeciesMention]:
        """Best-effort, never blocking — a species table fetch failing
        shouldn't take down the chat answer, same degrade-to-empty pattern
        as _build_environmental_context above.

        KNOWN COST: this fetches the *entire* species table on every call
        (via list_all()), once per evidence-backed chat request. Fine at
        the current table size; if the species table grows large or chat
        volume gets high enough for this to matter, the fix belongs at the
        dependency-wiring / repository layer (e.g. a short-TTL cache
        wrapping get_species_repository()'s list_all()), not here — this
        method should stay a dumb "ask the repository, degrade on
        failure" call, not grow its own caching logic."""
        if self._species_repository is None:
            return []
        try:
            all_species = await self._species_repository.list_all()
        except ProviderUnavailableError:
            logger.warning("Species repository unavailable, mentioned_species degrading to []")
            return []
        return find_mentioned_species(answer_text, all_species)

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
            #
            # Species matching is deliberately skipped here too — a greeting
            # response is an introduction, not a species discussion, so
            # running find_mentioned_species (and paying for the underlying
            # species-table fetch) on every single "hi" would be wasted
            # work for something that will essentially never match.
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
            # mentioned_species stays [] (dataclass default) — NO_EVIDENCE_MESSAGE
            # is a fixed template string, never worth running the matcher
            # against it.
            return ChatResult(
                query_category=category, evidence_available=False, answer=NO_EVIDENCE_MESSAGE
            )

        evidence_text = format_evidence(chunks)
        environmental_text = await self._build_environmental_context(latitude, longitude)
        user_prompt = build_user_prompt(query, environmental_text, evidence_text)

        response = await self._llm.generate(GROUNDED_SYSTEM_PROMPT, user_prompt)
        sources = build_sources(chunks)
        mentioned_species = await self._find_mentioned_species(response.text)

        return ChatResult(
            query_category=category,
            evidence_available=True,
            answer=response.text,
            sources=sources,
            model=response.model,
            mentioned_species=mentioned_species,
        )