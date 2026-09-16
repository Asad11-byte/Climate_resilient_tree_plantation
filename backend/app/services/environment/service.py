"""
Orchestrates environmental data lookups: Supabase cache first, then live
providers (SoilGrids, NASA POWER, Sentinel-2) on a cache miss — or on a
cache hit that's missing fields a provider could plausibly fill — caching
whatever comes back.

Rule: if a live provider fails or has no data, that provider is simply
skipped — never guessed. Only if EVERY provider comes back empty (and the
cache has nothing either) does this report "unavailable". A Supabase outage
(cache read/write failing) is a different, harder failure and is allowed to
propagate as ProviderUnavailableError so the API returns 503, not a false
"no data".

CACHE COMPLETENESS: a cached row is only trusted as-is if the "worth
backfilling" fields (soil + vegetation — NOT temperature/rainfall, which
NASA POWER almost always supplies) are populated. A row cached while a
provider was broken — e.g. all soil fields null from before the GEE
SoilGrids fix — would otherwise be served as a false "complete" answer
forever, even after providers start working for that area. See
_SOIL_BACKFILL_FIELDS / _VEGETATION_BACKFILL_FIELDS / _is_incomplete below.

THE FIX (this revision): soil and vegetation are now checked as two
INDEPENDENT categories, not one flat list. Previously, a row counted as
"incomplete" only if literally every backfill field was null. That meant a
row where soil succeeded but Sentinel legitimately found no cloud-free
image (SentinelProvider returns None for that — not an error) got cached
with soil populated and ndvi/ndwi/land_cover null, and from then on was
treated as permanently "complete" — soil being present was enough to skip
re-querying, so vegetation fields for that location could never be filled
in again, even on a later request where a cloud-free image existed. Now a
row missing an ENTIRE category (all of soil, or all of vegetation) is
still treated as incomplete and re-queried, independent of whether the
other category already succeeded. A single missing field within an
otherwise-populated category (e.g. just land_cover, with ndvi/ndwi
present) is still left alone — same original reasoning: a point can
legitimately be missing one specific field without needing a retry.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger
from app.core.exceptions import ProviderUnavailableError
from app.repositories.environmental_repository import EnvironmentalRepository
from app.services.environment.base import EnvironmentalReading, EnvironmentDataProvider

logger = get_logger(__name__)

_SOIL_BACKFILL_FIELDS = ("soil_ph", "clay", "sand", "organic_carbon")
_VEGETATION_BACKFILL_FIELDS = ("ndvi", "ndwi", "land_cover")
_BACKFILL_FIELDS = _SOIL_BACKFILL_FIELDS + _VEGETATION_BACKFILL_FIELDS


@dataclass
class EnvironmentResult:
    available: bool
    record: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


class EnvironmentDataService:
    def __init__(
        self,
        repository: EnvironmentalRepository,
        providers: List[EnvironmentDataProvider],
        cache_tolerance: float = 0.05,
    ):
        self._repository = repository
        self._providers = providers
        self._cache_tolerance = cache_tolerance

    async def get_environment(self, latitude: float, longitude: float) -> EnvironmentResult:
        cached = await self._repository.find_near(latitude, longitude, self._cache_tolerance)

        if cached is not None and not self._is_incomplete(cached):
            return EnvironmentResult(available=True, record=cached)

        if cached is not None:
            logger.info(
                "Cached row for (%s, %s) is missing %s — treating as a partial "
                "miss and re-querying live providers",
                latitude, longitude, self._missing_fields(cached),
            )

        readings: List[EnvironmentalReading] = []
        sources_used: List[str] = []
        for provider in self._providers:
            try:
                reading = await provider.fetch(latitude, longitude)
            except ProviderUnavailableError:
                logger.warning("Environment provider '%s' unreachable, skipping", provider.name)
                continue
            if reading is not None:
                readings.append(reading)
                sources_used.append(provider.name)

        if not readings:
            if cached is not None:
                # Providers found nothing new — the incomplete cached row is
                # still the best honest answer we have (better than nothing),
                # so serve it rather than reporting fully unavailable.
                return EnvironmentResult(available=True, record=cached)
            return EnvironmentResult(
                available=False, message="Data unavailable for this location."
            )

        merged_live = self._merge(readings)

        if cached is not None:
            # Backfill: keep every field the cache already had, fill in only
            # what was missing. Never let a fresh live value overwrite a
            # cached value that was already real — this is purely additive.
            record = dict(cached)
            for field, value in merged_live.items():
                if record.get(field) is None and value is not None:
                    record[field] = value
            existing_sources = record.get("data_source", "")
            new_sources = " + ".join(s for s in sources_used if s not in existing_sources)
            record["data_source"] = " + ".join(filter(None, [existing_sources, new_sources]))
            record["retrieved_at"] = datetime.now(timezone.utc).isoformat()
        else:
            record = {
                "latitude": latitude,
                "longitude": longitude,
                **merged_live,
                "data_source": " + ".join(sources_used),
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
            }

        # A cache-write failure shouldn't hide a successful live lookup from
        # the caller — log it and return the fresh data uncached rather than
        # raising, since Supabase being down doesn't mean the data is wrong.
        try:
            saved = await self._repository.upsert(record)
            return EnvironmentResult(available=True, record=saved)
        except ProviderUnavailableError:
            logger.warning("Could not cache environmental data to Supabase, returning uncached")
            return EnvironmentResult(available=True, record=record)

    @staticmethod
    def _is_incomplete(record: Dict[str, Any]) -> bool:
        """See THE FIX in the module docstring. A cached row is incomplete
        if soil is entirely null, OR vegetation is entirely null — checked
        as two independent categories rather than one flat list, so a row
        with real data in one category still gets the OTHER category
        backfilled instead of being treated as permanently complete."""
        soil_missing = all(record.get(f) is None for f in _SOIL_BACKFILL_FIELDS)
        vegetation_missing = all(record.get(f) is None for f in _VEGETATION_BACKFILL_FIELDS)
        return soil_missing or vegetation_missing

    @staticmethod
    def _missing_fields(record: Dict[str, Any]) -> List[str]:
        return [f for f in _BACKFILL_FIELDS if record.get(f) is None]

    @staticmethod
    def _merge(readings: List[EnvironmentalReading]) -> Dict[str, Any]:
        """Later providers don't overwrite earlier non-null fields — each
        field is taken from the first provider that actually supplied it."""
        merged: Dict[str, Any] = {}
        for reading in readings:
            for field in (
                "soil_ph", "clay", "sand", "organic_carbon",
                "temperature", "rainfall", "ndvi", "ndwi", "land_cover",
            ):
                if merged.get(field) is None:
                    value = getattr(reading, field)
                    if value is not None:
                        merged[field] = value
        return merged