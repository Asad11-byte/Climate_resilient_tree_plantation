
"""
Authentication dependency for Supabase JWTs.

Supports Supabase asymmetric JWT signing (ES256/RS256) by verifying the
access token against the project's JWKS endpoint.

Authorization header:
    Authorization: Bearer <supabase-access-token>

The JWT's `kid` identifies the correct public signing key.
"""

from dataclasses import dataclass
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from app.core.config import get_settings

_bearer_scheme = HTTPBearer(auto_error=False)

settings = get_settings()

# Supabase exposes the public keys used to verify asymmetric JWTs.
JWKS_URL = (
    f"{settings.supabase_url.rstrip('/')}"
    "/auth/v1/.well-known/jwks.json"
)

_jwk_client = PyJWKClient(JWKS_URL)


@dataclass
class CurrentUser:
    user_id: str
    email: Optional[str] = None


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> CurrentUser:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    token = credentials.credentials

    try:
        # Read the token header and obtain the public key matching its `kid`.
        signing_key = _jwk_client.get_signing_key_from_jwt(token)

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256", "RS256"],
            audience="authenticated",
            issuer=f"{settings.supabase_url.rstrip('/')}/auth/v1",
        )

    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        ) from exc

    except jwt.InvalidAudienceError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token audience",
        ) from exc

    except jwt.InvalidIssuerError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token issuer",
        ) from exc

    except jwt.PyJWKClientError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not obtain Supabase signing key",
        ) from exc

    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from exc

    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject claim",
        )

    return CurrentUser(
        user_id=user_id,
        email=payload.get("email"),
    )

