from pathlib import Path

import pytest

from app.services.ingestion.pipeline import IngestionPipeline
from tests.fakes import FakeEmbeddingProvider, FakeVectorStore


@pytest.fixture
def sample_md(tmp_path: Path) -> Path:
    content = (
        "# Plantation Guidance\n\n"
        "## Mandi Bahauddin\n\n"
        "Local evidence suggests Shisham and Kikar are the most commonly "
        "planted species in the district, based on Punjab Forest Department "
        "records from recent plantation drives.\n"
    )
    file_path = tmp_path / "guidance.md"
    file_path.write_text(content)
    return file_path


@pytest.mark.asyncio
async def test_ingest_file_indexes_chunks(sample_md: Path):
    pipeline = IngestionPipeline(FakeEmbeddingProvider(), FakeVectorStore())
    result = await pipeline.ingest_file(
        sample_md, metadata={"source": "Punjab Forest Department", "topic": "plantation", "year": 2022}
    )
    assert result.chunks_indexed > 0
    assert result.document_id


@pytest.mark.asyncio
async def test_reingesting_same_file_is_idempotent(sample_md: Path):
    """Re-running ingestion on the same file must not duplicate vectors —
    this is an explicit master-prompt requirement."""
    store = FakeVectorStore()
    pipeline = IngestionPipeline(FakeEmbeddingProvider(), store)

    await pipeline.ingest_file(sample_md, metadata={"source": "PFD"})
    count_after_first = len(store._points)

    await pipeline.ingest_file(sample_md, metadata={"source": "PFD"})
    count_after_second = len(store._points)

    assert count_after_first == count_after_second
    assert count_after_first > 0


@pytest.mark.asyncio
async def test_metadata_defaults_applied(sample_md: Path):
    store = FakeVectorStore()
    pipeline = IngestionPipeline(FakeEmbeddingProvider(), store)
    await pipeline.ingest_file(sample_md, metadata={"source": "Punjab Forest Department", "year": 2022})

    payloads = [r.payload for r in store._points.values()]
    assert all(p["location"] == "Mandi Bahauddin" for p in payloads)
    assert all(p["province"] == "Punjab" for p in payloads)
    assert all(p["source"] == "Punjab Forest Department" for p in payloads)
    assert all(p["year"] == 2022 for p in payloads)
