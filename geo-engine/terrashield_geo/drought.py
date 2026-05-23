"""DroughtAI compute — meteorological and vegetation drought.

  * ``spi``         — Standardized Precipitation Index from CHIRPS (McKee 1993).
  * ``vegetation``  — NDVI / Vegetation Condition Index anomaly.

Live path uses CHIRPS and MODIS/Sentinel-2; demo path is deterministic.
"""
from __future__ import annotations

import logging
from typing import Any

from . import aoi as aoi_mod
from . import demo, gee, tiles

log = logging.getLogger("terrashield.geo.drought")

SPI_SCALES = [1, 3, 6, 12]
# US Drought Monitor style classes by SPI value.
SPI_CLASSES = [
    ("D4 Exceptional", -2.0, "#730000"),
    ("D3 Extreme", -1.6, "#e60000"),
    ("D2 Severe", -1.3, "#ffaa00"),
    ("D1 Moderate", -0.8, "#fcd37f"),
    ("D0 Abnormal", -0.5, "#ffff00"),
    ("Normal+", 100, "#ffffff"),
]


def _classify_spi(value: float) -> str:
    for label, threshold, _ in SPI_CLASSES:
        if value <= threshold:
            return label
    return "Normal+"


def spi(aoi: dict[str, Any], scale_months: int = 3) -> dict[str, Any]:
    norm = aoi_mod.normalize(aoi)
    if scale_months not in SPI_SCALES:
        scale_months = 3
    if gee.is_live():
        try:
            return _spi_live(norm, scale_months)
        except Exception as exc:  # pragma: no cover
            log.warning("drought.spi live failed, demo fallback: %s", exc)
    return _spi_demo(norm, scale_months)


def _spi_demo(norm, scale_months) -> dict[str, Any]:
    import numpy as np

    bbox = norm["bbox"]
    # Map a [0,1] field to an SPI-like range roughly [-2.5, 2.5].
    field = demo.smooth_field(bbox, 22, salt=f"drought:spi:{scale_months}")
    spi_field = (field - 0.5) * 5.0
    grid = demo.field_to_grid(bbox, spi_field.round(2), value_key="spi")
    mean_spi = float(spi_field.mean())
    drought_pct = float((spi_field <= -0.8).mean() * 100)
    return {
        "module": "drought",
        "product": "spi",
        "source": "demo",
        "scale_months": scale_months,
        "tile_url": None,
        "grid": grid,
        "legend": [{"label": l, "color": c} for l, _, c in SPI_CLASSES],
        "stats": {
            "mean_spi": round(mean_spi, 2),
            "class": _classify_spi(mean_spi),
            "drought_area_pct": round(drought_pct, 1),
            "area_km2": norm["area_km2"],
        },
        "aoi": {"bbox": bbox, "centroid": norm["centroid"]},
    }


def _spi_live(norm, scale_months) -> dict[str, Any]:  # pragma: no cover
    ee = gee.get_ee()
    geom = aoi_mod.to_ee_geometry(norm)

    chirps = ee.ImageCollection("UCSB-CHG/CHIRPS/PENTAD").select("precipitation")
    # Build a monthly accumulation series, then z-score the most recent window
    # against the historical distribution (a pragmatic SPI approximation).
    end = ee.Date(chirps.aggregate_max("system:time_start"))
    window = end.advance(-scale_months, "month")
    recent = chirps.filterDate(window, end).sum().clip(geom)

    years = ee.List.sequence(1991, 2020)

    def yearly(y):
        y = ee.Number(y)
        s = ee.Date.fromYMD(y, end.get("month"), 1).advance(-scale_months, "month")
        e = ee.Date.fromYMD(y, end.get("month"), 1)
        return chirps.filterDate(s, e).sum().clip(geom).set("year", y)

    hist = ee.ImageCollection(years.map(yearly))
    mean = hist.mean()
    std = hist.reduce(ee.Reducer.stdDev()).max(0.001)
    spi_img = recent.subtract(mean).divide(std).rename("spi")

    tile_url = tiles.image_tile_url(
        spi_img, {"min": -2.5, "max": 2.5, "palette": ["#730000", "#ffaa00", "#ffffff", "#41b6c4", "#253494"]}
    )
    mean_spi = ee.Number(
        spi_img.reduceRegion(reducer=ee.Reducer.mean(), geometry=geom, scale=5000,
                             maxPixels=1e9, bestEffort=True).get("spi")
    ).getInfo()
    return {
        "module": "drought",
        "product": "spi",
        "source": "live",
        "scale_months": scale_months,
        "tile_url": tile_url,
        "grid": None,
        "legend": [{"label": l, "color": c} for l, _, c in SPI_CLASSES],
        "stats": {
            "mean_spi": round(mean_spi, 2),
            "class": _classify_spi(mean_spi),
            "area_km2": norm["area_km2"],
        },
        "aoi": {"bbox": norm["bbox"], "centroid": norm["centroid"]},
    }


def vegetation(aoi: dict[str, Any]) -> dict[str, Any]:
    """NDVI / Vegetation Condition Index anomaly (vegetation stress)."""
    norm = aoi_mod.normalize(aoi)
    if gee.is_live():
        try:
            return _vegetation_live(norm)
        except Exception as exc:  # pragma: no cover
            log.warning("drought.vegetation live failed, demo fallback: %s", exc)
    return _vegetation_demo(norm)


def _vegetation_demo(norm) -> dict[str, Any]:
    import numpy as np

    bbox = norm["bbox"]
    field = demo.smooth_field(bbox, 22, salt="drought:vci")
    vci = field  # 0 (stressed) .. 1 (healthy)
    grid = demo.field_to_grid(bbox, vci.round(3), value_key="vci")
    stressed = float((vci < 0.35).mean() * 100)
    return {
        "module": "drought",
        "product": "vegetation",
        "source": "demo",
        "tile_url": None,
        "grid": grid,
        "legend": tiles.build_legend("vegetation", ["Stressed", "", "Fair", "", "Healthy"]),
        "stats": {
            "mean_vci": round(float(vci.mean()), 3),
            "stressed_area_pct": round(stressed, 1),
            "area_km2": norm["area_km2"],
        },
        "aoi": {"bbox": bbox, "centroid": norm["centroid"]},
    }


def _vegetation_live(norm) -> dict[str, Any]:  # pragma: no cover
    ee = gee.get_ee()
    geom = aoi_mod.to_ee_geometry(norm)
    modis = ee.ImageCollection("MODIS/061/MOD13A2").select("NDVI")
    recent = modis.filterDate(
        ee.Date(modis.aggregate_max("system:time_start")).advance(-1, "month"),
        ee.Date(modis.aggregate_max("system:time_start")),
    ).mean().multiply(0.0001).clip(geom)
    hist = modis.filterDate("2015-01-01", "2023-12-31")
    ndvi_min = hist.min().multiply(0.0001).clip(geom)
    ndvi_max = hist.max().multiply(0.0001).clip(geom)
    vci = recent.subtract(ndvi_min).divide(ndvi_max.subtract(ndvi_min).max(0.001)).rename("vci")
    tile_url = tiles.image_tile_url(vci, {"min": 0, "max": 1, "palette": tiles.RAMPS["vegetation"]})
    mean_vci = ee.Number(
        vci.reduceRegion(reducer=ee.Reducer.mean(), geometry=geom, scale=1000,
                         maxPixels=1e9, bestEffort=True).get("vci")
    ).getInfo()
    return {
        "module": "drought",
        "product": "vegetation",
        "source": "live",
        "tile_url": tile_url,
        "grid": None,
        "legend": tiles.build_legend("vegetation", ["Stressed", "", "Fair", "", "Healthy"]),
        "stats": {"mean_vci": round(mean_vci, 3), "area_km2": norm["area_km2"]},
        "aoi": {"bbox": norm["bbox"], "centroid": norm["centroid"]},
    }
