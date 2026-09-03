"""
Domain-level exceptions. Services raise these; api/ routers translate them
into HTTP responses. This keeps services free of any FastAPI/HTTP concerns.
"""


class AppError(Exception):
    """Base class for all domain errors."""


class ProviderUnavailableError(AppError):
    """An external provider (Groq, Jina, Qdrant, Supabase, env-data API) is unreachable
    or returned an error. Callers should surface a safe, non-leaking message."""


class InsufficientEvidenceError(AppError):
    """Retrieval found no relevant evidence for the query. This is not a bug —
    the caller should return an honest 'evidence unavailable' response, never
    let the LLM fill the gap with invented facts."""


class InvalidLocationError(AppError):
    """Coordinates are missing, malformed, or outside the supported region."""


class NotFoundError(AppError):
    """Requested resource (species, document, session) does not exist."""
