"""Earth Engine gateway.

A single place to initialize Google Earth Engine. If credentials are missing or
init fails for any reason, the engine drops into DEMO mode instead of crashing —
so the whole platform runs offline. Compute modules check ``is_live()`` and pick
a live or demo code path accordingly.

Earth Engine is imported lazily; importing this module never requires
``earthengine-api`` to be installed.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any

log = logging.getLogger("terrashield.geo.gee")

_MODE_DEMO = "demo"
_MODE_LIVE = "live"


@dataclass
class _State:
    mode: str = _MODE_DEMO
    project: str | None = None
    error: str | None = None
    initialized: bool = False
    datasets_ok: dict[str, bool] = field(default_factory=dict)


_state = _State()


def get_ee() -> Any:
    """Lazily import and return the Earth Engine module, or None if unavailable."""
    try:
        import ee  # type: ignore

        return ee
    except Exception as exc:  # pragma: no cover - environment dependent
        log.debug("earthengine-api not importable: %s", exc)
        return None


def init(project: str | None = None, sa_key: str | None = None, force: bool = False) -> str:
    """Initialize Earth Engine. Returns the active mode: ``"live"`` or ``"demo"``.

    Resolution order for credentials:
      1. explicit ``project`` / ``sa_key`` arguments
      2. ``TERRASHIELD_GEE_PROJECT`` / ``TERRASHIELD_GEE_SA_KEY`` env vars

    Any failure is swallowed and the engine stays in demo mode.
    """
    if _state.initialized and not force:
        return _state.mode

    project = project or os.getenv("TERRASHIELD_GEE_PROJECT") or None
    sa_key = sa_key or os.getenv("TERRASHIELD_GEE_SA_KEY") or None
    _state.initialized = True

    if not project and not sa_key:
        _state.mode = _MODE_DEMO
        _state.error = "no GEE project/credentials configured"
        log.info("Earth Engine: DEMO mode (%s)", _state.error)
        return _state.mode

    ee = get_ee()
    if ee is None:
        _state.mode = _MODE_DEMO
        _state.error = "earthengine-api not installed"
        log.warning("Earth Engine: DEMO mode (%s)", _state.error)
        return _state.mode

    try:
        if sa_key and os.path.exists(sa_key):
            creds = ee.ServiceAccountCredentials(None, key_file=sa_key)
            ee.Initialize(creds, project=project)
        else:
            # Application Default Credentials (local OAuth or Cloud Run ADC).
            ee.Initialize(project=project)
        _state.mode = _MODE_LIVE
        _state.project = project
        _state.error = None
        log.info("Earth Engine: LIVE (project=%s)", project)
    except Exception as exc:
        _state.mode = _MODE_DEMO
        _state.error = f"{type(exc).__name__}: {exc}"
        log.warning("Earth Engine init failed, DEMO mode: %s", _state.error)
    return _state.mode


def is_live() -> bool:
    if not _state.initialized:
        init()
    return _state.mode == _MODE_LIVE


def mode() -> str:
    if not _state.initialized:
        init()
    return _state.mode


def status() -> dict:
    """Diagnostic status for the /earthdata/status endpoint."""
    if not _state.initialized:
        init()
    return {
        "mode": _state.mode,
        "project": _state.project,
        "error": _state.error,
        "ee_installed": get_ee() is not None,
    }


def evaluate_parallel(objs: dict[str, Any], max_workers: int = 6) -> dict[str, Any]:  # pragma: no cover
    """Evaluate several Earth Engine objects concurrently via ``getInfo``.

    Each ``getInfo`` is an independent, blocking HTTPS round-trip to Google's
    servers, so a small thread pool collapses N sequential waits into roughly one.
    Used where the per-call computations are heavy enough that batching them into
    a single request would risk the Earth Engine compute/timeout limit (e.g.
    multi-year SAR reductions). Returns a dict mapping the same keys to results.
    """
    from concurrent.futures import ThreadPoolExecutor

    items = list(objs.items())
    if not items:
        return {}

    def _eval(kv):
        key, obj = kv
        return key, obj.getInfo()

    out: dict[str, Any] = {}
    with ThreadPoolExecutor(max_workers=min(max_workers, len(items))) as ex:
        for key, value in ex.map(_eval, items):
            out[key] = value
    return out
