"""
Thin Supabase client wrapper. Repositories use this for table access.
No business rules belong here — just connection + generic helpers.
"""
from supabase import Client, create_client

from app.core.config import Settings
from app.core.exceptions import ProviderUnavailableError


def build_supabase_client(settings: Settings) -> Client:
    if not settings.supabase_url or not settings.supabase_key:
        raise ProviderUnavailableError("SUPABASE_URL and SUPABASE_KEY must be set")
    try:
        return create_client(settings.supabase_url, settings.supabase_key)
    except Exception as exc:  # noqa: BLE001
        raise ProviderUnavailableError("Could not create Supabase client") from exc


class SupabaseRepository:
    """Base class for table-specific repositories."""

    table_name: str = ""

    def __init__(self, client: Client):
        if not self.table_name:
            raise NotImplementedError("Subclasses must set table_name")
        self._client = client

    def _table(self):
        return self._client.table(self.table_name)

    async def health_check(self) -> bool:
        try:
            self._table().select("*").limit(1).execute()
            return True
        except Exception:  # noqa: BLE001
            return False
