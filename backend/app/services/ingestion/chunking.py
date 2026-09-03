"""
Chunking: RawDocument -> list of DocumentChunk.

Uses header-aware splitting for markdown/txt/docx-derived text (mirrors the
breadcrumb-prefix approach from the earlier hackathon RAG project — each
chunk is prefixed with its section path, e.g. "Species > Shisham > Soil
Requirements", so a chunk retrieved out of context still carries where it
came from). PDFs are split per-page since page numbers matter more than
markdown headers for citation purposes there.

Deliberately NOT over-engineered: one splitter strategy per source type,
no ML-based semantic chunking.
"""
from dataclasses import dataclass, field
from typing import List, Optional

from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

from app.services.ingestion.loaders import RawDocument

DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 150

_HEADERS_TO_SPLIT_ON = [
    ("#", "h1"),
    ("##", "h2"),
    ("###", "h3"),
]


@dataclass
class DocumentChunk:
    document_id: str
    chunk_index: int
    text: str                 # includes the breadcrumb prefix
    breadcrumb: str = ""
    page: Optional[int] = None
    extra: dict = field(default_factory=dict)


def _recursive_splitter(chunk_size: int, chunk_overlap: int) -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )


def chunk_markdown_or_text(
    raw: RawDocument,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> List[DocumentChunk]:
    header_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=_HEADERS_TO_SPLIT_ON)
    sections = header_splitter.split_text(raw.text)

    # If there were no headers at all, MarkdownHeaderTextSplitter returns the
    # whole text as one section with empty metadata — that's fine, it just
    # falls through with no breadcrumb.
    recursive = _recursive_splitter(chunk_size, chunk_overlap)

    chunks: List[DocumentChunk] = []
    index = 0
    for section in sections:
        breadcrumb = " > ".join(
            v for k in ("h1", "h2", "h3") if (v := section.metadata.get(k))
        )
        sub_texts = recursive.split_text(section.page_content) or [section.page_content]
        for sub in sub_texts:
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


def chunk_pdf_pages(
    raw: RawDocument,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> List[DocumentChunk]:
    if not raw.pages:
        return chunk_markdown_or_text(raw, chunk_size, chunk_overlap)

    recursive = _recursive_splitter(chunk_size, chunk_overlap)
    chunks: List[DocumentChunk] = []
    index = 0
    for page_num, page_text in enumerate(raw.pages, start=1):
        if not page_text.strip():
            continue
        for sub in recursive.split_text(page_text):
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


def chunk_document(
    raw: RawDocument,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> List[DocumentChunk]:
    if raw.file_type == "pdf":
        return chunk_pdf_pages(raw, chunk_size, chunk_overlap)
    return chunk_markdown_or_text(raw, chunk_size, chunk_overlap)
