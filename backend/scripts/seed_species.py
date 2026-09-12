#!/usr/bin/env python3
"""
Seed the tree_species table with a small set of real entries.

Values below are drawn from three sourced categories:
  - tree_species_evidence_base.md (World Agroforestry Centre Agroforestree
    Database, CABI Compendium, PFAF, and peer-reviewed studies) — Shisham,
    Kikar, Neem, Arjun.
  - tree_species_additional.md (extracted directly from four papers already
    ingested into this knowledge base: Komal et al. 2022 "Carbon Storage
    Potential of Agroforestry System near Brick Kilns"; Nisar et al. 2011
    "Ethnomedicinal Flora of District Mandi Bahaudin"; Jamil et al. 2022
    "Invasive Plants Diversity..."; Jamil et al. 2025 "Native Vegetation
    Correlation with Environmental Gradients...") — district-specific facts
    (local_presence, carbon-stock numbers, ethnomedicinal uses) for
    everything below Arjun.
  - General species agronomy (soil_requirements, water_requirement,
    drought/heat/flood_tolerance, growth_rate, plantation_use where not
    already given by the district papers) added 2026-09, sourced from
    Wikipedia, the World Agroforestry Centre's Agroforestree Database /
    "Useful Trees" country fact sheets, and Plants For A Future (PFAF) —
    all general-species (not district-specific) references, cited per
    field in each entry's `source_ids`. These are NOT claims about
    Mandi Bahauddin specifically; they describe the species' documented
    tolerances elsewhere, which is why local_presence / district carbon
    figures are kept separate and untouched.

Fields we still don't have a confident source for are left as `None` — the
API surfaces those as "Not available in current evidence" rather than
guessing. Several entries below are deliberately sparse (habitat-association
-only or ethnomedicinal-only species) because that's genuinely all the
evidence supports — resist the urge to fill in a plausible-sounding value
for these. In particular: local_presence, and any Mandi-Bahauddin-specific
carbon-stock or field-survey claim, are NEVER inferred from general species
literature — only from the four ingested district papers.

Invasive species are included with `plantation_use` explicitly stating they
are NOT recommended, rather than left neutral or omitted — silence would
read as "no opinion" when the evidence actually says "documented concern."

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
        "image_url": "/images/Shisham.jpg",
        "image_source": "User-provided photo (attribution/license to confirm)",
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
        "image_url": "/images/kikar.jpg",
        "image_source": "User-provided photo (attribution/license to confirm)",
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
        "image_url": "/images/neem.jpg",
        "image_source": "User-provided photo (attribution/license to confirm)",
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
        "image_url": "/images/arjun.jpg",
        "image_source": "User-provided photo (attribution/license to confirm)",
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
    # --- Below: local_presence / district figures from tree_species_additional.md;
    # --- general agronomy fields (soil/water/drought/heat/flood/growth_rate/
    # --- plantation_use where not already covered) added from Wikipedia,
    # --- World Agroforestry Centre, and PFAF as noted per entry.
    {
        "common_name": "River Red Gum",
        "scientific_name": "Eucalyptus camaldulensis",
        "local_names": None,
        "image_url": "/images/river_red_gum.jpg",
        "image_source": "User-provided photo (attribution/license to confirm)",
        "soil_requirements": "Very broad tolerance — grows on red or black soils, sandy alluvial soils, and salt-affected land; prefers well-drained sites but also grows on periodically flooded or saline/alkaline soils",
        "water_requirement": "Best growth at 500-1,250 mm annual rainfall, but tolerates as little as 250 mm and as much as ~2,000 mm; naturally found along inland watercourses where underground water is available",
        "drought_tolerance": "high",
        "heat_tolerance": "high",
        "flood_tolerance": "high (some provenances tolerate periodic inundation; naturally dominant along riverbanks and flats)",
        "growth_rate": "fast (an arid-land afforestation trial recorded ~5.0 t/ha/yr aboveground biomass at low planting density)",
        "planting_season": None,
        "plantation_use": "Windbreak, shade, biomass/fuelwood, saline and waterlogged land reclamation; widely planted by forest departments across South Asia",
        "local_presence": (
            "Recorded in agroforestry carbon-stock field sampling across all three tehsils of Mandi Bahauddin "
            "(Mandi-Bahauddin, Phalia, Malakwal); highest carbon stock of any species surveyed in Mandi-Bahauddin tehsil specifically"
        ),
        "description": (
            "The single highest-carbon-stock tree species recorded in the 75-plot "
            "agroforestry survey: 3,951 Mg C ha\u207b\u00b9 total in Mandi-Bahauddin tehsil "
            "(3,135 above-ground + 815 below-ground) — an outlier relative to the rest "
            "of the dataset, not a typical per-tree expectation; the same species scored "
            "far lower in Phalia (0.04 Mg C ha\u207b\u00b9) and Malakwal (20.9 Mg C ha\u207b\u00b9), "
            "showing high site-to-site variability. Widely planted by the Punjab Forest "
            "Department, but flagged elsewhere in this knowledge base's evidence as "
            "ecologically problematic for urban/water resources — rapid water-table "
            "depletion and poor shade quality are commonly cited concerns, separate from "
            "its carbon performance."
        ),
        "source_ids": [
            "tree_species_additional.md#eucalyptus-camaldulensis",
            "Komal et al. 2022, Agriculture 12(2): 295",
            "Wikipedia: Eucalyptus camaldulensis",
            "World Agroforestry Centre, vikaspedia.in — Eucalyptus site factors and rainfall range",
            "Tanouchi et al. 2009, Journal of Ecotechnology Research 14(3): 183-188 (arid-land afforestation growth rate)",
        ],
    },
    {
        "common_name": "Jamun",
        "scientific_name": "Syzygium cumini",
        "local_names": ["Java Plum"],
        "image_url": "/images/jamun.jpg",
        "image_source": "User-provided photo (attribution/license to confirm)",
        "soil_requirements": "Thrives in well-drained soils but tolerates waterlogging; adaptable to a wide range of soil types",
        "water_requirement": "Grows best with rainfall over 1,000 mm annually; sensitive to soil salinity (ECe 7-10 dS/m)",
        "drought_tolerance": "moderate (described as drought-tolerant once mature by some horticultural sources, but experimental studies show growth and yield decline under moderate-to-severe drought stress)",
        "heat_tolerance": "high (tropical/subtropical species grown 0-1,800 m altitude)",
        "flood_tolerance": "high (documented tolerant of waterlogged soils)",
        "growth_rate": "fast",
        "planting_season": None,
        "plantation_use": "Shade, windbreak, dune fixation, fuelwood, bee forage, edible fruit; suitable for low-lying or flood-prone plots given its waterlogging tolerance",
        "local_presence": (
            "Recorded in agroforestry carbon-stock sampling across all three tehsils "
            "of Mandi Bahauddin; second-highest carbon stock species in Mandi-Bahauddin "
            "tehsil specifically"
        ),
        "description": (
            "Total carbon stock 282 Mg C ha\u207b\u00b9 in Mandi-Bahauddin tehsil (136 "
            "above-ground + 35 below-ground), notably lower in Phalia (0.98 Mg C ha\u207b\u00b9) "
            "and Malakwal (1.20 Mg C ha\u207b\u00b9) — the same site-variability pattern seen "
            "with Eucalyptus. Documented tolerant of waterlogged soils, making it relevant "
            "for low-lying or flood-prone plots in Mandi Bahauddin."
        ),
        "source_ids": [
            "tree_species_additional.md#syzygium-cumini",
            "Komal et al. 2022, Agriculture 12(2): 295",
            "World Agroforestry Centre, Syzygium_cumini_KEN.pdf (rainfall/soil)",
            "Rahman et al. 2025, Discover Life Sciences (drought-stress growth response)",
        ],
    },
    {
        "common_name": "Poplar",
        "scientific_name": "Populus ciliata / Populus deltoides",
        "local_names": None,
        "image_url": "/images/poplar.jpg",
        "image_source": "User-provided photo (attribution/license to confirm)",
        "soil_requirements": (
            "P. ciliata (Himalayan poplar): wide range from sandy river-bed soils to clayey loam, best growth on "
            "well-aerated loamy soil with abundant moisture; does not tolerate alkalinity, prefers slightly acidic to "
            "neutral soils. P. deltoides, the species actually planted at scale in Punjab's irrigated plains "
            "agroforestry, is grown on irrigated alluvial agricultural land rather than rainfed hill soils."
        ),
        "water_requirement": (
            "P. ciliata's native range receives 660-2,970 mm mean annual rainfall at 1,700-3,000 m altitude in the "
            "Himalayas — conditions very different from Mandi Bahauddin's plains. P. deltoides in Punjab agroforestry "
            "is grown under irrigation on farmland, not as a rainfed species."
        ),
        "drought_tolerance": "low (both species are light-demanding, moisture-loving, and generally grown with irrigation or abundant natural moisture, not as drought-tolerant plantation trees)",
        "heat_tolerance": None,
        "flood_tolerance": None,
        "growth_rate": "fast",
        "planting_season": None,
        "plantation_use": (
            "P. deltoides is the backbone of irrigated-plains agroforestry in Punjab, Haryana, and western Uttar "
            "Pradesh (an estimated 60,000 ha equivalent in India alone), grown on farm boundaries and irrigated "
            "fields on a 6-8 year rotation for plywood/matchwood. P. ciliata is used mainly for erosion control on "
            "shallow Himalayan soils and is not the species typically planted in Punjab's plains."
        ),
        "local_presence": "Recorded in agroforestry carbon-stock field sampling across all three tehsils of Mandi Bahauddin",
        "description": (
            "P. ciliata total carbon stock: 75.9 Mg C ha\u207b\u00b9 (Mandi-Bahauddin), 44.5 Mg C ha\u207b\u00b9 "
            "(Malakwal), 0.40 Mg C ha\u207b\u00b9 (Phalia). Published above/below-ground biomass allometric "
            "equations exist for P. deltoides specifically (Das & Chaturvedi 2005 methodology), "
            "indicating both Populus species are part of standard Punjab agroforestry planting. Caveat worth "
            "flagging for plantation planning: P. ciliata is naturally a temperate, high-altitude Himalayan "
            "species (1,700-3,000 m) — the poplar actually grown at scale in Punjab's irrigated plains is usually "
            "P. deltoides, not P. ciliata; the carbon-stock survey did not distinguish which Populus taxon was "
            "measured at each plot."
        ),
        "source_ids": [
            "tree_species_additional.md#populus",
            "Komal et al. 2022, Agriculture 12(2): 295",
            "Wikipedia: Populus ciliata",
            "World Agroforestry Centre, Populus_ciliata.PDF (Agroforestree Database 4.0)",
            "eFloraofIndia — Populus deltoides cultivation statistics in Indian Punjab agroforestry",
        ],
    },
    {
        "common_name": "Ber",
        "scientific_name": "Ziziphus mauritiana",
        "local_names": ["Baer", "Jujube"],
        "image_url": "/images/ber.jpg",
        "image_source": "User-provided photo (attribution/license to confirm)",
        "soil_requirements": "Highly adaptable; flourishes even in alkaline soils up to pH 9.2, though deep sandy loam to loamy soils with neutral-to-slightly-alkaline pH are optimum for growth",
        "water_requirement": "Tolerates 125-2,225 mm annual rainfall but is most widespread in the 300-500 mm range",
        "drought_tolerance": "high",
        "heat_tolerance": "high (survives temperatures from 7°C to 50°C)",
        "flood_tolerance": "moderate-high (documented high tolerance to both waterlogging and drought)",
        "growth_rate": "fast (starts fruiting within 3 years)",
        "planting_season": None,
        "plantation_use": "Erosion control, shade, shelter/windbreak, living thorny fence, fodder (leaves), reclamation of nutrient-depleted or marginal land, edible fruit",
        "local_presence": (
            "Confirmed in Ethnomedicinal Survey field data (Phalia tehsil), in agroforestry "
            "carbon-stock sampling across all three tehsils, and a related species "
            "(Z. nummularia) recorded among dry-land-habitat species in the Native "
            "Vegetation Paper's CCA analysis"
        ),
        "description": (
            "Total carbon stock 37.8 Mg C ha\u207b\u00b9 (Mandi-Bahauddin), 18.7 Mg C ha\u207b\u00b9 (Malakwal), "
            "0.13 Mg C ha\u207b\u00b9 (Phalia). Leaf and fruit documented ethnomedicinally for skin "
            "infections where pus is present, and for iron deficiency."
        ),
        "source_ids": [
            "tree_species_additional.md#ziziphus",
            "Komal et al. 2022, Agriculture 12(2): 295",
            "Nisar et al. 2011, Middle-East J. Sci. Res. 9(2): 233-238",
            "Jamil et al. 2025, J. Anim. Plant Sci. 35(5): 1269-1280",
            "Wikipedia: Ziziphus mauritiana",
            "FAO Ecocrop datasheet — Ziziphus mauritiana (rainfall/soil pH range)",
        ],
    },
    {
        "common_name": "Dherek",
        "scientific_name": "Melia azedarach",
        "local_names": ["Chinaberry", "Bakain"],
        "image_url": "/images/derek.jpg",
        "image_source": "User-provided photo (attribution/license to confirm)",
        "soil_requirements": "Grows in most soils, both acidic and saline; highly adaptable from warm-temperate to humid-tropical conditions",
        "water_requirement": None,
        "drought_tolerance": "high",
        "heat_tolerance": "high",
        "flood_tolerance": None,
        "growth_rate": "fast",
        "planting_season": None,
        "plantation_use": "Shade and avenue/ornamental tree, timber, poles; caution — seeds (and to a lesser extent leaves and bark) are toxic to humans and livestock in large amounts",
        "local_presence": "Confirmed in Ethnomedicinal Survey field data (Phalia tehsil) and agroforestry carbon-stock sampling across all three tehsils",
        "description": (
            "Consistently one of the lowest carbon-stock performers recorded: 23.8 Mg C ha\u207b\u00b9 "
            "(Mandi-Bahauddin), 0.06 Mg C ha\u207b\u00b9 (Phalia), 0.05 Mg C ha\u207b\u00b9 (Malakwal — the lowest "
            "value recorded for any species in that tehsil). Leaf and fruit documented "
            "ethnomedicinally for skin infection and general skin diseases. Given its "
            "consistently low carbon performance across all three tehsils, this is a weaker "
            "candidate specifically for carbon-sequestration-focused planning, despite its "
            "ethnomedicinal value and common presence in Punjab."
        ),
        "source_ids": [
            "tree_species_additional.md#melia-azedarach",
            "Komal et al. 2022, Agriculture 12(2): 295",
            "Nisar et al. 2011, Middle-East J. Sci. Res. 9(2): 233-238",
            "World Agroforestry Centre, Melia_azedarach_KEN.pdf",
            "Wikipedia: Melia azedarach",
        ],
    },
    {
        "common_name": "Toot",
        "scientific_name": "Morus alba",
        "local_names": ["White Mulberry"],
        "image_url": "/images/toot.jpg",
        "image_source": "User-provided photo (attribution/license to confirm)",
        "soil_requirements": "Grows on a variety of soils from sandy loam to clayey loam, but prefers deep, alluvial, loamy soil with sufficient moisture and pH 6.0-7.5",
        "water_requirement": "Native range receives 1,500-2,500 mm mean annual rainfall, though the species is widely cultivated well outside this range under irrigation or in drier plains plantings",
        "drought_tolerance": "moderate (sources conflict: several horticultural references call it drought-tolerant once established, but the World Agroforestry Centre's Agroforestree Database describes it as shade-tolerant and highly susceptible to drought — treat this as an open question rather than settled)",
        "heat_tolerance": "high (documented growing across a 0-43°C mean annual temperature range)",
        "flood_tolerance": None,
        "growth_rate": "fast",
        "planting_season": None,
        "plantation_use": "Sericulture (leaves used for silkworm rearing), shade/shelter for orchards, erosion control on soil-conservation structures, ornamental roadside/avenue tree, soil improvement via leaf litter",
        "local_presence": "Recorded in agroforestry carbon-stock field sampling across all three tehsils of Mandi Bahauddin",
        "description": (
            "Low carbon stock across all tehsils: 18.7 Mg C ha\u207b\u00b9 (Mandi-Bahauddin), "
            "0.02 Mg C ha\u207b\u00b9 (Phalia — the lowest value recorded in that tehsil), "
            "0.09 Mg C ha\u207b\u00b9 (Malakwal)."
        ),
        "source_ids": [
            "tree_species_additional.md#morus",
            "Komal et al. 2022, Agriculture 12(2): 295",
            "World Agroforestry Centre, Morus_alba.PDF (Agroforestree Database 4.0)",
            "Wikipedia: Morus alba",
        ],
    },
    {
        "common_name": "Kala Toot",
        "scientific_name": "Morus nigra",
        "local_names": ["Black Mulberry"],
        "image_url": "/images/black toot.jpg",
        "image_source": "User-provided photo (attribution/license to confirm)",
        "soil_requirements": "Tolerant of a wide range of soils, from poor sandy soils to deep fertile loams; pH preference slightly acidic to highly alkaline",
        "water_requirement": None,
        "drought_tolerance": "moderate (commonly described as somewhat drought-resistant once established, but sources agree it still needs watering during long dry spells; it is also noted as the slowest-growing and least drought-hardy of the commonly cultivated mulberry species)",
        "heat_tolerance": "moderate-high",
        "flood_tolerance": None,
        "growth_rate": "moderate-slow (described as the slowest-growing of the commonly cultivated mulberry species, in contrast to the fast growth typically reported for M. alba)",
        "planting_season": None,
        "plantation_use": None,
        "local_presence": "Confirmed in Ethnomedicinal Survey field data (Phalia tehsil)",
        "description": (
            "A distinct species from Morus alba (White Mulberry) — root, leaf, and fruit "
            "documented ethnomedicinally for treating \"bad thorax\" and stomach worms. "
            "No district-specific carbon-stock, soil, or climate-tolerance data is available for this species "
            "in any of the four Mandi Bahauddin papers ingested so far; the general growing-condition notes above "
            "come from horticultural references rather than local field data and should be read as background only."
        ),
        "source_ids": [
            "tree_species_additional.md#morus",
            "Nisar et al. 2011, Middle-East J. Sci. Res. 9(2): 233-238",
            "Wikipedia: Morus nigra",
            "growables.org Tropical Fruit database — Mulberry (Morus nigra growth-rate comparison)",
        ],
    },
    {
        "common_name": "Siris",
        "scientific_name": "Albizia lebbeck",
        "local_names": None,
        "image_url": "/images/siris.jpg",
        "image_source": "User-provided photo (attribution/license to confirm)",
        "soil_requirements": "Establishes well on fertile, well-drained loamy soils but poorly on heavy clays; tolerates acidic, alkaline, saline, and waterlogged soils (cross-referenced with core evidence base)",
        "water_requirement": "500-2,500 mm annual rainfall tolerated, though it has also been grown successfully on as little as 400 mm/yr; roots sit near the surface so it benefits from a reasonably high water table",
        "drought_tolerance": "high (cross-referenced with core evidence base)",
        "heat_tolerance": "high (cross-referenced with core evidence base)",
        "flood_tolerance": "moderate (tolerates waterlogged soils per the World Agroforestry Centre, though its shallow root system makes it liable to blow over in storms)",
        "growth_rate": "fast (nitrogen-fixing)",
        "planting_season": None,
        "plantation_use": "Standard Punjab linear-plantation recommendation; nitrogen-fixing",
        "local_presence": (
            "The most extensively documented species in the Ethnomedicinal Survey's use "
            "list, corroborating established local presence and use in Mandi Bahauddin "
            "specifically, beyond general Punjab forestry literature"
        ),
        "description": (
            "Bark used ethnomedicinally for inflammations, boils, cough, eye infections, "
            "flu, gingivitis, lung problems, pectoral problems, as a general tonic, and "
            "for abdominal tumors, hernia, and secondary infertility. Already noted "
            "elsewhere in this knowledge base as heat- and drought-tolerant and a fast "
            "nitrogen-fixer."
        ),
        "source_ids": [
            "tree_species_additional.md#albizia-lebbeck",
            "Nisar et al. 2011, Middle-East J. Sci. Res. 9(2): 233-238",
            "tree_species_evidence_base.md (cross-reference)",
            "World Agroforestry Centre, Albizia_lebbeck.PDF (Agroforestree Database 4.0)",
        ],
    },
    {
        "common_name": "Bamboo",
        "scientific_name": "Bambusa vulgaris",
        "local_names": None,
        "image_url": "/images/bambo.jpg",
        "image_source": "User-provided photo (attribution/license to confirm)",
        "soil_requirements": "Tolerates a wide range of soil types and climatic conditions; grows vigorously on moist soil under humid conditions but adapts to semi-arid areas and degraded or flooded land",
        "water_requirement": None,
        "drought_tolerance": "moderate (may lose leaves and become completely defoliated in the dry season, but recovers once the rainy season starts)",
        "heat_tolerance": "high (tropical-subtropical species, found up to 1,200 m altitude)",
        "flood_tolerance": "moderate-high (documented growing on degraded and flooded lands, and along riverbanks)",
        "growth_rate": "fast",
        "planting_season": None,
        "plantation_use": "Standard agroforestry species (recorded across all three surveyed tehsils); light construction, basketry, plant-support sticks, paper pulp, ornamental use",
        "local_presence": "Recorded in agroforestry carbon-stock field sampling across all three tehsils of Mandi Bahauddin",
        "description": (
            "Total carbon stock: 67.6 Mg C ha\u207b\u00b9 (Mandi-Bahauddin), 2.52 Mg C ha\u207b\u00b9 (Phalia), "
            "0.20 Mg C ha\u207b\u00b9 (Malakwal)."
        ),
        "source_ids": [
            "tree_species_additional.md#bambusa-vulgaris",
            "Komal et al. 2022, Agriculture 12(2): 295",
            "Wikipedia: Bambusa vulgaris",
            "guaduabamboo.com species profile — Bambusa vulgaris habitat and climate tolerance",
        ],
    },
    {
        "common_name": "Pipal",
        "scientific_name": "Ficus religiosa",
        "local_names": ["Sacred Fig"],
        "image_url": "/images/pipal.jpg",
        "image_source": "User-provided photo (attribution/license to confirm)",
        "soil_requirements": "Grows on a wide variety of soils but prefers deep, alluvial sandy loam with good drainage; also found on shallow soils including rock crevices",
        "water_requirement": "500-5,000 mm mean annual rainfall tolerated",
        "drought_tolerance": "moderate (semi-evergreen — can shed leaves during drought and re-leafs within weeks once conditions improve)",
        "heat_tolerance": "moderate-high (tolerates air temperatures of roughly 0-35°C; growth diminishes above this)",
        "flood_tolerance": "moderate (described as a flood-tolerant plant by horticultural sources)",
        "growth_rate": "fast",
        "planting_season": None,
        "plantation_use": None,
        "local_presence": "Confirmed in Ethnomedicinal Survey field data (Phalia tehsil)",
        "description": (
            "Bark used ethnomedicinally to treat gonorrhea. Caution: large fig species — "
            "the broader evidence base in this knowledge base flags Ficus species "
            "generally for aggressive root systems that can damage underground "
            "infrastructure (drains, plumbing), relevant for site selection near urban "
            "infrastructure, though this specific caution is not independently stated in "
            "the Ethnomedicinal Survey itself."
        ),
        "source_ids": [
            "tree_species_additional.md#ficus",
            "Nisar et al. 2011, Middle-East J. Sci. Res. 9(2): 233-238",
            "Wikipedia: Ficus religiosa",
            "World Agroforestry Centre, Ficus_religiosa.PDF (Agroforestree Database 4.0)",
        ],
    },
    {
        "common_name": "Banyan",
        "scientific_name": "Ficus benghalensis",
        "local_names": ["Boher"],
        "image_url": "/images/banyan.jpg",
        "image_source": "User-provided photo (attribution/license to confirm)",
        "soil_requirements": "Grows on clay and loam soils; tolerates a broad range once established",
        "water_requirement": "Low water requirement once established, per horticultural references, though this is not district-specific data",
        "drought_tolerance": "high (most Ficus species, including this one, are commonly described as drought-tolerant once established)",
        "heat_tolerance": "high",
        "flood_tolerance": None,
        "growth_rate": "fast",
        "planting_season": None,
        "plantation_use": None,
        "local_presence": "Confirmed in Ethnomedicinal Survey field data (Phalia tehsil)",
        "description": (
            "Adventitious roots and latex used ethnomedicinally to treat gonorrhea, "
            "chronic flu, and influenza. Same root-system infrastructure caution as "
            "Ficus religiosa (see that entry) — not independently stated in the "
            "Ethnomedicinal Survey itself."
        ),
        "source_ids": [
            "tree_species_additional.md#ficus",
            "Nisar et al. 2011, Middle-East J. Sci. Res. 9(2): 233-238",
            "Wikipedia: Ficus benghalensis",
        ],
    },
    {
        "common_name": "Anar",
        "scientific_name": "Punica granatum",
        "local_names": ["Pomegranate"],
        "image_url": "/images/Anar.jpg",
        "image_source": "User-provided photo (attribution/license to confirm)",
        "soil_requirements": "Tolerates a wide range of soils (chalk, loam, sand) provided they are well-drained; adaptable to acid, alkaline, or neutral pH",
        "water_requirement": "Very drought tolerant once established; needs regular watering only while young",
        "drought_tolerance": "high",
        "heat_tolerance": "high (requires warm autumn temperatures for fruit to ripen)",
        "flood_tolerance": "low (requires well-drained soil; poor tolerance of waterlogging)",
        "growth_rate": None,
        "planting_season": None,
        "plantation_use": None,
        "local_presence": "Confirmed in Ethnomedicinal Survey field data (Phalia tehsil)",
        "description": (
            "Exocarp of fruit used ethnomedicinally for dysentery and menstrual "
            "irregularities. District-specific carbon-stock or soil data is not available — "
            "the general growing-condition notes above are background from horticultural "
            "references, not a plantation-suitability recommendation for this district."
        ),
        "source_ids": [
            "tree_species_additional.md#fruit-trees",
            "Nisar et al. 2011, Middle-East J. Sci. Res. 9(2): 233-238",
            "RHS Plant Profile: Punica granatum",
        ],
    },
    {
        "common_name": "Amrood",
        "scientific_name": "Psidium guajava",
        "local_names": ["Guava"],
        "image_url": "/images/amrood.jpg",
        "image_source": "User-provided photo (attribution/license to confirm)",
        "soil_requirements": "Not fussy about soil quality; tolerates a wide range including loam, though heavy clay should be avoided to prevent root rot",
        "water_requirement": "Needs regular irrigation in hot weather; sources disagree on drought tolerance (some call it drought-tolerant once established; a dedicated arid-climate growing guide states it is not drought tolerant and needs irrigation every 1-2 days in high heat)",
        "drought_tolerance": "low-moderate (sources conflict — treat as an open question rather than settled; see water_requirement)",
        "heat_tolerance": "moderate (good heat resistance generally, but growth is stressed above roughly 43°C and severely stressed above 46°C)",
        "flood_tolerance": None,
        "growth_rate": "moderate-fast",
        "planting_season": None,
        "plantation_use": None,
        "local_presence": "Confirmed in Ethnomedicinal Survey field data (Phalia tehsil)",
        "description": (
            "Fruit used ethnomedicinally for appetite improvement, stomach problems, old "
            "cough, bronchitis, and chronic whooping cough. District-specific carbon-stock, "
            "soil, or climate-tolerance data is not available — listed for local presence "
            "and general background only, not a plantation-suitability recommendation. "
            "Also worth noting: a Pakistan-based study found guava growth and yield "
            "significantly reduced under combined salinity and drought stress, which is "
            "relevant if considering it for marginal or saline plots."
        ),
        "source_ids": [
            "tree_species_additional.md#fruit-trees",
            "Nisar et al. 2011, Middle-East J. Sci. Res. 9(2): 233-238",
            "Sohail 2012, effect of salinity and drought on Psidium guajava growth (AGRIS/FAO)",
            "gardenoracle.com — Growing Guava heat/drought tolerance notes",
        ],
    },
    {
        "common_name": "Khajur",
        "scientific_name": "Phoenix dactylifera",
        "local_names": ["Date Palm"],
        "image_url": "/images/kajur.jpg",
        "image_source": "User-provided photo (attribution/license to confirm)",
        "soil_requirements": "Tolerant of clay, loam, and sandy soils across acidic, neutral, or alkaline pH",
        "water_requirement": "Low water requirement once established",
        "drought_tolerance": "high",
        "heat_tolerance": "high",
        "flood_tolerance": "low",
        "growth_rate": "slow",
        "planting_season": None,
        "plantation_use": None,
        "local_presence": "Confirmed in Ethnomedicinal Survey field data (Phalia tehsil)",
        "description": (
            "Fruit used ethnomedicinally for general body weakness. District-specific "
            "carbon-stock, soil, or climate-tolerance data is not available — listed for "
            "local presence and general background only, not a plantation-suitability "
            "recommendation for this district."
        ),
        "source_ids": [
            "tree_species_additional.md#fruit-trees",
            "Nisar et al. 2011, Middle-East J. Sci. Res. 9(2): 233-238",
            "AUB Landscape Plant Database — Phoenix dactylifera",
        ],
    },
    {
        "common_name": "Aam",
        "scientific_name": "Mangifera indica",
        "local_names": ["Mango"],
        "image_url": "/images/aam.jpg",
        "image_source": "User-provided photo (attribution/license to confirm)",
        "soil_requirements": "Prefers loam or sandy soils, acidic to alkaline pH",
        "water_requirement": "Needs regular water despite being moderately drought tolerant once established; requires full sun and room to grow",
        "drought_tolerance": "moderate (moderately drought tolerant once established per horticultural sources, but mature trees still need regular watering, and a controlled study found substantial genotype-dependent decline in shoot dry weight under drought)",
        "heat_tolerance": "high",
        "flood_tolerance": "low (poor tolerance of waterlogging/salt; prefers warm dry winters and moist hot summers)",
        "growth_rate": "moderate",
        "planting_season": None,
        "plantation_use": None,
        "local_presence": "Confirmed in Ethnomedicinal Survey field data (Phalia tehsil)",
        "description": (
            "Leaf and seed used ethnomedicinally for earache and vomiting. District-specific "
            "carbon-stock, soil, or climate-tolerance data is not available — listed for local "
            "presence and general background only, not a plantation-suitability recommendation."
        ),
        "source_ids": [
            "tree_species_additional.md#fruit-trees",
            "Nisar et al. 2011, Middle-East J. Sci. Res. 9(2): 233-238",
            "AUB Landscape Plant Database — Mangifera indica",
            "Sandeep et al. 2023, Indian J. Agricultural Sciences 93(8) — mango rootstock drought response",
        ],
    },
    {
        "common_name": "Frash",
        "scientific_name": "Tamarix aphylla / Tamarix dioica",
        "local_names": None,
        "image_url": "/images/farash.jpg",
        "image_source": "User-provided photo (attribution/license to confirm)",
        "soil_requirements": "T. aphylla thrives best on loam but is also found on stiff clays and sand; has a remarkable capacity for growing on saline soil and is very resistant to saline and alkaline soils generally",
        "water_requirement": "T. aphylla tolerates roughly 100-900 mm mean annual rainfall and grows more vigorously on land subject to occasional inundation than on land never flooded",
        "drought_tolerance": "high (T. aphylla is documented drought, heat, salt, and frost tolerant)",
        "heat_tolerance": "high (tolerates mean annual temperatures of 10-50°C)",
        "flood_tolerance": "moderate-high (grows more vigorously with occasional inundation)",
        "growth_rate": "fast",
        "planting_season": None,
        "plantation_use": "Windbreak and shade tree in agriculture, especially in drier regions; erosion control and reclamation of saline/marginal land",
        "local_presence": (
            "Habitat association only — recorded in the Native Vegetation Paper's CCA "
            "analysis, associated with the quadrant influenced by soil organic "
            "constituents (SOC), alongside graveyard and riverine-land habitats"
        ),
        "description": (
            "Consistent with Tamarix's general reputation as salt-tolerant, but this "
            "district-specific dataset only gives habitat/edaphic association, not a "
            "detailed tolerance profile — needs further sourcing before use in "
            "plantation recommendations. The soil/water/tolerance figures above come "
            "from general Tamarix aphylla literature, not a Mandi Bahauddin field study."
        ),
        "source_ids": [
            "tree_species_additional.md#habitat-association-only",
            "Jamil et al. 2025, J. Anim. Plant Sci. 35(5): 1269-1280",
            "Wikipedia: Tamarix aphylla",
            "World Agroforestry Centre, Tamarix_aphylla.PDF (Agroforestree Database 4.0)",
        ],
    },
    {
        "common_name": "Peelu",
        "scientific_name": "Salvadora oleoides",
        "local_names": None,
        "image_url": "/images/pelu.jpg",
        "image_source": "User-provided photo (attribution/license to confirm)",
        "soil_requirements": "Grows on saline soils; found in coastal regions and on inland saline soils in the arid regions of western India and Pakistan",
        "water_requirement": None,
        "drought_tolerance": None,
        "heat_tolerance": None,
        "flood_tolerance": None,
        "growth_rate": None,
        "planting_season": None,
        "plantation_use": "Shelterbelts and windbreaks in desert tracts; erosion control and reclamation of degraded saline land (regenerates freely by root suckers)",
        "local_presence": (
            "Habitat association only — recorded in the same SOC-associated CCA "
            "quadrant as Tamarix (above), alongside graveyard/riverine habitats"
        ),
        "description": (
            "Needs further sourcing before use in plantation recommendations — only habitat "
            "association is documented in this district's dataset. General literature "
            "describes it as highly salt tolerant and part of tropical thorn-forest "
            "vegetation alongside Prosopis and Tamarix, but frost-sensitive; this is "
            "background only, not a district-specific tolerance profile."
        ),
        "source_ids": [
            "tree_species_additional.md#habitat-association-only",
            "Jamil et al. 2025, J. Anim. Plant Sci. 35(5): 1269-1280",
            "World Agroforestry Centre, Salvadora_oleoides.PDF (Agroforestree Database 4.0)",
        ],
    },
    {
        "common_name": "Devi (Mesquite)",
        "scientific_name": "Prosopis juliflora",
        "local_names": None,
        "image_url": "/images/devi.jpg",
        "image_source": "User-provided photo (attribution/license to confirm)",
        "soil_requirements": "Tolerant of a wide range of soils including saline and waterlogged soils; deep-rooted, able to reach the water table in desert conditions",
        "water_requirement": "Highly drought tolerant; deep taproot allows survival where other species fail",
        "drought_tolerance": "high",
        "heat_tolerance": "high",
        "flood_tolerance": "moderate (tolerates waterlogged as well as dry soils)",
        "growth_rate": "moderate",
        "planting_season": None,
        "plantation_use": "Not recommended — documented as an invasive alien species in Mandi Bahauddin district",
        "local_presence": (
            "Documented as one of 43 invasive alien species recorded across 120 sampling "
            "sites in the district; also appears independently in the Native Vegetation "
            "Paper's species list. Invasive species overall were most common in "
            "scrubland and forest habitats."
        ),
        "description": (
            "Native to North & South America. Among the most common invasive species "
            "recorded in the district. Its salt and drought tolerance and deep root system "
            "are exactly why it spreads aggressively and displaces native vegetation, "
            "reducing biodiversity and, in some regions, depleting water resources."
        ),
        "source_ids": [
            "tree_species_additional.md#invasive-tree-species",
            "Jamil et al. 2022, Sustainability 14(20): 13312",
            "AUB Landscape Plant Database — Prosopis juliflora",
        ],
    },
    {
        "common_name": "Subabul",
        "scientific_name": "Leucaena leucocephala",
        "local_names": None,
        "image_url": "/images/subaul.jpg",
        "image_source": "User-provided photo (attribution/license to confirm)",
        "soil_requirements": "Tolerant of a wide range of soils including limestone, wet and dry soils, and those with moderate salt levels; prefers pH 6-7.7 but tolerates 5-8.5",
        "water_requirement": "Grows well only in subhumid or humid climates with dry seasons of up to 6-7 months",
        "drought_tolerance": "high",
        "heat_tolerance": "high",
        "flood_tolerance": None,
        "growth_rate": "fast (nitrogen-fixing)",
        "planting_season": None,
        "plantation_use": "Not recommended — documented as an invasive alien species in Mandi Bahauddin district",
        "local_presence": "Documented as one of 43 invasive alien species recorded across 120 sampling sites in the district",
        "description": (
            "Native to Mexico/Central America. A common invasive species; its fast "
            "nitrogen-fixing growth, drought tolerance, and prolific year-round seed "
            "production are part of why it spreads aggressively as a coloniser of "
            "disturbed and ruderal sites."
        ),
        "source_ids": [
            "tree_species_additional.md#invasive-tree-species",
            "Jamil et al. 2022, Sustainability 14(20): 13312",
            "farmknowledge.info — Leucaena leucocephala growing conditions (PFAF-derived)",
        ],
    },
    {
        "common_name": "Chinese Tallow",
        "scientific_name": "Sapium sebiferum",
        "local_names": None,
        "image_url": "/images/leaves-of-chinese-tallow.jpg",
        "image_source": "User-provided photo (attribution/license to confirm)",
        "soil_requirements": "Not choosy about soil type; tolerates clay, sand, and loam across alkaline-to-acidic pH, from wet to well-drained conditions",
        "water_requirement": None,
        "drought_tolerance": "moderate-high (deep taproot allows young trees to withstand periods of drought; also documented tolerant of flooding and brackish/saline water — an unusually wide moisture tolerance)",
        "heat_tolerance": "moderate-high (subtropical to warm-temperate species, hardy to light frost)",
        "flood_tolerance": "high (tolerant of inundation in fresh, brackish, or saltwater)",
        "growth_rate": "fast",
        "planting_season": None,
        "plantation_use": "Not recommended — documented as an invasive alien species in Mandi Bahauddin district",
        "local_presence": "Documented as one of 43 invasive alien species recorded across 120 sampling sites in the district",
        "description": (
            "Native to Japan/China (also known as Triadica sebifera, a reclassification of "
            "the older name Sapium sebiferum). Recorded as an invasive tree species in the "
            "district; its unusually broad tolerance of both drought and flooding, plus "
            "prolific seed production dispersed by birds and water, is part of why it "
            "aggressively displaces native vegetation in other invaded regions."
        ),
        "source_ids": [
            "tree_species_additional.md#invasive-tree-species",
            "Jamil et al. 2022, Sustainability 14(20): 13312",
            "Wikipedia: Triadica sebifera",
            "University of Florida IFAS Extension — Triadica sebifera (ST583)",
        ],
    },
    {
        "common_name": "Paper Mulberry",
        "scientific_name": "Broussonetia papyrifera",
        "local_names": None,
        "image_url": "/images/paper_mullbery.jpg",
        "image_source": "User-provided photo (attribution/license to confirm)",
        "soil_requirements": "Tolerant of a wide variety of soil types, including stony, sterile, or alkaline soils; prefers rich, moist, well-drained soil but tolerates far less",
        "water_requirement": None,
        "drought_tolerance": "high",
        "heat_tolerance": "high (also tolerates urban pollution)",
        "flood_tolerance": None,
        "growth_rate": "fast",
        "planting_season": None,
        "plantation_use": "Not recommended — documented as an invasive alien species in Mandi Bahauddin district",
        "local_presence": (
            "Documented as one of 43 invasive alien species recorded across 120 sampling "
            "sites in the district; also appears in the Native Vegetation Paper's "
            "ordination analysis"
        ),
        "description": (
            "Native to South-East Asia (China, Japan, Korea). Recorded as an invasive tree "
            "species in the district; its fast growth, drought/heat tolerance, and "
            "aggressive suckering and self-seeding habit are well documented as invasive "
            "traits elsewhere, including in the southeastern United States."
        ),
        "source_ids": [
            "tree_species_additional.md#invasive-tree-species",
            "Jamil et al. 2022, Sustainability 14(20): 13312",
            "harvesttotable.com — Broussonetia papyrifera growing conditions",
        ],
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