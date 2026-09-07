import pytest

from app.services.chat.service import NO_EVIDENCE_MESSAGE, ChatService
from app.services.retrieval.service import RetrievalService
from app.services.vectorstore.base import VectorRecord
from tests.fakes import FakeEmbeddingProvider, FakeLLMProvider, FakeReranker, FakeVectorStore


def _make_retrieval_service(store):
    return RetrievalService(FakeEmbeddingProvider(), store, FakeReranker(), top_k_candidates=10, top_k_final=3)


@pytest.mark.asyncio
async def test_chat_returns_grounded_answer_when_evidence_exists():
    store = FakeVectorStore()
    await store.upsert(
        [
            VectorRecord(
                id="1",
                vector=[10.0, 5.0, 0, 0, 0, 0, 0, 0],
                payload={
                    "text": "Shisham tolerates drought once established.",
                    "document_id": "d1",
                    "title": "Species Guide",
                    "source": "Punjab Forest Department",
                    "year": 2022,
                },
            )
        ]
    )
    llm = FakeLLMProvider(canned_text="Recommendation: Shisham.\nWhy: drought tolerant per evidence.")
    service = ChatService(_make_retrieval_service(store), llm)

    result = await service.chat("Which trees tolerate drought?")

    assert result.evidence_available is True
    assert "Shisham" in result.answer
    assert len(result.sources) == 1
    assert result.model == "fake-model"
    # the LLM must have actually received the retrieved evidence, not an empty context
    assert "Shisham tolerates drought" in llm.last_user_prompt


@pytest.mark.asyncio
async def test_chat_skips_llm_call_when_no_evidence():
    """Groq must never be called when retrieval finds nothing — the answer
    should be the honest fallback message, not a model guess."""
    store = FakeVectorStore()  # empty
    llm = FakeLLMProvider(canned_text="this should never be returned")
    service = ChatService(_make_retrieval_service(store), llm)

    result = await service.chat("Some totally unindexed question")

    assert result.evidence_available is False
    assert result.answer == NO_EVIDENCE_MESSAGE
    assert result.sources == []
    assert llm.last_user_prompt is None  # LLM was never invoked


@pytest.mark.asyncio
async def test_chat_includes_location_context_when_coordinates_given():
    store = FakeVectorStore()
    await store.upsert(
        [VectorRecord(id="1", vector=[1, 0, 0, 0, 0, 0, 0, 0],
                       payload={"text": "some evidence", "document_id": "d1"})]
    )
    llm = FakeLLMProvider()
    service = ChatService(_make_retrieval_service(store), llm)

    await service.chat("query", latitude=32.5, longitude=73.5)

    assert "32.5" in llm.last_user_prompt
    assert "73.5" in llm.last_user_prompt


@pytest.mark.asyncio
async def test_chat_greeting_skips_retrieval_but_still_calls_llm():
    """A greeting should never trigger retrieval (nothing to retrieve for
    'hi') and should never get the generic no-evidence message — it should
    reach Groq so the system prompt's greeting-handling instructions apply."""
    store = FakeVectorStore()  # deliberately empty — retrieval would fail if called
    llm = FakeLLMProvider(canned_text="I'm the tree plantation assistant for Mandi Bahauddin.")
    service = ChatService(_make_retrieval_service(store), llm)

    result = await service.chat("hi")

    assert result.evidence_available is True
    assert "tree plantation" in result.answer
    assert result.sources == []
    assert llm.last_user_prompt is not None  # Groq WAS called, unlike the no-evidence path


@pytest.mark.asyncio
async def test_chat_non_greeting_short_query_still_uses_retrieval():
    """Sanity check that the greeting fast-path doesn't accidentally swallow
    real short questions."""
    store = FakeVectorStore()  # empty -> should raise InsufficientEvidenceError
    llm = FakeLLMProvider()
    service = ChatService(_make_retrieval_service(store), llm)

    result = await service.chat("soil pH?")

    assert result.evidence_available is False
    assert llm.last_user_prompt is None


@pytest.mark.asyncio
async def test_chat_passes_real_environmental_data_into_prompt_when_available():
    """This is the fix: when an EnvironmentDataService is wired in, the LLM
    must see actual soil/climate values for the coordinates, not just the
    raw lat/lon with a 'not integrated' disclaimer."""
    from app.repositories.environmental_repository import EnvironmentalRepository
    from app.services.environment.service import EnvironmentDataService
    from tests.fakes import FakeSupabaseClient

    store = FakeVectorStore()
    await store.upsert(
        [VectorRecord(id="1", vector=[1, 0, 0, 0, 0, 0, 0, 0],
                       payload={"text": "some evidence", "document_id": "d1"})]
    )
    client = FakeSupabaseClient()
    client.seed("environmental_data", [
        {"id": "1", "latitude": 32.585, "longitude": 73.492, "soil_ph": 6.8,
         "clay": 22.0, "data_source": "SoilGrids", "retrieved_at": "2026-01-01T00:00:00Z"},
    ])
    env_repo = EnvironmentalRepository(client)
    env_service = EnvironmentDataService(env_repo, providers=[])

    llm = FakeLLMProvider()
    service = ChatService(_make_retrieval_service(store), llm, environment_service=env_service)

    await service.chat("query", latitude=32.585, longitude=73.492)

    assert "6.8" in llm.last_user_prompt
    assert "SoilGrids" in llm.last_user_prompt


@pytest.mark.asyncio
async def test_chat_degrades_gracefully_when_environment_lookup_fails():
    from app.core.exceptions import ProviderUnavailableError
    from app.services.environment.base import EnvironmentDataProvider

    class BrokenEnvironmentService:
        async def get_environment(self, latitude, longitude):
            raise ProviderUnavailableError("boom")

    store = FakeVectorStore()
    await store.upsert(
        [VectorRecord(id="1", vector=[1, 0, 0, 0, 0, 0, 0, 0],
                       payload={"text": "some evidence", "document_id": "d1"})]
    )
    llm = FakeLLMProvider()
    service = ChatService(
        _make_retrieval_service(store), llm, environment_service=BrokenEnvironmentService()
    )

    # Should not raise — degrades to the "unavailable" framing instead.
    result = await service.chat("query", latitude=32.585, longitude=73.492)
    assert result.evidence_available is True
    assert "unavailable" in llm.last_user_prompt.lower() or "not" in llm.last_user_prompt.lower()