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
