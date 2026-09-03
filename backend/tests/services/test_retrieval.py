import pytest

from app.core.exceptions import InsufficientEvidenceError
from app.services.retrieval.service import RetrievalService
from app.services.vectorstore.base import VectorRecord
from tests.fakes import FakeEmbeddingProvider, FakeReranker, FakeVectorStore


@pytest.mark.asyncio
async def test_retrieve_returns_chunks_when_evidence_exists():
    store = FakeVectorStore()
    await store.upsert(
        [
            VectorRecord(
                id="1",
                vector=[10.0, 5.0, 0, 0, 0, 0, 0, 0],
                payload={"text": "Shisham grows well in loamy soil.", "document_id": "d1", "topic": "soil"},
            ),
            VectorRecord(
                id="2",
                vector=[10.0, 5.0, 0, 0, 0, 0, 0, 0],
                payload={"text": "Kikar is drought tolerant.", "document_id": "d2", "topic": "tree_species"},
            ),
        ]
    )
    service = RetrievalService(FakeEmbeddingProvider(), store, FakeReranker(), top_k_candidates=10, top_k_final=2)
    results = await service.retrieve("Which trees tolerate drought?")
    assert len(results) == 2
    assert all(r.rerank_score is not None for r in results)


@pytest.mark.asyncio
async def test_retrieve_raises_when_no_candidates():
    store = FakeVectorStore()  # empty
    service = RetrievalService(FakeEmbeddingProvider(), store, FakeReranker())
    with pytest.raises(InsufficientEvidenceError):
        await service.retrieve("Anything at all")


@pytest.mark.asyncio
async def test_retrieve_applies_metadata_filter():
    store = FakeVectorStore()
    await store.upsert(
        [
            VectorRecord(id="1", vector=[1, 0, 0, 0, 0, 0, 0, 0],
                         payload={"text": "soil chunk", "document_id": "d1", "topic": "soil"}),
            VectorRecord(id="2", vector=[1, 0, 0, 0, 0, 0, 0, 0],
                         payload={"text": "species chunk", "document_id": "d2", "topic": "tree_species"}),
        ]
    )
    service = RetrievalService(FakeEmbeddingProvider(), store, FakeReranker())
    results = await service.retrieve("query", metadata_filter={"topic": "soil"})
    assert len(results) == 1
    assert results[0].payload["topic"] == "soil"


@pytest.mark.asyncio
async def test_retrieve_raises_when_all_matches_below_relevance_threshold():
    """A weak/off-topic top match must not be passed through as if it were
    real evidence — this is what prevents a nonsense query from getting a
    confidently-worded but ungrounded Groq answer."""
    store = FakeVectorStore()
    await store.upsert(
        [VectorRecord(id="1", vector=[1, 0, 0, 0, 0, 0, 0, 0],
                       payload={"text": "barely related", "document_id": "d1"})]
    )
    # FakeReranker's best possible score for a single candidate is 1.0 —
    # setting the floor above that forces every match to be filtered out.
    service = RetrievalService(
        FakeEmbeddingProvider(), store, FakeReranker(), min_relevance_score=2.0
    )
    with pytest.raises(InsufficientEvidenceError):
        await service.retrieve("some query")


@pytest.mark.asyncio
async def test_retrieve_keeps_matches_at_or_above_threshold():
    store = FakeVectorStore()
    await store.upsert(
        [VectorRecord(id="1", vector=[1, 0, 0, 0, 0, 0, 0, 0],
                       payload={"text": "relevant text", "document_id": "d1"})]
    )
    service = RetrievalService(
        FakeEmbeddingProvider(), store, FakeReranker(), min_relevance_score=0.5
    )
    results = await service.retrieve("some query")
    assert len(results) == 1
