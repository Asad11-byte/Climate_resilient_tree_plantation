"""
Chunking: RawDocument -> list of DocumentChunk.

Uses semantic chunking: text is first split into sentence-level units, each
unit is embedded, and chunk boundaries are placed where consecutive
sentences' embeddings diverge the most (a breakpoint = a topic shift),
rather than at a fixed character count. A chunk that mixes two unrelated
topics dilutes its own embedding and becomes a worse match for queries
about either topic — that's the direct mechanism by which this should
improve retrieval precision/recall over fixed-size splitting.

Markdown/txt still get a first pass of header-aware splitting (mirrors the
breadcrumb-prefix approach from the earlier hackathon RAG project — each
chunk is prefixed with its section path, e.g. "Species > Shisham > Soil
Requirements"). Semantic merging then runs *within* each header section, so
breadcrumbs stay meaningful and a topic shift inside one long section can
still split into multiple chunks. PDFs run semantic merging per page, since
page numbers matter more than markdown headers for citation purposes there.

This requires an EmbeddingProvider at chunking time (one extra embedding
call per document, over sentence-sized units, in addition to the final
embedding call the ingestion pipeline already makes over the resulting
chunk texts) — chunk_document is now async because of that.
"""
import re
import statistics
from dataclasses import dataclass, field
from typing import List, Optional

from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

from app.services.embeddings.base import EmbeddingProvider
from app.services.ingestion.loaders import RawDocument

DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 150

# Semantic chunking tuning.
#
# SEMANTIC_BREAKPOINT_PERCENTILE is the standard "Kamradt-style" breakpoint
# technique: a gap between consecutive sentences counts as a topic shift
# once it's bigger than this percentile of all the gaps *in that section*,
# so the cutoff adapts to how varied the text actually is instead of using
# one fixed similarity threshold for every document.
#
# MIN_CHUNK_CHARS: a semantic chunk smaller than this gets merged into its
# neighbour — a lone one-sentence chunk is usually a worse retrieval unit
# (too little context to match a real question) than a slightly larger one.
#
# MAX_CHUNK_CHARS: hard cap even if no semantic breakpoint fires, so one
# highly self-similar section can't become a single giant chunk.
SEMANTIC_BREAKPOINT_PERCENTILE = 90
MIN_CHUNK_CHARS = 200
MAX_CHUNK_CHARS = DEFAULT_CHUNK_SIZE

_HEADERS_TO_SPLIT_ON = [
    ("#", "h1"),
    ("##", "h2"),
    ("###", "h3"),
]

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")


@dataclass
class DocumentChunk:
    document_id: str
    chunk_index: int
    text: str                 # includes the breadcrumb prefix
    breadcrumb: str = ""
    page: Optional[int] = None
    extra: dict = field(default_factory=dict)


def _split_into_sentences(text: str) -> List[str]:
    """Lightweight, dependency-free sentence splitter — good enough for the
    breakpoint-detection step below, since it only needs to be consistent,
    not linguistically perfect (embeddings are computed per unit either
    way). Paragraph breaks are treated as hard boundaries first, since
    tables/lists/captions rarely form real sentences and shouldn't be
    glued onto the next one."""
    units: List[str] = []
    for paragraph in text.split("\n\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        for sentence in _SENTENCE_SPLIT_RE.split(paragraph):
            sentence = sentence.strip()
            if sentence:
                units.append(sentence)
    return units


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _semantic_merge(units: List[str], embeddings: List[List[float]], max_chunk_chars: int) -> List[str]:
    """Merges sentence-level units into semantically coherent chunks,
    breaking wherever similarity to the next sentence drops enough to look
    like a topic shift, with a hard max_chunk_chars cap regardless."""
    if len(units) <= 1:
        return [u for u in units if u.strip()]

    distances = [1 - _cosine_similarity(embeddings[i], embeddings[i + 1]) for i in range(len(units) - 1)]

    if len(distances) < 2:
        threshold = float("inf")  # too few sentences to detect a meaningful breakpoint
    else:
        cut_points = statistics.quantiles(distances, n=100, method="inclusive")
        idx = min(max(SEMANTIC_BREAKPOINT_PERCENTILE, 1), 99) - 1
        threshold = cut_points[idx]

    chunks: List[str] = []
    current: List[str] = [units[0]]
    current_len = len(units[0])

    for i in range(len(units) - 1):
        next_unit = units[i + 1]
        is_topic_shift = distances[i] > threshold
        would_overflow = current_len + len(next_unit) + 1 > max_chunk_chars
        if is_topic_shift or would_overflow:
            chunks.append(" ".join(current))
            current = [next_unit]
            current_len = len(next_unit)
        else:
            current.append(next_unit)
            current_len += len(next_unit) + 1

    chunks.append(" ".join(current))

    # Merge any chunk smaller than MIN_CHUNK_CHARS into its neighbour so a
    # single short sentence never becomes an isolated, low-context chunk.
    merged: List[str] = []
    for chunk in chunks:
        if merged and len(chunk) < MIN_CHUNK_CHARS and len(merged[-1]) + len(chunk) <= max_chunk_chars * 1.5:
            merged[-1] = f"{merged[-1]} {chunk}"
        else:
            merged.append(chunk)
    return merged


def _safety_split_oversized(chunks: List[str], chunk_size: int, chunk_overlap: int) -> List[str]:
    """A single "sentence" with no internal punctuation (e.g. a giant
    run-on paragraph, OCR noise, a long list rendered as one line) can come
    out of _split_into_sentences as one atomic unit bigger than
    max_chunk_chars — the merge loop above can't split an atomic unit, so
    catch that here with the same recursive character splitter the old
    fixed-size approach used, as a fallback for this edge case only."""
    recursive = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap, separators=["\n\n", "\n", ". ", " ", ""],
    )
    result: List[str] = []
    for chunk in chunks:
        if len(chunk) > chunk_size * 1.5:
            result.extend(t for t in recursive.split_text(chunk) if t.strip())
        else:
            result.append(chunk)
    return result


async def _semantic_chunks_for_text(
    text: str, embedding_provider: EmbeddingProvider, chunk_size: int, chunk_overlap: int
) -> List[str]:
    units = _split_into_sentences(text)
    if not units:
        return []
    if len(units) == 1:
        return _safety_split_oversized(units, chunk_size, chunk_overlap)

    embeddings = await embedding_provider.embed_documents(units)
    merged = _semantic_merge(units, embeddings, max_chunk_chars=chunk_size)
    return _safety_split_oversized(merged, chunk_size, chunk_overlap)


async def chunk_markdown_or_text(
    raw: RawDocument,
    embedding_provider: EmbeddingProvider,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> List[DocumentChunk]:
    header_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=_HEADERS_TO_SPLIT_ON)
    sections = header_splitter.split_text(raw.text)

    chunks: List[DocumentChunk] = []
    index = 0
    for section in sections:
        breadcrumb = " > ".join(
            v for k in ("h1", "h2", "h3") if (v := section.metadata.get(k))
        )
        if not section.page_content.strip():
            continue

        semantic_texts = await _semantic_chunks_for_text(
            section.page_content, embedding_provider, chunk_size, chunk_overlap
        )
        for sub in semantic_texts:
            if not sub.strip():
                continue
            body = f"{breadcrumb}\n{sub.strip()}" if breadcrumb else sub.strip()
            chunks.append(
                DocumentChunk(
                    document_id=raw.document_id,
                    chunk_index=index,
                    text=body,
                    breadcrumb=breadcrumb,
                )
            )
            index += 1
    return chunks


async def chunk_pdf_pages(
    raw: RawDocument,
    embedding_provider: EmbeddingProvider,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> List[DocumentChunk]:
    if not raw.pages:
        return await chunk_markdown_or_text(raw, embedding_provider, chunk_size, chunk_overlap)

    chunks: List[DocumentChunk] = []
    index = 0
    for page_num, page_text in enumerate(raw.pages, start=1):
        if not page_text.strip():
            continue
        semantic_texts = await _semantic_chunks_for_text(
            page_text, embedding_provider, chunk_size, chunk_overlap
        )
        for sub in semantic_texts:
            if not sub.strip():
                continue
            chunks.append(
                DocumentChunk(
                    document_id=raw.document_id,
                    chunk_index=index,
                    text=sub.strip(),
                    page=page_num,
                )
            )
            index += 1
    return chunks


async def chunk_document(
    raw: RawDocument,
    embedding_provider: EmbeddingProvider,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> List[DocumentChunk]:
    if raw.file_type == "pdf":
        return await chunk_pdf_pages(raw, embedding_provider, chunk_size, chunk_overlap)
    return await chunk_markdown_or_text(raw, embedding_provider, chunk_size, chunk_overlap)