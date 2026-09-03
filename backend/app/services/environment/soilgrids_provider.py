"""
SoilGrids v2.0 REST API client (ISRIC), for soil pH / clay / sand / organic
carbon at a coordinate. https://rest.isric.org/soilgrids/v2.0/docs

STATUS NOTE (check before debugging further): ISRIC has posted that the
SoilGrids REST API is temporarily paused due to ongoing issues, with no
restoration ETA (https://isric.org/explore/soilgrids). If this provider is
returning nothing, check that page first — it's the most likely cause, not
a shape mismatch below. SoilGridsGEEProvider (soilgrids_gee_provider.py)
reads the same underlying SoilGrids v2.0 data directly from Earth Engine
and does not depend on this endpoint; it's listed ahead of this provider
in dependencies.py for that reason. This provider is kept so it silently
resumes contributing if/when the REST service comes back.

Parsing below is defensive: raises ProviderUnavailableError on an
unexpected shape rather than guessing a value.
"""
from typing import Any, Dict, Optional

import httpx

from app.core.config import Settings
from app.core.exceptions import ProviderUnavailableError
from app.core.logging import get_logger
from app.services.environment.base import EnvironmentalReading, EnvironmentDataProvider

logger = get_logger(__name__)

# SoilGrids property -> our field name. phh2o is reported as pH * 10;
# clay/sand as g/kg (i.e. permille, /10 for %); soc (organic carbon) as
# dg/kg (/10 for g/kg). Conversion factors per SoilGrids' documented units.
_PROPERTIES = ["phh2o", "clay", "sand", "soc"]
_DEPTH = "0-5cm"
_DEPTH_TOP, _DEPTH_BOTTOM, _DEPTH_UNIT = 0, 5, "cm"


class SoilGridsProvider(EnvironmentDataProvider):
    name = "SoilGrids"

    def __init__(self, settings: Settings):
        self._base_url = settings.soilgrids_base_url
        self._timeout = settings.environment_provider_timeout_seconds

    async def fetch(self, latitude: float, longitude: float) -> Optional[EnvironmentalReading]:
        params = [("lon", longitude), ("lat", latitude), ("depth", _DEPTH), ("value", "mean")]
        params += [("property", p) for p in _PROPERTIES]

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(self._base_url, params=params)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError as exc:
            raise ProviderUnavailableError(f"SoilGrids failed: {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            raise ProviderUnavailableError("Could not reach SoilGrids API") from exc

        try:
            values = self._extract_means(data)
        except (KeyError, IndexError, TypeError) as exc:
            logger.warning(
                "Unexpected SoilGrids response shape: %s | top-level keys: %s",
                exc,
                list(data.keys()) if isinstance(data, dict) else type(data),
            )
            raise ProviderUnavailableError("Unexpected SoilGrids response shape") from exc

        if not values:
            return None

        return EnvironmentalReading(
            soil_ph=self._safe_div(values.get("phh2o"), 10),
            clay=self._safe_div(values.get("clay"), 10),
            sand=self._safe_div(values.get("sand"), 10),
            organic_carbon=self._safe_div(values.get("soc"), 10),
        )

    @staticmethod
    def _safe_div(value: Optional[float], divisor: float) -> Optional[float]:
        return None if value is None else round(value / divisor, 2)

    @classmethod
    def _matches_target_depth(cls, depth_entry: Dict[str, Any]) -> bool:
        """Match by label first ("0-5cm", tolerant of spacing/case), falling
        back to the structured range object — different client libraries
        and API revisions have been seen to format the label differently,
        but the range fields (top_depth/bottom_depth/unit_depth) are the
        more stable source of truth."""
        label = str(depth_entry.get("label", "")).strip().lower().replace(" ", "")
        if label == _DEPTH.lower():
            return True

        rng = depth_entry.get("range") or {}
        return (
            rng.get("top_depth") == _DEPTH_TOP
            and rng.get("bottom_depth") == _DEPTH_BOTTOM
            and str(rng.get("unit_depth", "")).lower().startswith(_DEPTH_UNIT)
        )

    @classmethod
    def _extract_means(cls, data: Dict[str, Any]) -> Dict[str, Optional[float]]:
        """SoilGrids nests results as properties.layers[].name / depths[].
        values.mean, with each depth entry carrying both a "label" and a
        structured "range". Returns {property_name: mean_value_or_None}."""
        layers = data.get("properties", {}).get("layers", [])
        result: Dict[str, Optional[float]] = {}
        for layer in layers:
            # "name" is the documented field; "code" has shown up as an
            # alternate key in some responses — accept either.
            prop_name = layer.get("name") or layer.get("code")
            if not prop_name:
                continue
            mean = None
            for depth_entry in layer.get("depths", []):
                if cls._matches_target_depth(depth_entry):
                    mean = depth_entry.get("values", {}).get("mean")
                    break
            result[prop_name] = mean
        return result

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(self._base_url, params={"lon": 0, "lat": 0, "property": "phh2o"})
                return resp.status_code == 200
        except httpx.RequestError:
            return False