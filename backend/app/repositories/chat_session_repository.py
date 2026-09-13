from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.repositories.base import SupabaseRepository

TITLE_MAX_LENGTH = 60


def truncate_title(text: str) -> str:
    """Turn a first user message into a short session title."""
    text = " ".join(text.strip().split())
    if len(text) <= TITLE_MAX_LENGTH:
        return text
    return text[: TITLE_MAX_LENGTH - 1].rstrip() + "…"


class ChatSessionRepository(SupabaseRepository):
    table_name = "chat_sessions"

    async def list_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        result = (
            self._table()
            .select("*")
            .eq("user_id", user_id)
            .order("updated_at", desc=True)
            .execute()
        )
        return result.data or []

    async def create(self, user_id: str) -> Dict[str, Any]:
        result = self._table().insert({"user_id": user_id}).execute()
        return result.data[0]

    async def get_for_user(self, session_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Scoped by user_id, not just id. The connection uses the
        service_role key (bypasses RLS), so this explicit filter — not the
        database — is what actually stops one user from reading, renaming,
        or deleting another user's session."""
        result = (
            self._table()
            .select("*")
            .eq("id", session_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        rows = result.data or []
        return rows[0] if rows else None

    async def rename(self, session_id: str, user_id: str, title: str) -> Optional[Dict[str, Any]]:
        result = (
            self._table()
            .update({"title": title, "updated_at": datetime.now(timezone.utc).isoformat()})
            .eq("id", session_id)
            .eq("user_id", user_id)
            .execute()
        )
        rows = result.data or []
        return rows[0] if rows else None

    async def touch(self, session_id: str, user_id: str, title: Optional[str] = None) -> None:
        """Bump updated_at every turn (for recency ordering), and set the
        title too if one was just computed for a previously-untitled session."""
        payload: Dict[str, Any] = {"updated_at": datetime.now(timezone.utc).isoformat()}
        if title:
            payload["title"] = title
        self._table().update(payload).eq("id", session_id).eq("user_id", user_id).execute()

    async def delete(self, session_id: str, user_id: str) -> None:
        # chat_messages.session_id has `on delete cascade`, so messages are
        # cleaned up automatically.
        self._table().delete().eq("id", session_id).eq("user_id", user_id).execute()