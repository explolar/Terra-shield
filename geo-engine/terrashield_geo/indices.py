"""Spectral index helpers (live path).

Pure functions over an ``ee.Image`` with standard band names. Kept here so the
flood/drought modules share one definition of NDVI, NDWI, etc.
"""
from __future__ import annotations

from typing import Any


def ndvi(image: Any, nir: str = "B8", red: str = "B4") -> Any:
    return image.normalizedDifference([nir, red]).rename("ndvi")


def ndwi(image: Any, green: str = "B3", nir: str = "B8") -> Any:
    """McFeeters NDWI — open water delineation."""
    return image.normalizedDifference([green, nir]).rename("ndwi")


def mndwi(image: Any, green: str = "B3", swir: str = "B11") -> Any:
    """Modified NDWI — better water/built-up separation."""
    return image.normalizedDifference([green, swir]).rename("mndwi")


def savi(image: Any, nir: str = "B8", red: str = "B4", L: float = 0.5) -> Any:
    n, r = image.select(nir), image.select(red)
    return n.subtract(r).multiply(1 + L).divide(n.add(r).add(L)).rename("savi")


def vci(ndvi_img: Any, ndvi_min: Any, ndvi_max: Any) -> Any:
    """Vegetation Condition Index in [0, 1]."""
    return (
        ndvi_img.subtract(ndvi_min)
        .divide(ndvi_max.subtract(ndvi_min).max(0.001))
        .clamp(0, 1)
        .rename("vci")
    )
