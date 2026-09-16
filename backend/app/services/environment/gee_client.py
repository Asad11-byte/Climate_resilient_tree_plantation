"""
Shared Google Earth Engine client/session helper.

Supports two authentication modes:

LOCAL DEVELOPMENT
    GEE_SERVICE_ACCOUNT_EMAIL
    GEE_SERVICE_ACCOUNT_KEY_PATH=./secrets/gee-key.json

VERCEL / PRODUCTION
    GEE_SERVICE_ACCOUNT_KEY_JSON=<entire service-account JSON>

The JSON-based production configuration is preferred because Vercel
does not have access to the local secrets/gee-key.json file.

FALLBACK BEHAVIOR: if GEE_SERVICE_ACCOUNT_KEY_JSON is set but invalid or
incomplete (empty, malformed JSON, missing required fields — e.g. a
leftover/placeholder value from setting up the Vercel deployment while
still developing locally), this falls back to GEE_SERVICE_ACCOUNT_KEY_PATH
instead of failing outright, PROVIDED a key path is actually configured.
This is deliberate: a broken JSON env var should not silently break local
development just because both variables happen to be present in .env at
once. Which source actually succeeded is logged at INFO level either way,
so this is diagnosable without reading this file's source.

Both SoilGridsGEEProvider and SentinelProvider can call
ensure_initialized() before using ee.* APIs.
"""

import asyncio
import json
import threading
from pathlib import Path
from typing import Any, Dict, Optional

import ee

from app.core.config import Settings
from app.core.exceptions import ProviderUnavailableError
from app.core.logging import get_logger


logger = get_logger(__name__)

# Prevent multiple concurrent initialization attempts.
_init_lock = threading.Lock()

# Process-level initialization state.
_initialized = False
_initialized_via: Optional[str] = None  # "key_json" | "key_path" — for diagnostics only


def _load_key_json(key_json: str) -> Dict[str, Any]:
    """
    Parse the inline Google service-account JSON.

    Raises:
        ProviderUnavailableError: If the JSON is missing or invalid.
    """
    if not key_json or not key_json.strip():
        raise ProviderUnavailableError(
            "GEE_SERVICE_ACCOUNT_KEY_JSON is empty"
        )

    try:
        data = json.loads(key_json)
    except json.JSONDecodeError as exc:
        raise ProviderUnavailableError(
            "GEE_SERVICE_ACCOUNT_KEY_JSON is not valid JSON"
        ) from exc

    if not isinstance(data, dict):
        raise ProviderUnavailableError(
            "GEE_SERVICE_ACCOUNT_KEY_JSON must contain a JSON object"
        )

    required_fields = (
        "client_email",
        "private_key",
    )

    missing = [
        field for field in required_fields
        if not data.get(field)
    ]

    if missing:
        raise ProviderUnavailableError(
            "GEE service-account JSON is missing required field(s): "
            + ", ".join(missing)
        )

    return data


def _load_key_file(key_path: str) -> Dict[str, Any]:
    """
    Load the service-account JSON from a local file.

    This is primarily intended for local development.
    """
    if not key_path or not key_path.strip():
        raise ProviderUnavailableError(
            "GEE_SERVICE_ACCOUNT_KEY_PATH is empty"
        )

    path = Path(key_path)

    if not path.exists():
        raise ProviderUnavailableError(
            f"GEE service-account key file not found: {path}"
        )

    if not path.is_file():
        raise ProviderUnavailableError(
            f"GEE service-account key path is not a file: {path}"
        )

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        raise ProviderUnavailableError(
            f"GEE service-account key file contains invalid JSON: {path}"
        ) from exc
    except OSError as exc:
        raise ProviderUnavailableError(
            f"Could not read GEE service-account key file: {path}"
        ) from exc

    if not isinstance(data, dict):
        raise ProviderUnavailableError(
            "GEE service-account key file must contain a JSON object"
        )

    required_fields = (
        "client_email",
        "private_key",
    )

    missing = [
        field for field in required_fields
        if not data.get(field)
    ]

    if missing:
        raise ProviderUnavailableError(
            "GEE service-account JSON is missing required field(s): "
            + ", ".join(missing)
        )

    return data


def _get_credentials(
    settings: Settings,
) -> tuple[ee.ServiceAccountCredentials, str, Optional[str], str]:
    """
    Build Earth Engine service-account credentials.

    Priority:

    1. GEE_SERVICE_ACCOUNT_KEY_JSON — tried first if present at all.
    2. GEE_SERVICE_ACCOUNT_KEY_PATH — tried if (1) wasn't configured, OR
       if (1) was configured but failed validation (see module docstring
       for why this falls back instead of raising immediately).

    The email is extracted from the JSON when possible, so production
    does not need a separate GEE_SERVICE_ACCOUNT_EMAIL variable.

    Returns (credentials, email, project_id, source_label) — source_label
    is "key_json" or "key_path", logged by the caller for diagnostics.
    """

    key_json = getattr(
        settings,
        "gee_service_account_key_json",
        None,
    )

    key_path = getattr(
        settings,
        "gee_service_account_key_path",
        None,
    )

    configured_email = getattr(
        settings,
        "gee_service_account_email",
        None,
    )

    key_json_error: Optional[Exception] = None

    # ---------------------------------------------------------
    # Production / Vercel — tried first if configured at all
    # ---------------------------------------------------------
    if key_json:
        try:
            key_data = _load_key_json(key_json)

            email = key_data.get("client_email")
            if not email:
                raise ProviderUnavailableError(
                    "client_email missing from GEE_SERVICE_ACCOUNT_KEY_JSON"
                )

            credentials = ee.ServiceAccountCredentials(
                email,
                key_data=key_json,
            )

            project_id = key_data.get("project_id")

            return credentials, email, project_id, "key_json"

        except ProviderUnavailableError as exc:
            # Don't raise yet — remember this and try key_path next, if
            # one is configured. This is the actual fix: previously an
            # invalid/leftover KEY_JSON value would break local dev even
            # when a perfectly valid KEY_PATH was also present, because
            # this branch raised immediately instead of falling through.
            key_json_error = exc
            logger.warning(
                "GEE_SERVICE_ACCOUNT_KEY_JSON was set but invalid (%s) — "
                "falling back to GEE_SERVICE_ACCOUNT_KEY_PATH if configured",
                exc,
            )

    # ---------------------------------------------------------
    # Local development — also the fallback if key_json was
    # present but broken
    # ---------------------------------------------------------
    if key_path:
        key_data = _load_key_file(key_path)

        email = (
            key_data.get("client_email")
            or configured_email
        )

        if not email:
            raise ProviderUnavailableError(
                "client_email missing from GEE key file and "
                "GEE_SERVICE_ACCOUNT_EMAIL is not configured"
            )

        credentials = ee.ServiceAccountCredentials(
            email,
            key_path,
        )

        project_id = key_data.get("project_id")

        return credentials, email, project_id, "key_path"

    # Neither worked. If key_json was configured but invalid, surface
    # that specific error rather than the generic "nothing configured"
    # message — it's more actionable (you HAVE credentials, they're wrong,
    # vs. you have none at all).
    if key_json_error is not None:
        raise key_json_error

    raise ProviderUnavailableError(
        "No Google Earth Engine service-account credentials configured. "
        "Set GEE_SERVICE_ACCOUNT_KEY_JSON for production/Vercel or "
        "GEE_SERVICE_ACCOUNT_KEY_PATH for local development."
    )


def _initialize_sync(settings: Settings) -> None:
    """
    Synchronous Earth Engine initialization.

    Called through asyncio.to_thread() so initialization does not block
    the FastAPI event loop.
    """
    global _initialized, _initialized_via

    if _initialized:
        return

    with _init_lock:
        if _initialized:
            return

        try:
            credentials, email, project_id, source = _get_credentials(settings)

            # Prefer the project from the service-account JSON.
            #
            # If your Settings class later defines a dedicated
            # gee_project_id, it can override the JSON project_id.
            configured_project_id = getattr(
                settings,
                "gee_project_id",
                None,
            )

            project = configured_project_id or project_id

            if project:
                ee.Initialize(
                    credentials,
                    project=project,
                )
            else:
                ee.Initialize(credentials)

        except ProviderUnavailableError:
            raise

        except Exception as exc:
            logger.exception(
                "Google Earth Engine initialization failed"
            )

            raise ProviderUnavailableError(
                f"Earth Engine authentication failed: {exc}"
            ) from exc

        _initialized = True
        _initialized_via = source

        logger.info(
            "Earth Engine session initialized for %s (credentials source: %s)",
            email,
            source,
        )


async def ensure_initialized(settings: Settings) -> None:
    """
    Ensure Earth Engine is initialized.

    Safe to call repeatedly. After the first successful initialization,
    subsequent calls are effectively no-ops.
    """
    await asyncio.to_thread(
        _initialize_sync,
        settings,
    )


async def health_check(settings: Settings) -> bool:
    """
    Check whether Earth Engine authentication and API access work.

    Returns:
        True  -> GEE is initialized and responding.
        False -> authentication/API check failed.
    """
    try:
        await ensure_initialized(settings)

        await asyncio.to_thread(
            lambda: ee.Number(1).getInfo()
        )

        return True

    except Exception:
        logger.exception(
            "Google Earth Engine health check failed"
        )
        return False


def reset_initialization() -> None:
    """
    Reset the process-level initialization state.

    Primarily useful for tests.

    Do not normally call this during application runtime.
    """
    global _initialized, _initialized_via

    with _init_lock:
        _initialized = False
        _initialized_via = None