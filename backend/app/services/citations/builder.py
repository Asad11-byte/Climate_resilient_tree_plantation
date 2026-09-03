"""
Builds citation objects from retrieved-chunk payload metadata only.
Never touches LLM output — sources must be traceable to what was actually
retrieved, per master prompt section 17 ("Do NOT let Gemini/Groq generate
fake URLs").
"""
from dataclasses import dataclass
from typing import List, Optional

from app.services.retrieval.service import RetrievedChunk


@dataclass
class Source:
    document_id: str
    title: str
    source: str
    source_url: Optional[str]
    document_type: str
    year: Optional[int]
    location: str
    page: Optional[int]


def build_sources(chunks: List[RetrievedChunk]) -> List[Source]:
    seen = set()
    sources: List[Source] = []
    for chunk in chunks:
        p = chunk.payload
        document_id = p.get("document_id", "")
        page = p.get("page")
        dedup_key = (document_id, page)
        if dedup_key in seen:
            continue
        seen.add(dedup_key)
        sources.append(
            Source(
                document_id=document_id,
                title=p.get("title") or "Untitled",
                source=p.get("source") or "Not available in current evidence",
                source_url=p.get("source_url"),
                document_type=p.get("document_type") or "Not available in current evidence",
                year=p.get("year"),
                location=p.get("location") or "Not available in current evidence",
                page=page,
            )
        )
    return sources
