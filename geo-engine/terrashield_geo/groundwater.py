"""GroundwaterAI — terrestrial water-storage & groundwater-depletion analytics.

Inspired by groundwater-intelligence products (e.g. SmartBhujal's GWFlowAI), this
module brings water security into TerraShield using NASA GRACE / GRACE-FO.

  * storage anomaly  — GRACE liquid-water-equivalent thickness (cm vs 2004-2009)
  * depletion trend  — linear trend of the storage anomaly (cm/yr); negative =
                       depletion (cf. Rodell et al., 2009/2018; Famiglietti, 2014)
  * recharge proxy   — CHIRPS rainfall minus MODIS evapotranspiration (mm/yr)
  * stress class     — from the depletion trend

Live path uses Earth Engine; demo path is deterministic.
"""
from __future__ import annotations

import logging
from typing import Any

from . import aoi as aoi_mod
from . import demo, gee, tiles

log = logging.getLogger("terrashield.geo.groundwater")

# Depletion-trend classes (cm/yr of terrestrial water storage).
STRESS_CLASSES = [
    ("Severe depletion", -1.5, "#67000d"),
    ("High depletion", -0.8, "#cb181d"),
    ("Moderate depletion", -0.3, "#fb6a4a"),
    ("Stable", 0.3, "#fee08b"),
    ("Recharging", 100.0, "#1a9850"),
]


def _classify(trend: float) -> str:
    for label, thr, _c in STRESS_CLASSES:
        if trend <= thr:
            return label
    return "Recharging"


def groundwater(aoi: dict[str, Any]) -> dict[str, Any]:
    norm = aoi_mod.normalize(aoi, aoi_mod.COARSE_MAX_AREA_KM2)  # GRACE is regional-scale
    if gee.is_live():
        try:
            return _groundwater_live(norm)
        except Exception as exc:  # pragma: no cover
            log.warning("groundwater live failed, demo fallback: %s", exc)
    return _groundwater_demo(norm)


def _groundwater_demo(norm) -> dict[str, Any]:
    import numpy as np

    bbox = norm["bbox"]
    field = demo.smooth_field(bbox, 20, salt="groundwater:tws")
    anomaly = (field - 0.55) * 30.0  # cm, roughly [-16, +13]
    grid = demo.field_to_grid(bbox, anomaly.round(1), value_key="anomaly_cm")
    rng = np.random.default_rng(abs(hash(tuple(round(b, 3) for b in bbox))) % (2**32))
    trend = float(np.clip(rng.normal(-0.7, 0.6), -2.5, 1.0))  # most regions depleting
    years = list(range(2004, 2025))
    base = float(anomaly.mean())
    series = [{"year": y, "anomaly_cm": round(base + trend * (y - 2004) + rng.normal(0, 1.2), 1)}
              for y in years]
    return {
        "module": "groundwater", "product": "storage", "source": "demo",
        "tile_url": None, "grid": grid,
        "legend": [{"label": l, "color": c} for l, _, c in STRESS_CLASSES],
        "series": series,
        "stats": {
            "mean_anomaly_cm": round(float(anomaly.mean()), 1),
            "depletion_trend_cm_yr": round(trend, 2),
            "stress_class": _classify(trend),
            "recharge_proxy_mm_yr": round(float(rng.uniform(-200, 400)), 0),
            "native_resolution": "~3° mascon (~330 km)",
            "regional_note": (
                "GRACE resolves total water storage at regional scale (~330 km / "
                "~150,000 km² per mascon). Values represent the wider aquifer system "
                "around this AOI, not a single field or well."
            ),
            "area_km2": norm["area_km2"],
        },
        "aoi": {"bbox": bbox, "centroid": norm["centroid"]},
    }


def _groundwater_live(norm) -> dict[str, Any]:  # pragma: no cover
    import numpy as np

    ee = gee.get_ee()
    geom = aoi_mod.to_ee_geometry(norm)
    # Continuous GRACE + GRACE-FO record (2002-present) via the JPL mascon CRI
    # solution (single lwe_thickness band, cm). The older MASS_GRIDS_V04/LAND
    # product only runs through Jan 2017, so the series stopped at the GRACE
    # mission end; the mascon spans the GRACE/GRACE-FO gap to recent years.
    col = ee.ImageCollection("NASA/GRACE/MASS_GRIDS_V04/MASCON_CRI").map(
        lambda img: img.select("lwe_thickness").rename("lwe")
            .copyProperties(img, ["system:time_start"])
    )

    # Region-mean monthly anomaly series. One getInfo pulls every (t, v) point;
    # the trend is then fit client-side (avoids a second server round-trip).
    def to_feat(img):
        v = img.reduceRegion(ee.Reducer.mean(), geom, 50000,
                             maxPixels=1e9, bestEffort=True, tileScale=4).values().get(0)
        t = img.date().difference(ee.Date("2004-01-01"), "year")
        return ee.Feature(None, {"t": t, "v": v})

    fc = ee.FeatureCollection(col.map(to_feat)).filter(ee.Filter.notNull(["v"]))

    # Recharge proxy: CHIRPS annual rainfall - MODIS ET (mm/yr). Built as a
    # null-safe ee.Number so it can be evaluated alongside the series.
    recharge_num = None
    try:
        rain = (ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
                .filterDate("2022-01-01", "2023-01-01").select("precipitation").sum())
        et = (ee.ImageCollection("MODIS/061/MOD16A2").filterDate("2022-01-01", "2023-01-01")
              .select("ET").sum().multiply(0.1))  # 0.1 mm scale
        rv = rain.subtract(et).reduceRegion(
            ee.Reducer.mean(), geom, 5000, maxPixels=1e9, bestEffort=True, tileScale=4).values().get(0)
        recharge_num = ee.Number(ee.Algorithms.If(rv, rv, 0))
    except Exception:  # pragma: no cover  — recharge is optional
        recharge_num = None

    # Pull the series and the recharge value concurrently (two independent
    # round-trips). If recharge evaluation fails it must not drop the series, so
    # fall back to a series-only fetch.
    recharge_val = None
    objs = {"series": fc}
    if recharge_num is not None:
        objs["recharge"] = recharge_num
    try:
        ev = gee.evaluate_parallel(objs)
        points = ev["series"].get("features", [])
        if "recharge" in ev:
            recharge_val = round(float(ev["recharge"] or 0.0), 0)
    except Exception:  # pragma: no cover  — recharge errored; series is essential
        points = fc.getInfo().get("features", [])

    ts = np.array([(p["properties"]["t"], p["properties"]["v"]) for p in points
                   if p["properties"].get("v") is not None], dtype=float)

    trend, mean_anom = 0.0, 0.0
    series: list[dict[str, Any]] = []
    if ts.shape[0] >= 2:
        trend = float(np.polyfit(ts[:, 0], ts[:, 1], 1)[0])  # cm/yr
        # Annual means -> compact, readable series for the chart.
        by_year: dict[int, list[float]] = {}
        for t, v in ts:
            by_year.setdefault(2004 + int(t), []).append(v)
        series = [{"year": y, "anomaly_cm": round(float(np.mean(vs)), 1)}
                  for y, vs in sorted(by_year.items())]
        # "Current" anomaly = mean of the most recent 12 monthly solutions.
        mean_anom = float(np.mean(ts[ts[:, 0].argsort()][-12:, 1]))
    elif ts.shape[0] == 1:
        mean_anom = float(ts[0, 1])

    latest = ee.Image(col.sort("system:time_start", False).first())
    tile_url = tiles.image_tile_url(
        latest.clip(geom),
        {"min": -20, "max": 20, "palette": ["#67000d", "#fb6a4a", "#ffffbf", "#74add1", "#313695"]})

    return {
        "module": "groundwater", "product": "storage", "source": "live",
        "tile_url": tile_url, "grid": None,
        "legend": [{"label": l, "color": c} for l, _, c in STRESS_CLASSES],
        "series": series,
        "stats": {
            "mean_anomaly_cm": round(mean_anom, 1),
            "depletion_trend_cm_yr": round(trend, 2),
            "stress_class": _classify(trend),
            "recharge_proxy_mm_yr": recharge_val,
            "dataset": "NASA GRACE/GRACE-FO Mascon CRI (V04 RL06.3, to 2024)",
            "native_resolution": "~3° mascon (~330 km)",
            "regional_note": (
                "GRACE resolves total water storage at regional scale (~330 km / "
                "~150,000 km² per mascon). Values represent the wider aquifer system "
                "around this AOI, not a single field or well."
            ),
            "n_observations": int(ts.shape[0]),
            "area_km2": norm["area_km2"],
        },
        "aoi": {"bbox": norm["bbox"], "centroid": norm["centroid"]},
    }
