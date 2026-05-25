"""terrashield_geo — the EarthData Engine.

Geospatial compute for TerraShield AI. Runs live on Google Earth Engine when
credentials are present, and falls back to deterministic demo surfaces otherwise
so the whole platform works offline.
"""
from __future__ import annotations

from . import (
    aoi,
    climate,
    datasets,
    drought,
    flood,
    flood_factors,
    gee,
    groundwater,
    indices,
    infra,
    landslide,
    ml_flood,
    optimize,
    tiles,
)

__version__ = "0.1.0"

__all__ = [
    "aoi",
    "climate",
    "datasets",
    "drought",
    "flood",
    "flood_factors",
    "gee",
    "groundwater",
    "indices",
    "infra",
    "landslide",
    "ml_flood",
    "optimize",
    "tiles",
    "__version__",
]
