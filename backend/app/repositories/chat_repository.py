"""
Data access for chat_sessions / chat_messages.

Plain functions, not a class — there's no state to hold beyond the cached
Supabase client, so a class would just be ceremony. Called directly from
app/api/chat.py and app/api/sessions.py (no DI indirection needed, since
get_supabase_client() is already cached and cheap to call).

Note: the `supabase-py` client used here (create_client) is synchronous.
These functions are plain `def`, not `async def` — call them normally
(no `await`) from your async route handlers. For a low-traffic app this is
fine; if request volume grows, wrap calls in
`starlette.concurrency.run_in_threadpool` to avoid blocking the event loop.
"""
from datetime import datetime, timezone
from typing import Any, Optional

from app.core.supabase import get_supabase_client

SESSIONS_TABLE = "chat_sessions"
MESSAGES_TABLE = "chat_messages"

TITLE_MAX_LENGTH = 60


def truncate_title(text: str) -> str:
    """Turn a first user message into a short session title."""
    text = " ".join(text.strip().split())
    if len(text) <= TITLE_MAX_LENGTH:
        return text
    return text[: TITLE_MAX_LENGTH - 1].rstrip() + "…"


def list_sessions(user_id: Optional[str] = None) -> list[dict]:
    client = get_supabase_client()
    query = client.table(SESSIONS_TABLE).select("*").order("updated_at", desc=True)
    if user_id:
        query = query.eq("user_id", user_id)
    response = query.execute()
    return response.data or []


def create_session(user_id: Optional[str] = None) -> dict:
    client = get_supabase_client()
    payload: dict[str, Any] = {"user_id": user_id} if user_id else {}
    response = client.table(SESSIONS_TABLE).insert(payload).execute()
    return response.data[0]


def get_session(session_id: str) -> Optional[dict]:
    client = get_supabase_client()
    response = client.table(SESSIONS_TABLE).select("*").eq("id", session_id).limit(1).execute()
    return response.data[0] if response.data else None


def rename_session(session_id: str, title: str) -> dict:
    client = get_supabase_client()
    response = (
        client.table(SESSIONS_TABLE)
        .update({"title": title, "updated_at": datetime.now(timezone.utc).isoformat()})
        .eq("id", session_id)
        .execute()
    )
    return response.data[0]


def touch_session(session_id: str, title: Optional[str] = None) -> None:
    """Bump updated_at (so recency ordering/grouping stays correct), and set
    the title too if one was just computed for a previously-untitled session."""
    client = get_supabase_client()
    payload: dict[str, Any] = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if title:
        payload["title"] = title
    client.table(SESSIONS_TABLE).update(payload).eq("id", session_id).execute()


def delete_session(session_id: str) -> None:
    client = get_supabase_client()
    # chat_messages.session_id has `on delete cascade`, so messages are
    # cleaned up automatically.
    client.table(SESSIONS_TABLE).delete().eq("id", session_id).execute()


def list_messages(session_id: str) -> list[dict]:
    client = get_supabase_client()
    response = (
        client.table(MESSAGES_TABLE)
        .select("*")
        .eq("session_id", session_id)
        .order("created_at")
        .execute()
    )
    return response.data or []


def save_message(
    session_id: str,
    role: str,
    content: str,
    query_category: Optional[str] = None,
    evidence_available: Optional[bool] = None,
    sources: Optional[list[dict]] = None,
) -> dict:
    client = get_supabase_client()
    payload = {
        "session_id": session_id,
        "role": role,
        "content": content,
        "query_category": query_category,
        "evidence_available": evidence_available,
        "sources": sources,
    }
    response = client.table(MESSAGES_TABLE).insert(payload).execute()
    return response.data[0]