"""
Assembles the two context blocks the Groq system prompt expects: retrieved
evidence and environmental/location context. Kept separate from the chat
orchestrator so prompt-formatting can change without touching retrieval or
LLM-calling code.

Environmental data lookups (SoilGrids/NASA POWER/etc.) are Phase 5 work —
until then this module is explicit that no environmental data is available,
rather than letting the LLM assume or fabricate soil/climate conditions.
"""
from typing import List, Optional

from app.services.retrieval.service import RetrievedChunk


def format_evidence(chunks: List[RetrievedChunk]) -> str:
    if not chunks:
        return "No evidence retrieved."

    lines = []
    for i, chunk in enumerate(chunks, start=1):
        title = chunk.payload.get("title") or "Untitled source"
        source = chunk.payload.get("source") or "Not available in current evidence"
        year = chunk.payload.get("year")
        page = chunk.payload.get("page")
        breadcrumb = chunk.payload.get("breadcrumb")

        header_bits = [f"[{i}] {title}", f"Source: {source}"]
        if year:
            header_bits.append(f"Year: {year}")
        if page:
            header_bits.append(f"Page: {page}")
        if breadcrumb:
            header_bits.append(f"Section: {breadcrumb}")

        lines.append(" | ".join(header_bits))
        lines.append(chunk.text)
        lines.append("")  # blank line between chunks

    return "\n".join(lines).strip()


def format_environmental_context(
    latitude: Optional[float] = None, longitude: Optional[float] = None
) -> str:
    if latitude is None or longitude is None:
        return "No location was provided. Give general, non-location-specific guidance only."

    # Phase 5 will replace this with real SoilGrids/NASA POWER/etc. lookups.
    return (
        f"Location: latitude={latitude}, longitude={longitude} (Mandi Bahauddin area)\n"
        "Structured environmental data (soil, climate, vegetation) is not yet "
        "integrated for this location. Do not state or assume specific soil, "
        "climate, or vegetation values for these coordinates — note this as an "
        "uncertainty instead."
    )
