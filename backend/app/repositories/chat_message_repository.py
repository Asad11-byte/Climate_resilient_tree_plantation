from typing import Any, Dict, List, Optional

from app.repositories.base import SupabaseRepository


class ChatMessageRepository(SupabaseRepository):
    table_name = "chat_messages"

    async def list_for_session(self, session_id: str) -> List[Dict[str, Any]]:
        """No user_id filter here — chat_messages doesn't have that column.
        Callers must verify the caller owns `session_id` (via
        ChatSessionRepository.get_for_user) before calling this."""
        result = (
            self._table()
            .select("*")
            .eq("session_id", session_id)
            .order("created_at")
            .execute()
        )
        return result.data or []

    async def save(
        self,
        session_id: str,
        role: str,
        content: str,
        query_category: Optional[str] = None,
        evidence_available: Optional[bool] = None,
        sources: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        payload = {
            "session_id": session_id,
            "role": role,
            "content": content,
            "query_category": query_category,
            "evidence_available": evidence_available,
            "sources": sources,
        }
        result = self._table().insert(payload).execute()
        return result.data[0]