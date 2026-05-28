"""API-key authentication (prototype-grade).

If ``TERRASHIELD_API_KEYS`` is empty the API is OPEN — intended for local
development and the test suite. Set it in production (a comma-separated list,
stored in Secret Manager) to require a matching ``X-API-Key`` request header.

This is a prototype control: it blocks anonymous internet abuse and gives a
per-key throttle handle. A browser frontend that ships the key in its bundle
does not keep it secret from a determined user — rotate keys and pair with the
per-key rate limit accordingly.
"""
from __future__ import annotations

import secrets

from fastapi import Header, HTTPException, status

from .config import Settings


def make_api_key_auth(settings: Settings):
    keys = settings.api_key_set

    def dependency(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> str | None:
        if not keys:  # open mode — no keys configured (dev / tests)
            return None
        # constant-time compare against each accepted key
        if x_api_key and any(secrets.compare_digest(x_api_key, k) for k in keys):
            return x_api_key
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid API key.",
            headers={"WWW-Authenticate": "API-Key"},
        )

    return dependency
