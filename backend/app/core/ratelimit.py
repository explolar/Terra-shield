"""Lightweight per-key token-bucket rate limiting (no external deps).

Protects the compute endpoints from accidental hammering / GEE quota burn.
The bucket key prefers the API key, then the real client IP from
``X-Forwarded-For`` (Cloud Run sets this; ``request.client.host`` is only the
proxy and is useless for limiting). NOTE: state is per-process, so cap
``--max-instances`` low or back this with Redis for multi-instance production.
"""
from __future__ import annotations

import threading
import time

from fastapi import Header, HTTPException, Request, status


class TokenBucket:
    def __init__(self, rate_per_min: int):
        self.capacity = max(rate_per_min, 1)
        self.refill_per_sec = self.capacity / 60.0
        self._buckets: dict[str, tuple[float, float]] = {}  # ip -> (tokens, last_ts)
        self._lock = threading.Lock()

    def allow(self, key: str) -> tuple[bool, float]:
        now = time.time()
        with self._lock:
            tokens, last = self._buckets.get(key, (self.capacity, now))
            tokens = min(self.capacity, tokens + (now - last) * self.refill_per_sec)
            if tokens >= 1:
                self._buckets[key] = (tokens - 1, now)
                return True, 0.0
            retry = (1 - tokens) / self.refill_per_sec
            self._buckets[key] = (tokens, now)
            return False, retry


def client_key(request: Request, x_api_key: str | None) -> str:
    """Rate-limit bucket key: API key if present (stable, not IP-spoofable),
    else the first hop of X-Forwarded-For (the real caller behind Cloud Run),
    else the direct peer as a last resort."""
    if x_api_key:
        return f"key:{x_api_key}"
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return "ip:" + xff.split(",")[0].strip()
    return "ip:" + (request.client.host if request.client else "unknown")


def make_rate_limiter(rate_per_min: int):
    bucket = TokenBucket(rate_per_min)

    async def dependency(
        request: Request,
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    ) -> None:
        ok, retry = bucket.allow(client_key(request, x_api_key))
        if not ok:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Retry in {retry:.1f}s.",
                headers={"Retry-After": str(int(retry) + 1)},
            )

    return dependency
