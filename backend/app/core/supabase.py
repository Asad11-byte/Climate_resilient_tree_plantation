"""
Supabase client for chat session/message persistence.

Only app/repositories/chat_repository.py should import this — nothing else
in the app should reach into Supabase directly, same rule as
app/core/config.py: one source of truth, one entry point.

Requires the `supabase` package: pip install supabase
"""
from functools import lru_cache

from supabase import Client, create_client

from app.core.config import get_settings


@lru_cache
def get_supabase_client() -> Client:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_KEY must be set to use chat session storage."
        )
    # Use the service_role key here, not the anon key, unless you've written
    # RLS policies that allow the backend's inserts/updates/deletes on
    # chat_sessions and chat_messages. The anon key is subject to RLS like
    # any other client.
    return create_client(settings.supabase_url, settings.supabase_key)