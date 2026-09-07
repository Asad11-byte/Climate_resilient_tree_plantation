"""
Assembles the two context blocks the Groq system prompt expects: retrieved
evidence and environmental/location context. Kept separate from the chat
orchestrator so prompt-formatting can change without touching retrieval or
LLM-calling code.
"""
from typing import Any, Dict, List, Optional

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


# payload field -> (label, unit) — units per SoilGrids/NASA POWER conventions
# used by app/services/environment/*_provider.py.
_ENV_FIELDS = [
    ("soil_ph", "Soil pH", ""),
    ("clay", "Clay content", "%"),
    ("sand", "Sand content", "%"),
    ("organic_carbon", "Organic carbon", "g/kg"),
    ("temperature", "Mean temperature", "°C"),
    ("rainfall", "Rainfall", "mm"),
    ("ndvi", "NDVI (vegetation index)", ""),
    ("ndwi", "NDWI (water index)", ""),
    ("land_cover", "Land cover", ""),
]


def format_environmental_context(
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    environmental_record: Optional[Dict[str, Any]] = None,
    environmental_available: Optional[bool] = None,
) -> str:
    """
    `environmental_record` should be the dict returned by
    EnvironmentDataService.get_environment() (cached or freshly fetched from
    SoilGrids/NASA POWER/etc.) — the caller (ChatService) is responsible for
    fetching it; this function only formats what it's given, so it stays
    testable without a live provider.
    """
    if latitude is None or longitude is None:
        return "No location was provided. Give general, non-location-specific guidance only."

    header = f"Location: latitude={latitude}, longitude={longitude} (Mandi Bahauddin area)"

    if not environmental_record:
        reason = (
            "Data unavailable for this location."
            if environmental_available is False
            else "Structured environmental data is not yet integrated for this location."
        )
        return (
            f"{header}\n{reason} Do not state or assume specific soil, climate, "
            "or vegetation values for these coordinates — note this as an "
            "uncertainty instead."
        )

    data_source = environmental_record.get("data_source") or "an external dataset"
    lines = [header, f"Environmental data (estimated from {data_source}):"]

    any_value = False
    for field, label, unit in _ENV_FIELDS:
        value = environmental_record.get(field)
        if value is None:
            lines.append(f"- {label}: not available from these sources")
        else:
            any_value = True
            lines.append(f"- {label}: {value}{unit}")

    if not any_value:
        # Defensive: a record technically exists but every field is null.
        return (
            f"{header}\nNo usable environmental values were returned for this "
            "location. Do not assume specific soil, climate, or vegetation "
            "conditions — note this as an uncertainty instead."
        )

    lines.append(
        "These are modelled/estimated values from the sources above, not "
        "field measurements — phrase them accordingly and do not treat any "
        "'not available' field as zero or as evidence of absence."
    )
    return "\n".join(lines)