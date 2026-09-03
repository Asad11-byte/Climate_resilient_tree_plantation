"""
Shared Google Earth Engine session helper. Both SoilGridsGEEProvider and
SentinelProvider need an authenticated `ee` session; owning that setup here
means auth happens once and both providers stay thin wrappers around it.

Requires, in Settings (see app/core/config.py):
  - gee_service_account_email
  - gee_service_account_key_path (path to the downloaded JSON key file)
    OR gee_service_account_key_json (the key JSON inline, e.g. from a
    secrets manager)

The GEE project tied to that service account must be registered for
non-commercial or commercial Earth Engine use — https://code.earthengine.google.com/register —
or every call below raises ProviderUnavailableError on auth.
"""
import asyncio
import json
import threading
from typing import Optional

import ee

from app.core.config import Settings
from app.core.exceptions import ProviderUnavailableError
from app.core.logging import get_logger

logger = get_logger(__name__)

_init_lock = threading.Lock()
_initialized = False


def _initialize_sync(settings: Settings) -> None:
    global _initialized
    if _initialized:
        return
    with _init_lock:
        if _initialized:
            return
        email = getattr(settings, "gee_service_account_email", None)
        key_path = getattr(settings, "gee_service_account_key_path", None)
        key_json = getattr(settings, "gee_service_account_key_json", None)
        if not email or not (key_path or key_json):
            raise ProviderUnavailableError(
                "GEE_SERVICE_ACCOUNT_EMAIL and a service account key "
                "(GEE_SERVICE_ACCOUNT_KEY_PATH or _KEY_JSON) must be set"
            )
        try:
            if key_json:
                # Round-trip through json to fail fast on malformed input
                # rather than passing a bad string into ee.
                json.loads(key_json)
                credentials = ee.ServiceAccountCredentials(email, key_data=key_json)
            else:
                credentials = ee.ServiceAccountCredentials(email, key_path)
            ee.Initialize(credentials)
        except Exception as exc:  # ee raises plain Exception/EEException on auth failure
            raise ProviderUnavailableError(f"Earth Engine auth failed: {exc}") from exc
        _initialized = True
        logger.info("Earth Engine session initialized for %s", email)


async def ensure_initialized(settings: Settings) -> None:
    """Call before any `ee.*` usage. Cheap no-op once already initialized."""
    await asyncio.to_thread(_initialize_sync, settings)


async def health_check(settings: Settings) -> bool:
    try:
        await ensure_initialized(settings)
        await asyncio.to_thread(lambda: ee.Number(1).getInfo())
        return True
    except Exception:
        return False