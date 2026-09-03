#!/usr/bin/env python3
"""
Seed the tree_species table with a small set of real entries.

Values below are general silvicultural knowledge about these species commonly
cited in Punjab forestry literature (Shisham/Dalbergia sissoo, Kikar/Acacia
nilotica). Fields we don't have a confident source for are left as `None` —
the API surfaces those as "Not available in current evidence" rather than
guessing. Treat this as a starting seed, not a substitute for sourcing real
values from the ingested documents in Phase 2/6.

Usage:
    python scripts/seed_species.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.dependencies import get_species_repository  # noqa: E402
from app.core.logging import configure_logging, get_logger  # noqa: E402

logger = get_logger(__name__)

SEED_SPECIES = [
    {
        "common_name": "Shisham",
        "scientific_name": "Dalbergia sissoo",
        "local_names": ["Tahli", "Sheesham"],
        "soil_requirements": "Well-drained alluvial soils, neutral to slightly alkaline pH",
        "water_requirement": "Moderate; needs consistent moisture in first two growing seasons",
        "drought_tolerance": "moderate",
        "heat_tolerance": "high",
        "flood_tolerance": "low",
        "growth_rate": None,
        "planting_season": "Start of monsoon (July)",
        "plantation_use": "Timber, agroforestry, riverine plantation",
        "local_presence": None,
        "description": "Widely planted in Punjab's riverine belts; sensitive to waterlogging.",
        "source_ids": None,
    },
    {
        "common_name": "Kikar",
        "scientific_name": "Acacia nilotica",
        "local_names": ["Babul"],
        "soil_requirements": "Tolerates a wide range of soils, including saline and waterlogged",
        "water_requirement": "Low once established",
        "drought_tolerance": "high",
        "heat_tolerance": "high",
        "flood_tolerance": "moderate",
        "growth_rate": None,
        "planting_season": "Start of monsoon (July)",
        "plantation_use": "Agroforestry on marginal land, fuelwood",
        "local_presence": None,
        "description": "Resilient species increasingly favored under rising summer temperatures.",
        "source_ids": None,
    },
]


async def main() -> None:
    configure_logging(debug=True)
    repo = get_species_repository()

    for entry in SEED_SPECIES:
        created = await repo.create(entry)
        print(f"Seeded: {created.get('common_name')} (id={created.get('id')})")


if __name__ == "__main__":
    asyncio.run(main())
