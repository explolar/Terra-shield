"""Lightweight per-IP token-bucket rate limiting (no external deps).

Protects the compute endpoints from accidental hammering / GEE quota burn.
For multi-instance production, back this with Redis instead of process memory.
"""
from __future__ import annotations

import threading
import time

from fastapi import HTTPException, Request, status


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


def make_rate_limiter(rate_per_min: int):
    bucket = TokenBucket(rate_per_min)

    async def dependency(request: Request) -> None:
        ip = request.client.host if request.client else "unknown"
        ok, retry = bucket.allow(ip)
        if not ok:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Retry in {retry:.1f}s.",
                headers={"Retry-After": str(int(retry) + 1)},
            )

    return dependency
