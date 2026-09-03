from typing import Any, Dict, List, Optional

from app.repositories.base import SupabaseRepository


class SpeciesRepository(SupabaseRepository):
    table_name = "tree_species"

    async def list_all(self) -> List[Dict[str, Any]]:
        result = self._table().select("*").execute()
        return result.data or []

    async def get_by_id(self, species_id: str) -> Optional[Dict[str, Any]]:
        result = self._table().select("*").eq("id", species_id).limit(1).execute()
        rows = result.data or []
        return rows[0] if rows else None

    async def create(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Used by the seeding script, not the public API. Callers must not
        invent field values — leave unknown fields absent/None."""
        result = self._table().insert(record).execute()
        return result.data[0]
