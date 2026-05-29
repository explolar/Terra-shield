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


def _spi_gamma(hist: list, x) -> float:
    """Standardized Precipitation Index via the canonical gamma fit (McKee et al.,
    1993): fit a 2-parameter gamma to the non-zero accumulations, mix in the
    probability of zero, then map the CDF to the standard normal."""
    import numpy as np
    from scipy import stats

    arr = np.array([h for h in hist if h is not None], dtype=float)
    arr = arr[~np.isnan(arr)]
    if arr.size < 5 or x is None:
        return 0.0
    n = arr.size
    q = float((arr <= 0).sum()) / n  # probability of zero precipitation
    nz = arr[arr > 0]
    if nz.size < 3:
        return 0.0
    a, _loc, scale = stats.gamma.fit(nz, floc=0)
    cdf = q + (1 - q) * stats.gamma.cdf(float(x), a, loc=0, scale=scale)
    # Clamp to ~±3 sigma (norm.cdf(±3)) — SPI beyond this is almost always a data
    # artifact, not a real signal.
    cdf = min(max(cdf, 0.00135), 0.99865)
    return round(float(stats.norm.ppf(cdf)), 2)


def _spi_live(norm, scale_months) -> dict[str, Any]:  # pragma: no cover
    ee = gee.get_ee()
    geom = aoi_mod.to_ee_geometry(norm)

    chirps = ee.ImageCollection("UCSB-CHG/CHIRPS/PENTAD").select("precipitation")
    # Anchor to the START of the latest month so the most recent window uses the 3
    # fully-complete months before it (CHIRPS pentads lag ~3 weeks; the latest
    # partial month would otherwise read as a false extreme drought).
    last = ee.Date(chirps.aggregate_max("system:time_start"))
    end = ee.Date.fromYMD(last.get("year"), last.get("month"), 1)
    end_month = end.get("month")
    years = ee.List.sequence(1991, 2020)

    # One scale_months accumulation per historical year, ending in the same month.
    def window_sum(y):
        y = ee.Number(y)
        e = ee.Date.fromYMD(y, end_month, 1)
        s = e.advance(-scale_months, "month")
        return chirps.filterDate(s, e).sum().set("year", y)

    hist_ic = ee.ImageCollection(years.map(window_sum))

    def region_val(img):
        v = ee.Image(img).reduceRegion(
            reducer=ee.Reducer.mean(), geometry=geom, scale=5000,
            maxPixels=1e9, bestEffort=True, tileScale=4,
        ).values().get(0)
        return ee.Algorithms.If(v, v, 0)

    # Pull the regional accumulation series + the recent value, fit gamma in Python.
    hist_vals = ee.List(hist_ic.toList(hist_ic.size()).map(region_val)).getInfo()
    recent_img = chirps.filterDate(end.advance(-scale_months, "month"), end).sum()
    _rv = recent_img.reduceRegion(
        reducer=ee.Reducer.mean(), geometry=geom, scale=5000,
        maxPixels=1e9, bestEffort=True, tileScale=4,
    ).values().get(0)
    recent_val = ee.Number(ee.Algorithms.If(_rv, _rv, 0)).getInfo()
    spi_value = _spi_gamma(hist_vals, recent_val)

    # Per-pixel SPI map: a z-score image (band names aligned to avoid mismatch).
    clim_mean = hist_ic.mean().rename("p")
    clim_std = hist_ic.reduce(ee.Reducer.stdDev()).rename("p").max(1)
    spi_img = recent_img.rename("p").subtract(clim_mean).divide(clim_std).rename("spi").clip(geom)
    tile_url = tiles.image_tile_url(
        spi_img, {"min": -2.5, "max": 2.5,
                  "palette": ["#730000", "#ffaa00", "#ffffff", "#41b6c4", "#253494"]}
    )

    return {
        "module": "drought",
        "product": "spi",
        "source": "live",
        "scale_months": scale_months,
        "tile_url": tile_url,
        "grid": None,
        "legend": [{"label": l, "color": c} for l, _, c in SPI_CLASSES],
        "stats": {
            "mean_spi": round(spi_value, 2),
            "class": _classify_spi(spi_value),
            "method": "gamma-fit SPI (McKee et al., 1993)",
            "area_km2": norm["area_km2"],
        },
        "aoi": {"bbox": norm["bbox"], "centroid": norm["centroid"]},
    }


def _standardize(hist: list, x) -> float:
    """Normal standardization of a (possibly negative) water-balance series to a
    z-score, clamped to ±3. The canonical SPEI fits a log-logistic (Vicente-
    Serrano 2010); the Gaussian standardization is a common, stable operational
    simplification for D = P − PET, which is roughly symmetric."""
    import numpy as np

    arr = np.array([h for h in hist if h is not None], dtype=float)
    arr = arr[~np.isnan(arr)]
    if arr.size < 5 or x is None:
        return 0.0
    mu, sd = float(arr.mean()), float(arr.std() or 1.0)
    return round(float(np.clip((float(x) - mu) / sd, -3.0, 3.0)), 2)


def spei(aoi: dict[str, Any], scale_months: int = 3) -> dict[str, Any]:
    """Standardized Precipitation-Evapotranspiration Index (Vicente-Serrano 2010):
    like SPI but on the water balance P − PET, so it captures heat-driven drought
    that SPI misses — important for warming monsoon climates."""
    norm = aoi_mod.normalize(aoi)
    if scale_months not in SPI_SCALES:
        scale_months = 3
    if gee.is_live():
        try:
            return _spei_live(norm, scale_months)
        except Exception as exc:  # pragma: no cover
            log.warning("drought.spei live failed, demo fallback: %s", exc)
    return _spei_demo(norm, scale_months)


def _spei_demo(norm, scale_months) -> dict[str, Any]:
    import numpy as np

    bbox = norm["bbox"]
    field = demo.smooth_field(bbox, 22, salt=f"drought:spei:{scale_months}")
    spei_field = (field - 0.55) * 5.0  # drier bias — PET pulls the water balance down
    grid = demo.field_to_grid(bbox, spei_field.round(2), value_key="spei")
    mean_spei = float(spei_field.mean())
    return {
        "module": "drought", "product": "spei", "source": "demo",
        "scale_months": scale_months, "tile_url": None, "grid": grid,
        "legend": [{"label": l, "color": c} for l, _, c in SPI_CLASSES],
        "stats": {
            "mean_spei": round(mean_spei, 2),
            "class": _classify_spi(mean_spei),
            "drought_area_pct": round(float((spei_field <= -0.8).mean() * 100), 1),
            "method": "P−PET standardized (demo)",
            "area_km2": norm["area_km2"],
        },
        "aoi": {"bbox": bbox, "centroid": norm["centroid"]},
    }


def _spei_live(norm, scale_months) -> dict[str, Any]:  # pragma: no cover
    ee = gee.get_ee()
    geom = aoi_mod.to_ee_geometry(norm)

    # TerraClimate monthly water balance D = precip − PET (mm). PET band scale 0.1.
    tc = ee.ImageCollection("IDAHO_EPSCOR/TERRACLIMATE")

    def wbal(img):
        img = ee.Image(img)
        return (img.select("pr").subtract(img.select("pet").multiply(0.1))
                .rename("d").copyProperties(img, ["system:time_start"]))

    d_coll = tc.map(wbal)
    last = ee.Date(tc.aggregate_max("system:time_start"))
    end = ee.Date.fromYMD(last.get("year"), last.get("month"), 1)
    end_month = end.get("month")
    years = ee.List.sequence(1991, 2020)

    def window_sum(y):
        y = ee.Number(y)
        e = ee.Date.fromYMD(y, end_month, 1)
        s = e.advance(-scale_months, "month")
        return d_coll.filterDate(s, e).sum().set("year", y)

    hist_ic = ee.ImageCollection(years.map(window_sum))

    def region_val(img):
        v = ee.Image(img).reduceRegion(ee.Reducer.mean(), geom, 5000,
                                       maxPixels=1e9, bestEffort=True, tileScale=4).values().get(0)
        return ee.Algorithms.If(v, v, 0)

    hist_vals = ee.List(hist_ic.toList(hist_ic.size()).map(region_val)).getInfo()
    recent_img = d_coll.filterDate(end.advance(-scale_months, "month"), end).sum()
    _rv = recent_img.reduceRegion(ee.Reducer.mean(), geom, 5000,
                                  maxPixels=1e9, bestEffort=True, tileScale=4).values().get(0)
    recent_val = ee.Number(ee.Algorithms.If(_rv, _rv, 0)).getInfo()
    spei_value = _standardize(hist_vals, recent_val)

    clim_mean = hist_ic.mean().rename("d")
    clim_std = hist_ic.reduce(ee.Reducer.stdDev()).rename("d").max(1)
    spei_img = recent_img.rename("d").subtract(clim_mean).divide(clim_std).rename("spei").clip(geom)
    tile_url = tiles.image_tile_url(
        spei_img, {"min": -2.5, "max": 2.5,
                   "palette": ["#730000", "#ffaa00", "#ffffff", "#41b6c4", "#253494"]})

    return {
        "module": "drought", "product": "spei", "source": "live",
        "scale_months": scale_months, "tile_url": tile_url, "grid": None,
        "legend": [{"label": l, "color": c} for l, _, c in SPI_CLASSES],
        "stats": {
            "mean_spei": round(spei_value, 2),
            "class": _classify_spi(spei_value),
            "method": "P−PET standardized SPEI (TerraClimate; Vicente-Serrano 2010)",
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

    # Thermal Condition Index (TCI) from MODIS LST, then the Vegetation Health
    # Index VHI = 0.5·VCI + 0.5·TCI (Kogan 1995) — a composite that captures both
    # moisture (VCI) and heat (TCI) stress, more robust than NDVI alone.
    vhi = None
    try:
        lst = ee.ImageCollection("MODIS/061/MOD11A2").select("LST_Day_1km")
        lst_last = ee.Date(lst.aggregate_max("system:time_start"))
        lst_recent = lst.filterDate(lst_last.advance(-1, "month"), lst_last).mean().multiply(0.02).clip(geom)
        lst_hist = lst.filterDate("2015-01-01", "2023-12-31")
        lst_min = lst_hist.min().multiply(0.02).clip(geom)
        lst_max = lst_hist.max().multiply(0.02).clip(geom)
        tci = lst_max.subtract(lst_recent).divide(lst_max.subtract(lst_min).max(0.001)).rename("tci")
        vhi = vci.multiply(0.5).add(tci.multiply(0.5)).rename("vhi")
    except Exception:  # pragma: no cover  — LST optional
        vhi = None

    bands = vci if vhi is None else vci.addBands(vhi)
    red = bands.reduceRegion(reducer=ee.Reducer.mean(), geometry=geom, scale=1000,
                             maxPixels=1e9, bestEffort=True).getInfo()
    mean_vci = float(red.get("vci") or 0)
    mean_vhi = red.get("vhi")
    stats = {"mean_vci": round(mean_vci, 3), "area_km2": norm["area_km2"]}
    if mean_vhi is not None:
        stats["mean_vhi"] = round(float(mean_vhi), 3)
        stats["index"] = "Vegetation Health Index (0.5·VCI + 0.5·TCI; Kogan 1995)"
    return {
        "module": "drought",
        "product": "vegetation",
        "source": "live",
        "tile_url": tile_url,
        "grid": None,
        "legend": tiles.build_legend("vegetation", ["Stressed", "", "Fair", "", "Healthy"]),
        "stats": stats,
        "aoi": {"bbox": norm["bbox"], "centroid": norm["centroid"]},
    }
