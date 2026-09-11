#!/usr/bin/env python3
"""
Seed the tree_species table with a small set of real entries.

Values below are drawn from the sourced tree_species_evidence_base.md
document (World Agroforestry Centre Agroforestree Database, CABI Compendium,
PFAF, and peer-reviewed studies — see that document for full citations per
species). Fields we don't have a confident source for are left as `None` —
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
        "soil_requirements": "Well-drained, porous soils such as sandy loams, pH 5.0-8.0; prefers riverbank/alluvial soils",
        "water_requirement": "500-4,500 mm annual rainfall without irrigation; needs consistent moisture during establishment",
        "drought_tolerance": "moderate-high",
        "heat_tolerance": "high",
        "flood_tolerance": "low",
        "growth_rate": None,
        "planting_season": "Start of monsoon (July)",
        "plantation_use": "Timber, fuelwood, fodder, shade, erosion control, riverine plantation",
        "local_presence": "Confirmed present in Phalia tehsil, Mandi Bahauddin, by direct field ethnobotanical survey (bark used for nose bleeds); also confirmed in agroforestry carbon-stock field sampling across all three tehsils (Mandi-Bahauddin, Phalia, Malakwal)",
        "description": (
            "Widely planted nitrogen-fixing species in Punjab's riverine belts. "
            "Significant risk from Shisham dieback disease (Fusarium solani / "
            "Botryodiplodia theobromae fungal complex), which causes progressive "
            "wilting and mortality, worsened by drought stress — a major "
            "caveat for large-scale plantation planning."
        ),
        "source_ids": [
            "tree_species_evidence_base.md#shisham",
            "Nisar et al. 2011, Middle-East J. Sci. Res. 9(2): 233-238",
            "Komal et al. 2022, Agriculture 12(2): 295",
        ],
    },
    {
        "common_name": "Kikar",
        "scientific_name": "Acacia nilotica",
        "local_names": ["Babul"],
        "soil_requirements": "Tolerates a wide range of soils including saline/alkaline, up to pH 9",
        "water_requirement": "Drought-tolerant once established; adequate moisture needed for full growth",
        "drought_tolerance": "high",
        "heat_tolerance": "high (withstands >50°C)",
        "flood_tolerance": "moderate (used in waterlogged/saline land reclamation)",
        "growth_rate": None,
        "planting_season": "Start of monsoon (July)",
        "plantation_use": "Agroforestry on marginal/degraded land, fuelwood, windbreaks, saline soil reclamation",
        "local_presence": "Confirmed present in Phalia tehsil, Mandi Bahauddin, by direct field ethnobotanical survey (pod used for gonorrhea remedy); also confirmed in agroforestry carbon-stock field sampling across all three tehsils, among the highest-distribution species recorded (up to 15% of tree basal area in Mandi-Bahauddin tehsil)",
        "description": (
            "Multipurpose nitrogen-fixing tree used extensively for reclaiming "
            "saline, alkaline, and waterlogged land in South Asian agroforestry. "
            "Field trials show no growth deterioration under saline irrigation, "
            "performing better than Shisham under the same conditions."
        ),
        "source_ids": [
            "tree_species_evidence_base.md#kikar",
            "Nisar et al. 2011, Middle-East J. Sci. Res. 9(2): 233-238",
            "Komal et al. 2022, Agriculture 12(2): 295",
        ],
    },
    {
        "common_name": "Neem",
        "scientific_name": "Azadirachta indica",
        "local_names": None,
        "soil_requirements": "Wide pH tolerance (4-10, optimal 6.2-7.0); prefers well-drained loamy to heavy clay soils",
        "water_requirement": "Highly drought tolerant; documented surviving on as little as 130mm/yr in some regions, optimal range 400-1,200 mm/yr",
        "drought_tolerance": "high",
        "heat_tolerance": "high (tolerates up to 50°C; unfavourable below ~4°C)",
        "flood_tolerance": "low",
        "growth_rate": "fast",
        "planting_season": None,
        "plantation_use": "Shade/avenue tree, windbreak, dune-fixation/erosion control, intercropping",
        "local_presence": None,
        "description": (
            "Fast-growing, drought-tolerant native to South Asia including "
            "Pakistan. Waterlogging is a clear limitation — sources explicitly "
            "note waterlogged soil retards growth and raises mortality risk, "
            "so it is a poor fit for low-lying or flood-prone plots despite "
            "excellent heat/drought tolerance elsewhere."
        ),
        "source_ids": ["tree_species_evidence_base.md#neem"],
    },
    {
        "common_name": "Arjun",
        "scientific_name": "Terminalia arjuna",
        "local_names": None,
        "soil_requirements": "Alluvial loams, sandy loams, and clay-loam floodplain soils; tolerant of seasonally waterlogged clay",
        "water_requirement": "Needs supplemental watering during establishment; natural regeneration poor in semi-arid conditions",
        "drought_tolerance": "moderate",
        "heat_tolerance": "moderate-high (tolerates roughly 5-47°C; best growth 20-33°C)",
        "flood_tolerance": "high",
        "growth_rate": None,
        "planting_season": None,
        "plantation_use": "Riverbank stabilization, avenue/shade planting, watershed protection",
        "local_presence": None,
        "description": (
            "The strongest candidate among reviewed species for waterlogged "
            "and flood-prone sites — good documented tolerance to soil "
            "salinity, seasonal flooding, and waterlogged clay soils, with a "
            "buttressed trunk adapted to soft riparian habitat. Needs "
            "supplemental watering while establishing, even though the mature "
            "tree tolerates flooding well."
        ),
        "source_ids": ["tree_species_evidence_base.md#arjun"],
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