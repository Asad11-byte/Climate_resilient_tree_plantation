"""
Interface for live environmental-data lookups (SoilGrids, NASA POWER, etc.).

Distinct from services/environment being empty scaffolding in earlier
phases — this is now real. `fetch()` returning None means "this provider
has no data for this coordinate" (a legitimate, non-error outcome); raising
ProviderUnavailableError means "the provider itself couldn't be reached" —
callers treat these differently (None is fine to combine with other
providers' results, a raise should be logged and the provider skipped).
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class EnvironmentalReading:
    soil_ph: Optional[float] = None
    clay: Optional[float] = None
    sand: Optional[float] = None
    organic_carbon: Optional[float] = None
    temperature: Optional[float] = None
    rainfall: Optional[float] = None
    ndvi: Optional[float] = None
    ndwi: Optional[float] = None
    land_cover: Optional[str] = None


class EnvironmentDataProvider(ABC):
    name: str = "unknown"

    @abstractmethod
    async def fetch(self, latitude: float, longitude: float) -> Optional[EnvironmentalReading]:
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> bool:
        raise NotImplementedError
