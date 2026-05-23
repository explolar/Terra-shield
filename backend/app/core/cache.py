"""In-process TTL cache for expensive geo-engine results.

Keyed by (namespace, normalized-request-json). Swap for Redis in production by
re-implementing get/set against a redis client — the call sites won't change.
GEE calls are slow and quota-limited, so caching is a first-class concern.
"""
from __future__ import annotations

import hashlib
import json
import threading
import time
from typing import Any, Callable

from .config import get_settings


class TTLCache:
    def __init__(self, ttl_seconds: int, max_entries: int = 512):
        self.ttl = ttl_seconds
        self.max_entries = max_entries
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    def _evict_if_needed(self) -> None:
        if len(self._store) <= self.max_entries:
            return
        # Drop the oldest ~10% of entries.
        oldest = sorted(self._store.items(), key=lambda kv: kv[1][0])
        for k, _ in oldest[: max(1, self.max_entries // 10)]:
            self._store.pop(k, None)

    def get(self, key: str) -> Any | None:
        with self._lock:
            item = self._store.get(key)
            if item is None:
                self.misses += 1
                return None
            ts, value = item
            if time.time() - ts > self.ttl:
                self._store.pop(key, None)
                self.misses += 1
                return None
            self.hits += 1
            return value

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._store[key] = (time.time(), value)
            self._evict_if_needed()

    def stats(self) -> dict[str, Any]:
        total = self.hits + self.misses
        return {
            "entries": len(self._store),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(self.hits / total, 3) if total else 0.0,
        }


_cache = TTLCache(ttl_seconds=get_settings().cache_ttl_seconds)


def make_key(namespace: str, payload: Any) -> str:
    blob = json.dumps(payload, sort_keys=True, default=str)
    digest = hashlib.sha256(blob.encode()).hexdigest()[:24]
    return f"{namespace}:{digest}"


def cached(namespace: str, payload: Any, producer: Callable[[], Any]) -> Any:
    """Return cached value for (namespace, payload) or compute+store it."""
    key = make_key(namespace, payload)
    hit = _cache.get(key)
    if hit is not None:
        return hit
    value = producer()
    _cache.set(key, value)
    return value


def cache_stats() -> dict[str, Any]:
    return _cache.stats()
