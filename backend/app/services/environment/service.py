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
_BACKFILL_FIELDS / _is_incomplete below.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger
from app.core.exceptions import ProviderUnavailableError
from app.repositories.environmental_repository import EnvironmentalRepository
from app.services.environment.base import EnvironmentalReading, EnvironmentDataProvider

logger = get_logger(__name__)

# Fields worth re-querying live providers for if a cached row is missing
# them. Deliberately excludes temperature/rainfall — NASA POWER has
# near-complete global coverage, so a null there usually means a genuine
# gap, not a provider that was broken at cache-write time.
_BACKFILL_FIELDS = (
    "soil_ph", "clay", "sand", "organic_carbon", "ndvi", "ndwi", "land_cover",
)


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
        """A cached row counts as incomplete if it's missing every
        backfill-worthy field — i.e. it looks like it was written before any
        soil/vegetation provider worked for this area, rather than a
        genuine "no data here" result that happened to leave some fields
        null. Requiring ALL of them null (not just one) avoids re-querying
        every request for a row that's legitimately missing just NDVI due
        to cloud cover, say."""
        return all(record.get(field) is None for field in _BACKFILL_FIELDS)

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