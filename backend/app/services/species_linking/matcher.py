"""
Server-side species mention matching: given Groq's final answer text and the
full species table, find which species are actually named in it.

Deliberately NOT an LLM call and NOT client-side fuzzy matching — same
principle as citations being built only from retrieved payload metadata,
never invented or inferred: a species link should only ever point somewhere
real, and the frontend should never have to guess which words are species
names via string heuristics of its own.

LIMITATION (real, not hidden): a species being mentioned in the answer text
is not the same as being recommended. A species could appear in an "avoid
this" or "unlike X, Y is better" context and still surface as a link here.
The link means "learn more about this species," not an endorsement — the
actual recommendation/reasoning lives in the answer text itself
(Recommendation / Why / Uncertainty sections), which this matcher does not
and should not try to interpret.
"""
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SpeciesMention:
    id: str
    common_name: str
    scientific_name: Optional[str] = None


def _name_variants(species: Dict[str, Any]) -> List[str]:
    """Every name form worth matching against for one species row —
    common name, scientific name, and any local names. Empty/None entries
    are skipped rather than matched (an empty string would match
    everything)."""
    names: List[str] = []
    for key in ("common_name", "scientific_name"):
        value = species.get(key)
        if value:
            names.append(value)
    local_names = species.get("local_names")
    if local_names:
        names.extend(n for n in local_names if n)
    return names


def _build_pattern(name: str) -> "re.Pattern[str]":
    """Word-boundary, case-insensitive match for one name. Word boundaries
    matter here specifically to avoid short common names (e.g. a 3-4 letter
    local name) matching as a substring inside an unrelated longer word —
    a plain case-insensitive `in` check doesn't have that protection."""
    return re.compile(r"\b" + re.escape(name) + r"\b", re.IGNORECASE)


def find_mentioned_species(
    answer_text: str, all_species: Sequence[Dict[str, Any]]
) -> List[SpeciesMention]:
    """Returns one SpeciesMention per species row that has at least one
    name form appearing in answer_text, in the order those species were
    first mentioned in the text (not the order of all_species) — so the
    chip row roughly matches reading order. Each species appears at most
    once even if multiple of its name variants (e.g. both common and
    scientific name) are present."""
    matches: List[tuple[int, SpeciesMention]] = []

    for species in all_species:
        species_id = species.get("id")
        if not species_id:
            continue  # a malformed row shouldn't crash matching for everything else

        earliest_position: Optional[int] = None
        for name in _name_variants(species):
            match = _build_pattern(name).search(answer_text)
            if match and (earliest_position is None or match.start() < earliest_position):
                earliest_position = match.start()

        if earliest_position is not None:
            matches.append((
                earliest_position,
                SpeciesMention(
                    id=species_id,
                    common_name=species.get("common_name", "Unknown"),
                    scientific_name=species.get("scientific_name"),
                ),
            ))

    matches.sort(key=lambda pair: pair[0])
    return [mention for _, mention in matches]