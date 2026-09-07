"""
Query classification: cheap keyword matching, not a trained model.

Master prompt section 11 is explicit: "Use classification only when useful;
don't over-engineer it." This is used as an optional signal (e.g. to bias
metadata filtering or to log query patterns), never as a hard gate that can
wrongly exclude relevant evidence.
"""
from typing import List

CATEGORIES = [
    "tree_species", "soil", "climate", "water",
    "plantation", "climate_change", "location", "general",
]

_GREETINGS = {
    "hi", "hi!", "hii", "hiii", "hello", "hello!", "hey", "hey!", "hiya",
    "salam", "assalam o alaikum", "assalamualaikum", "asalam o alaikum",
    "good morning", "good afternoon", "good evening",
    "who are you", "what are you", "what is this", "what can you do",
    "help", "start", "test",
}


def is_greeting(query: str) -> bool:
    """Cheap, conservative check for greetings/small talk — deliberately a
    fixed phrase list (not a length/heuristic guess) so a short real question
    like 'soil pH?' is never misrouted away from retrieval."""
    normalized = query.strip().lower().rstrip("!.?")
    return normalized in _GREETINGS

_KEYWORDS = {
    "tree_species": ["species", "tree", "shisham", "kikar", "sheesham", "which trees"],
    "soil": ["soil", "ph", "clay", "sand", "loam", "organic carbon"],
    "climate": ["temperature", "rainfall", "climate", "weather", "humidity"],
    "water": ["water", "irrigation", "drought", "flood", "waterlogging"],
    "plantation": ["plant", "plantation", "nursery", "sapling", "spacing", "planting season"],
    "climate_change": ["climate change", "warming", "adaptation", "resilien"],
    "location": ["mandi bahauddin", "location", "coordinates", "near", "district"],
}


def classify_query(query: str) -> str:
    lowered = query.lower()
    scores = {cat: 0 for cat in CATEGORIES}
    for category, keywords in _KEYWORDS.items():
        for kw in keywords:
            if kw in lowered:
                scores[category] += 1
    best_category, best_score = max(scores.items(), key=lambda kv: kv[1])
    return best_category if best_score > 0 else "general"