import math
from typing import Any, Dict, List, Optional

from app.repositories.base import SupabaseRepository

# Roughly 0.05 degrees is a few km — generous enough to match a cached
# lookup for "near this point" without pretending resolution we don't have.
DEFAULT_TOLERANCE_DEGREES = 0.05


def _distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    return math.sqrt((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2)


class EnvironmentalRepository(SupabaseRepository):
    table_name = "environmental_data"

    async def find_near(
        self, latitude: float, longitude: float, tolerance: float = DEFAULT_TOLERANCE_DEGREES
    ) -> Optional[Dict[str, Any]]:
        """Returns the closest cached record within `tolerance` degrees, or
        None if nothing is cached nearby. Never interpolates or estimates a
        value that isn't in the table — a miss means "data unavailable",
        full stop, until Phase 5 wires up a live provider to backfill it."""
        result = (
            self._table()
            .select("*")
            .gte("latitude", latitude - tolerance)
            .lte("latitude", latitude + tolerance)
            .gte("longitude", longitude - tolerance)
            .lte("longitude", longitude + tolerance)
            .execute()
        )
        rows: List[Dict[str, Any]] = result.data or []
        if not rows:
            return None

        return min(
            rows,
            key=lambda r: _distance(latitude, longitude, r["latitude"], r["longitude"]),
        )

    async def upsert(self, record: Dict[str, Any]) -> Dict[str, Any]:
        result = self._table().upsert(record).execute()
        return result.data[0]
