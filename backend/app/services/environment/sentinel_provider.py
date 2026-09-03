"""
Sentinel-2 NDVI/NDWI + ESA WorldCover land cover for a point, via Earth
Engine. Populates the three EnvironmentalReading fields no other provider
fills: ndvi, ndwi, land_cover.
"""
import asyncio
import datetime as dt
from typing import Optional

import ee

from app.core.config import Settings
from app.core.exceptions import ProviderUnavailableError
from app.core.logging import get_logger
from app.services.environment import gee_client
from app.services.environment.base import EnvironmentalReading, EnvironmentDataProvider

logger = get_logger(__name__)

_LOOKBACK_DAYS = 90
_MAX_CLOUD_PERCENT = 20
_BUFFER_METERS = 500

_WORLDCOVER_LABELS = {
    10: "Tree cover", 20: "Shrubland", 30: "Grassland", 40: "Cropland",
    50: "Built-up", 60: "Bare / sparse vegetation", 70: "Snow and ice",
    80: "Permanent water bodies", 90: "Herbaceous wetland",
    95: "Mangroves", 100: "Moss and lichen",
}


class SentinelProvider(EnvironmentDataProvider):
    name = "Sentinel-2"

    def __init__(self, settings: Settings):
        self._settings = settings

    async def fetch(self, latitude: float, longitude: float) -> Optional[EnvironmentalReading]:
        await gee_client.ensure_initialized(self._settings)
        try:
            values = await asyncio.to_thread(self._sample_sync, latitude, longitude)
        except ProviderUnavailableError:
            raise
        except Exception as exc:
            raise ProviderUnavailableError(f"Earth Engine Sentinel-2 query failed: {exc}") from exc

        if values is None:
            # No cloud-free image in the lookback window — legitimate "no
            # data", not a failure.
            return None

        return EnvironmentalReading(
            ndvi=values.get("ndvi"),
            ndwi=values.get("ndwi"),
            land_cover=values.get("land_cover"),
        )

    def _sample_sync(self, latitude: float, longitude: float) -> Optional[dict]:
        point = ee.Geometry.Point([longitude, latitude])
        region = point.buffer(_BUFFER_METERS)

        end = ee.Date(dt.datetime.utcnow().isoformat())
        start = end.advance(-_LOOKBACK_DAYS, "day")

        collection = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(region)
            .filterDate(start, end)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", _MAX_CLOUD_PERCENT))
            .sort("system:time_start", False)  # most recent first
        )

        if collection.size().getInfo() == 0:
            return None

        image = collection.first()
        nir, red, green = image.select("B8"), image.select("B4"), image.select("B3")
        ndvi = nir.subtract(red).divide(nir.add(red)).rename("ndvi")
        ndwi = green.subtract(nir).divide(green.add(nir)).rename("ndwi")

        index_stats = (
            ee.Image.cat([ndvi, ndwi])
            .reduceRegion(reducer=ee.Reducer.mean(), geometry=region, scale=10, maxPixels=1e8)
            .getInfo()
        )

        worldcover = ee.ImageCollection("ESA/WorldCover/v200").first()
        cover_code = (
            worldcover.reduceRegion(reducer=ee.Reducer.mode(), geometry=region, scale=10, maxPixels=1e8)
            .getInfo()
            .get("Map")
        )

        if index_stats.get("ndvi") is None and index_stats.get("ndwi") is None and cover_code is None:
            return None

        return {
            "ndvi": round(index_stats["ndvi"], 4) if index_stats.get("ndvi") is not None else None,
            "ndwi": round(index_stats["ndwi"], 4) if index_stats.get("ndwi") is not None else None,
            "land_cover": (
                _WORLDCOVER_LABELS.get(cover_code, f"Unknown ({cover_code})")
                if cover_code is not None
                else None
            ),
        }

    async def health_check(self) -> bool:
        return await gee_client.health_check(self._settings)