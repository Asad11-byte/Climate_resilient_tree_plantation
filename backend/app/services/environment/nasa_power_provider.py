"""
NASA POWER climatology API client, for long-term average temperature and
rainfall at a coordinate. https://power.larc.nasa.gov/docs/services/api/

Same caveat as soilgrids_provider.py: not exercised against the live API in
this sandbox (egress restricted). Parsing raises ProviderUnavailableError on
an unexpected shape rather than guessing.
"""
from typing import Any, Dict, Optional

import httpx

from app.core.config import Settings
from app.core.exceptions import ProviderUnavailableError
from app.core.logging import get_logger
from app.services.environment.base import EnvironmentalReading, EnvironmentDataProvider

logger = get_logger(__name__)

# NASA POWER climatology parameters:
#   T2M          = mean air temperature at 2m (°C), annual average key "ANN"
#   PRECTOTCORR  = corrected total precipitation (mm/day), annual average key "ANN"
_PARAMETERS = "T2M,PRECTOTCORR"


class NasaPowerProvider(EnvironmentDataProvider):
    name = "NASA POWER"

    def __init__(self, settings: Settings):
        self._base_url = settings.nasa_power_base_url
        self._timeout = settings.environment_provider_timeout_seconds

    async def fetch(self, latitude: float, longitude: float) -> Optional[EnvironmentalReading]:
        params = {
            "parameters": _PARAMETERS,
            "community": "AG",
            "longitude": longitude,
            "latitude": latitude,
            "format": "JSON",
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(self._base_url, params=params)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError as exc:
            raise ProviderUnavailableError(f"NASA POWER failed: {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            raise ProviderUnavailableError("Could not reach NASA POWER API") from exc

        try:
            temperature, rainfall = self._extract_annual_means(data)
        except (KeyError, TypeError) as exc:
            logger.warning("Unexpected NASA POWER response shape: %s", exc)
            raise ProviderUnavailableError("Unexpected NASA POWER response shape") from exc

        if temperature is None and rainfall is None:
            return None

        return EnvironmentalReading(temperature=temperature, rainfall=rainfall)

    @staticmethod
    def _extract_annual_means(data: Dict[str, Any]):
        parameters = data.get("properties", {}).get("parameter", {})
        t2m = parameters.get("T2M", {})
        precip = parameters.get("PRECTOTCORR", {})
        temperature = t2m.get("ANN")
        rainfall = precip.get("ANN")
        return temperature, rainfall

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    self._base_url,
                    params={"parameters": "T2M", "community": "AG", "longitude": 0, "latitude": 0, "format": "JSON"},
                )
                return resp.status_code == 200
        except httpx.RequestError:
            return False
