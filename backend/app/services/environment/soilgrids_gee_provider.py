"""
Soil properties (pH, clay, sand, organic carbon), read from Earth Engine.

Primary source: ISRIC's own SoilGrids v2.0 assets
(projects/soilgrids-isric/{phh2o,clay,sand,soc}_mean). These have been
observed to return empty/masked pixels at multiple real-world points
(confirmed at Mandi Bahauddin and Amsterdam, across several sampling
strategies) despite valid band metadata — the asset itself appears to have
gaps or has been re-permissioned since the tutorials referencing it were
written. We still try it first since it's the actual SoilGrids v2.0 model
when it does return data.

Fallback source: OpenLandMap (same research lineage — Hengl/OpenGeoHub,
predecessor to SoilGrids — but a DIFFERENT model, not identical
predictions). Officially catalogued in Earth Engine, confirmed non-empty.
Used per-field, only for whichever fields the primary source didn't
return, so a location that has one gap doesn't discard fields that DID
come back real.

IMPORTANT — unit conventions differ between the two sources:
  - phh2o: both report pH * 10          -> divide by 10 either way
  - clay/sand: SoilGrids reports g/kg   -> divide by 10 for %
               OpenLandMap reports % directly -> NO division
  - soc: SoilGrids reports dg/kg        -> divide by 10 for g/kg
         OpenLandMap's scale factor (5 * 0.001 -> kg/kg, per its own
         processing docs) means raw value * 5 -> g/kg
Mixing these up would silently produce wrong values, which is exactly
what this system is built to avoid — see the per-source conversion
functions below rather than a single shared divisor.
"""
import asyncio
from typing import Dict, Optional

import ee  # type: ignore

from app.core.config import Settings
from app.core.exceptions import ProviderUnavailableError
from app.core.logging import get_logger
from app.services.environment import gee_client
from app.services.environment.base import EnvironmentalReading, EnvironmentDataProvider

logger = get_logger(__name__)

_DEPTH_BAND_SUFFIX = "0-5cm_mean"
_PRIMARY_ASSETS = {
    "phh2o": "projects/soilgrids-isric/phh2o_mean",
    "clay": "projects/soilgrids-isric/clay_mean",
    "sand": "projects/soilgrids-isric/sand_mean",
    "soc": "projects/soilgrids-isric/soc_mean",
}
_FALLBACK_ASSETS = {
    "phh2o": "OpenLandMap/SOL/SOL_PH-H2O_USDA-4C1A2A_M/v02",
    "clay": "OpenLandMap/SOL/SOL_CLAY-WFRACTION_USDA-3A1A1A_M/v02",
    "sand": "OpenLandMap/SOL/SOL_SAND-WFRACTION_USDA-3A1A1A_M/v02",
    "soc": "OpenLandMap/SOL/SOL_ORGANIC-CARBON_USDA-6A1C_M/v02",
}
_FALLBACK_BAND = "b0"  # OpenLandMap's 0cm-depth band, all four datasets

_PRIMARY_BUFFERS_METERS = [250, 1000]  # widen once before giving up on primary
_FALLBACK_BUFFER_METERS = 250


class SoilGridsGEEProvider(EnvironmentDataProvider):
    name = "SoilGrids (Earth Engine, with OpenLandMap fallback)"

    def __init__(self, settings: Settings):
        self._settings = settings

    async def fetch(self, latitude: float, longitude: float) -> Optional[EnvironmentalReading]:
        await gee_client.ensure_initialized(self._settings)
        try:
            values, sources = await asyncio.to_thread(self._sample_sync, latitude, longitude)
        except ProviderUnavailableError:
            raise
        except Exception as exc:
            raise ProviderUnavailableError(f"Earth Engine soil query failed: {exc}") from exc

        if not values:
            return None

        logger.info("Soil data sources used for (%s, %s): %s", latitude, longitude, sources)

        return EnvironmentalReading(
            soil_ph=self._convert("phh2o", values.get("phh2o"), sources.get("phh2o")),
            clay=self._convert("clay", values.get("clay"), sources.get("clay")),
            sand=self._convert("sand", values.get("sand"), sources.get("sand")),
            organic_carbon=self._convert("soc", values.get("soc"), sources.get("soc")),
        )

    def _sample_sync(self, latitude: float, longitude: float) -> tuple[Dict[str, Optional[float]], Dict[str, str]]:
        point = ee.Geometry.Point([longitude, latitude])
        values: Dict[str, Optional[float]] = {}
        sources: Dict[str, str] = {}

        # --- Primary: SoilGrids, widening the buffer once before giving up ---
        for buffer_m in _PRIMARY_BUFFERS_METERS:
            missing = [p for p in _PRIMARY_ASSETS if values.get(p) is None]
            if not missing:
                break
            region = point.buffer(buffer_m)
            image = ee.Image.cat(
                [
                    ee.Image(_PRIMARY_ASSETS[p]).select(f"{p}_{_DEPTH_BAND_SUFFIX}").rename(p)
                    for p in missing
                ]
            )
            result = image.reduceRegion(
                reducer=ee.Reducer.mean(), geometry=region, scale=250, maxPixels=1e8
            ).getInfo()
            for prop, val in (result or {}).items():
                if val is not None:
                    values[prop] = val
                    sources[prop] = f"SoilGrids (Earth Engine, {buffer_m}m)"

        # --- Fallback: OpenLandMap, per still-missing field ---
        missing = [p for p in _PRIMARY_ASSETS if values.get(p) is None]
        if missing:
            region = point.buffer(_FALLBACK_BUFFER_METERS)
            image = ee.Image.cat(
                [
                    ee.Image(_FALLBACK_ASSETS[p]).select(_FALLBACK_BAND).rename(p)
                    for p in missing
                ]
            )
            result = image.reduceRegion(
                reducer=ee.Reducer.mean(), geometry=region, scale=250, maxPixels=1e8
            ).getInfo()
            for prop, val in (result or {}).items():
                if val is not None:
                    values[prop] = val
                    sources[prop] = "OpenLandMap"

        if not values:
            return {}, {}
        return values, sources

    @staticmethod
    def _convert(prop: str, raw: Optional[float], source: Optional[str]) -> Optional[float]:
        """Applies the correct conversion for whichever source actually
        supplied this field — SoilGrids and OpenLandMap use different unit
        conventions for clay/sand/soc (see module docstring)."""
        if raw is None:
            return None

        is_openlandmap = source == "OpenLandMap"

        if prop == "phh2o":
            return round(raw / 10, 2)  # pH*10 -> pH, same convention both sources
        if prop in ("clay", "sand"):
            return round(raw, 2) if is_openlandmap else round(raw / 10, 2)
        if prop == "soc":
            return round(raw * 5, 2) if is_openlandmap else round(raw / 10, 2)
        return None

    async def health_check(self) -> bool:
        return await gee_client.health_check(self._settings)