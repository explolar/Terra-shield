"""Health & introspection."""
from __future__ import annotations

from fastapi import APIRouter

from ...core.cache import cache_stats
from ...core.config import get_settings

router = APIRouter(tags=["system"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "terrashield-backend"}


@router.get("/version")
def version() -> dict:
    s = get_settings()
    return {"version": "0.1.0", "env": s.env}


@router.get("/cache/stats")
def cache_statistics() -> dict:
    return cache_stats()
