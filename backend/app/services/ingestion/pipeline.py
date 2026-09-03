"""
Ingestion pipeline: file on disk -> embedded chunks upserted into Qdrant.

Orchestrates services/ingestion/{loaders,chunking}, services/embeddings,
services/vectorstore. Contains no HTTP/client-specific code itself — that
all lives in the providers it's given.
"""
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger
from app.services.embeddings.base import EmbeddingProvider
from app.services.ingestion.chunking import chunk_document
from app.services.ingestion.loaders import load_file
from app.services.vectorstore.base import VectorRecord, VectorStore

logger = get_logger(__name__)

# Fixed namespace so chunk point-IDs are deterministic across runs.
_ID_NAMESPACE = uuid.UUID("f0c1a2b3-1111-4a2b-9c3d-abcdef123456")

# Metadata fields required by the master prompt's payload schema.
# Anything not supplied by the caller defaults to None / "Not available".
REQUIRED_METADATA_FIELDS = [
    "title", "source", "source_url", "location", "province", "country",
    "year", "document_type", "topic",
]

EMBEDDING_BATCH_SIZE = 32


@dataclass
class IngestResult:
    document_id: str
    source_path: str
    chunks_indexed: int
    skipped_empty_chunks: int = 0


@dataclass
class DirectoryIngestSummary:
    files_found: int
    results: List[IngestResult]
    failures: List[str]


def _deterministic_point_id(document_id: str, chunk_index: int) -> str:
    return str(uuid.uuid5(_ID_NAMESPACE, f"{document_id}:{chunk_index}"))


def _batched(items: List[Any], size: int):
    for i in range(0, len(items), size):
        yield items[i : i + size]


class IngestionPipeline:
    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
        chunk_size: int = 800,
        chunk_overlap: int = 150,
    ):
        self._embeddings = embedding_provider
        self._vector_store = vector_store
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    async def ingest_file(
        self, path: Path, metadata: Optional[Dict[str, Any]] = None
    ) -> IngestResult:
        metadata = metadata or {}
        raw = load_file(path)
        chunks = chunk_document(raw, self._chunk_size, self._chunk_overlap)

        texts = [c.text for c in chunks if c.text.strip()]
        skipped = len(chunks) - len(texts)
        if not texts:
            logger.warning("No non-empty chunks produced for %s", path)
            return IngestResult(raw.document_id, str(path), 0, skipped)

        await self._vector_store.ensure_collection()

        records: List[VectorRecord] = []
        for batch in _batched(chunks, EMBEDDING_BATCH_SIZE):
            batch = [c for c in batch if c.text.strip()]
            if not batch:
                continue
            vectors = await self._embeddings.embed_documents([c.text for c in batch])
            for chunk, vector in zip(batch, vectors):
                payload = {
                    "document_id": chunk.document_id,
                    "chunk_index": chunk.chunk_index,
                    "text": chunk.text,
                    "breadcrumb": chunk.breadcrumb,
                    "page": chunk.page,
                    "title": metadata.get("title", raw.title),
                    "source": metadata.get("source", "Not available in current evidence"),
                    "source_url": metadata.get("source_url"),
                    "location": metadata.get("location", "Mandi Bahauddin"),
                    "province": metadata.get("province", "Punjab"),
                    "country": metadata.get("country", "Pakistan"),
                    "year": metadata.get("year"),
                    "document_type": metadata.get("document_type", "Not available in current evidence"),
                    "topic": metadata.get("topic", "general"),
                }
                records.append(
                    VectorRecord(
                        id=_deterministic_point_id(chunk.document_id, chunk.chunk_index),
                        vector=vector,
                        payload=payload,
                    )
                )

        # Deterministic IDs mean upsert is naturally idempotent — re-running
        # ingestion on the same file overwrites the same points instead of
        # duplicating them.
        await self._vector_store.upsert(records)
        logger.info("Indexed %d chunks from %s", len(records), path)
        return IngestResult(raw.document_id, str(path), len(records), skipped)

    async def ingest_directory(
        self, directory: Path, default_metadata: Optional[Dict[str, Any]] = None
    ) -> "DirectoryIngestSummary":
        from app.services.ingestion.loaders import SUPPORTED_EXTENSIONS

        directory = Path(directory)
        results: List[IngestResult] = []
        failures: List[str] = []
        files = sorted(
            p for p in directory.rglob("*") if p.suffix.lower() in SUPPORTED_EXTENSIONS
        )
        for file_path in files:
            per_file_metadata = dict(default_metadata or {})
            sidecar = file_path.with_suffix(file_path.suffix + ".meta.json")
            if sidecar.exists():
                import json

                per_file_metadata.update(json.loads(sidecar.read_text()))
            try:
                result = await self.ingest_file(file_path, per_file_metadata)
                results.append(result)
            except Exception as exc:  # noqa: BLE001
                logger.exception("Failed to ingest %s", file_path)
                failures.append(f"{file_path}: {type(exc).__name__}: {exc}")
        return DirectoryIngestSummary(files_found=len(files), results=results, failures=failures)
