"""ClimateLens compute — CMIP6 / SSP future-climate projections.

Live path uses NASA NEX-GDDP-CMIP6 (``NASA/GDDP-CMIP6``) on Earth Engine:
0.25°, daily, 1950–2100, SSP scenarios. Demo path returns deterministic
projections so the dashboard works offline.
"""
from __future__ import annotations

import logging
from typing import Any

from . import aoi as aoi_mod
from . import demo, gee, tiles

log = logging.getLogger("terrashield.geo.climate")

SCENARIOS = ["ssp245", "ssp585"]
VARIABLES = {
    "pr": {"label": "Precipitation", "unit": "mm/yr", "ramp": "precip"},
    "tas": {"label": "Mean temperature", "unit": "°C", "ramp": "temp"},
    "tasmax": {"label": "Max temperature", "unit": "°C", "ramp": "temp"},
}
HORIZONS = {"2030s": (2030, 2039), "2050s": (2050, 2059), "2080s": (2080, 2089)}
BASELINE = (1995, 2014)

# Small curated NEX-GDDP-CMIP6 ensemble (all present in the dataset) — averaged
# instead of a single model so the projection isn't hostage to one GCM's bias.
ENSEMBLE_MODELS = ["ACCESS-CM2", "MPI-ESM1-2-HR", "EC-Earth3", "MRI-ESM2-0", "GFDL-ESM4"]

# Rough warming/wetting signal strength per scenario (demo realism).
_SIGNAL = {
    "ssp245": {"pr": 0.08, "tas": 1.8, "tasmax": 2.0},
    "ssp585": {"pr": 0.18, "tas": 3.6, "tasmax": 4.2},
}


def scenarios() -> dict[str, Any]:
    return {
        "scenarios": SCENARIOS,
        "variables": VARIABLES,
        "horizons": list(HORIZONS.keys()),
        "baseline": f"{BASELINE[0]}-{BASELINE[1]}",
        "models": ["ensemble", "ACCESS-CM2", "MPI-ESM1-2-HR", "EC-Earth3"],
        "dataset": "NASA/GDDP-CMIP6 (NEX-GDDP-CMIP6)",
    }


def projection(
    aoi: dict[str, Any],
    scenario: str = "ssp585",
    variable: str = "pr",
    horizon: str = "2050s",
    model: str = "ensemble",
) -> dict[str, Any]:
    norm = aoi_mod.normalize(aoi, aoi_mod.COARSE_MAX_AREA_KM2)  # CMIP6 is regional-scale
    if scenario not in SCENARIOS:
        scenario = "ssp585"
    if variable not in VARIABLES:
        variable = "pr"
    if horizon not in HORIZONS:
        horizon = "2050s"

    if gee.is_live():
        try:
            return _projection_live(norm, scenario, variable, horizon, model)
        except Exception as exc:  # pragma: no cover
            log.warning("climate.projection live failed, demo fallback: %s", exc)
    return _projection_demo(norm, scenario, variable, horizon, model)


def _projection_demo(norm, scenario, variable, horizon, model) -> dict[str, Any]:
    import numpy as np

    bbox = norm["bbox"]
    meta = VARIABLES[variable]
    signal = _SIGNAL[scenario][variable]

    # Plausible baseline level from latitude (cooler/wetter signals).
    lat = abs(norm["centroid"][1])
    if variable == "pr":
        baseline_val = float(np.interp(lat, [0, 10, 25, 40], [2400, 1500, 900, 600]))
        projected_val = baseline_val * (1 + signal)
        delta = projected_val - baseline_val
        pct = signal * 100
    else:
        baseline_val = float(np.interp(lat, [0, 15, 30, 45], [28, 27, 25, 18]))
        if variable == "tasmax":
            baseline_val += 6
        projected_val = baseline_val + signal
        delta = signal
        pct = signal / max(baseline_val, 1e-6) * 100

    # Yearly time series baseline-mid → horizon-end with noise + trend.
    y0, y1 = BASELINE[0], HORIZONS[horizon][1]
    years = list(range(y0, y1 + 1))
    rng = np.random.default_rng(abs(hash((tuple(bbox), scenario, variable))) % (2**32))
    trend = np.linspace(baseline_val, projected_val, len(years))
    noise = rng.normal(0, abs(delta) * 0.25 + (baseline_val * 0.02), len(years))
    series = [round(float(t + nz), 2) for t, nz in zip(trend, noise)]

    # Spatial anomaly grid.
    field = demo.smooth_field(bbox, 22, salt=f"climate:{variable}:{scenario}")
    anomaly_grid = demo.field_to_grid(
        bbox, (field * delta).round(2) if variable != "pr" else (field * delta).round(0),
        value_key="delta",
    )

    return {
        "module": "climate",
        "product": "projection",
        "source": "demo",
        "scenario": scenario,
        "variable": variable,
        "variable_label": meta["label"],
        "unit": meta["unit"],
        "horizon": horizon,
        "model": model,
        "baseline": round(baseline_val, 2),
        "projected": round(projected_val, 2),
        "delta": round(delta, 2),
        "pct_change": round(pct, 1),
        "timeseries": [{"year": y, "value": v} for y, v in zip(years, series)],
        "tile_url": None,
        "grid": anomaly_grid,
        "legend": tiles.build_legend(meta["ramp"], ["Low", "", "Mid", "", "High"]),
        "aoi": {"bbox": bbox, "centroid": norm["centroid"]},
    }


def _projection_live(norm, scenario, variable, horizon, model) -> dict[str, Any]:  # pragma: no cover
    ee = gee.get_ee()
    geom = aoi_mod.to_ee_geometry(norm)
    meta = VARIABLES[variable]
    h0, h1 = HORIZONS[horizon]

    # NASA/GDDP-CMIP6 is daily across ~35 models. Averaging ALL of them over 20 yr
    # times out a synchronous request, so use a small curated multi-model ensemble
    # over 10-year windows — more robust than a single model (Mishra 2021), still
    # responsive. period_mean's .mean() averages across both models and days.
    base0, base1 = 2005, 2014  # representative recent-baseline decade
    src = ee.ImageCollection("NASA/GDDP-CMIP6")
    if model == "ensemble":
        coll = src.filter(ee.Filter.inList("model", ENSEMBLE_MODELS))
        model_label = f"{len(ENSEMBLE_MODELS)}-model ensemble"
    else:
        coll = src.filter(ee.Filter.eq("model", model))
        model_label = model

    # NOTE: intentionally NOT clipped — the coarse means feed the change factor,
    # which is resampled onto the fine baseline; clipping to a sub-cell AOI would
    # mask the neighbouring CMIP6 cells the bilinear resample needs.
    def period_mean(scen, y0, y1):
        img = (
            coll.filter(ee.Filter.eq("scenario", scen))
            .filter(ee.Filter.calendarRange(y0, y1, "year"))
            .select(variable)
            .mean()
        )
        if variable == "pr":
            img = img.multiply(86400 * 365)  # kg/m²/s -> mm/yr
        else:
            img = img.subtract(273.15)  # K -> °C
        return img.rename(variable)

    base_c = period_mean("historical", base0, base1)   # coarse 0.25° CMIP6 means
    proj_c = period_mean(scenario, h0, h1)

    # Change-factor (delta) downscaling: carry the coarse CMIP6 change signal onto
    # WorldClim's observed ~1 km climatology — multiplicative for precipitation,
    # additive for temperature. Yields a genuinely ~1 km projected field that is
    # bias-corrected against the observed baseline, not just an interpolated cell.
    wc = ee.ImageCollection("WORLDCLIM/V1/MONTHLY")
    if variable == "pr":
        wc_base = wc.select("prec").sum().rename(variable)               # mm/yr @ ~1 km
        factor = proj_c.divide(base_c.max(1)).resample("bilinear")       # P_fut/P_hist
        proj_fine = wc_base.multiply(factor).rename(variable)
    else:
        band = "tmax" if variable == "tasmax" else "tavg"
        wc_base = wc.select(band).mean().multiply(0.1).rename(variable)  # °C @ ~1 km
        diff = proj_c.subtract(base_c).resample("bilinear")              # T_fut - T_hist
        proj_fine = wc_base.add(diff).rename(variable)

    # One getInfo: observed baseline mean, downscaled projected mean, and a 2–98
    # percentile range over the AOI for the map colour scale.
    def _mean(img):
        return img.reduceRegion(ee.Reducer.mean(), geom, 1000, maxPixels=1e9,
                                bestEffort=True, tileScale=4).values().get(0)

    pcts = proj_fine.reduceRegion(ee.Reducer.percentile([2, 98]), geom, 1000,
                                  maxPixels=1e9, bestEffort=True, tileScale=4)
    out = ee.Dictionary({"base": _mean(wc_base), "proj": _mean(proj_fine),
                         "lo": pcts.values().get(0), "hi": pcts.values().get(1)}).getInfo()
    baseline_val = float(out.get("base") or 0)
    projected_val = float(out.get("proj") or 0)
    delta = projected_val - baseline_val

    lo, hi = out.get("lo"), out.get("hi")
    if lo is None or hi is None or hi <= lo:  # fallback colour range
        if variable == "pr":
            lo, hi = 0.0, (max(baseline_val, projected_val) * 1.3) or 1.0
        else:
            lo, hi = min(baseline_val, projected_val) - 1, max(baseline_val, projected_val) + 1
    vis = {"min": round(float(lo), 2), "max": round(float(hi), 2),
           "palette": tiles.RAMPS[meta["ramp"]]}
    # The ~1 km projected field, bilinear-smoothed and bounded to the AOI.
    tile_url = tiles.image_tile_url(proj_fine.clip(geom.buffer(2000)), vis)

    # QDM-style extreme diagnostic (precip only): change in the 95th percentile of
    # daily rainfall — heavy precip intensifies faster than the mean (Clausius-
    # Clapeyron). Single model + own getInfo, isolated so it can't break the map.
    extreme_pct = None
    if variable == "pr":
        try:
            em = ENSEMBLE_MODELS[0]

            def _p95(scen, y0, y1):
                d = (src.filter(ee.Filter.eq("model", em))
                     .filter(ee.Filter.eq("scenario", scen))
                     .filter(ee.Filter.calendarRange(y0, y1, "year"))
                     .select("pr").reduce(ee.Reducer.percentile([95])).multiply(86400))  # mm/day
                return ee.Number(d.reduceRegion(ee.Reducer.mean(), geom, 27830,
                                 maxPixels=1e9, bestEffort=True, tileScale=4).values().get(0))

            ex = ee.Dictionary({"b": _p95("historical", base0, base1),
                                "f": _p95(scenario, h0, h1)}).getInfo()
            if ex.get("b"):
                extreme_pct = round((ex["f"] - ex["b"]) / ex["b"] * 100, 1)
        except Exception:  # pragma: no cover  — diagnostic is optional
            extreme_pct = None

    # Trajectory for the result/chat curve: interpolate between the two real
    # decade-mean endpoints (baseline -> horizon). A trend line, not per-year obs.
    ts_years = list(range((base0 + base1) // 2, h1 + 1))
    _n = max(len(ts_years) - 1, 1)
    timeseries = [
        {"year": y, "value": round(baseline_val + (projected_val - baseline_val) * i / _n, 2)}
        for i, y in enumerate(ts_years)
    ]

    return {
        "module": "climate",
        "product": "projection",
        "source": "live",
        "scenario": scenario,
        "variable": variable,
        "variable_label": meta["label"],
        "unit": meta["unit"],
        "horizon": horizon,
        "model": model_label,
        "baseline": round(baseline_val, 2),
        "projected": round(projected_val, 2),
        "delta": round(delta, 2),
        "pct_change": round(delta / max(abs(baseline_val), 1e-6) * 100, 1),
        "extreme_precip_change_pct": extreme_pct,  # Δ in daily-rainfall 95th pct
        "baseline_period": f"{base0}-{base1}",
        "timeseries": timeseries,
        "tile_url": tile_url,
        "grid": None,
        "legend": tiles.build_legend(meta["ramp"], ["Low", "", "Mid", "", "High"]),
        "downscaled": True,
        "downscale_method": "multi-model ensemble change-factor downscaling onto WorldClim ~1 km",
        "baseline_source": "WorldClim V1 observed climatology (~1 km)",
        "native_resolution": "~1 km (from 0.25° CMIP6 NEX-GDDP)",
        "aoi": {"bbox": norm["bbox"], "centroid": norm["centroid"]},
    }


def anomaly(aoi, scenario="ssp585", variable="pr", horizon="2050s") -> dict[str, Any]:
    """Anomaly map convenience wrapper (delta grid only)."""
    res = projection(aoi, scenario, variable, horizon)
    res["product"] = "anomaly"
    return res


# --------------------------------------------------------------------------- #
# ETCCDI climate-extreme indices (Zhang et al., 2011)
# --------------------------------------------------------------------------- #
EXTREME_INDICES = {
    "rx1day": {"label": "Max 1-day precipitation", "unit": "mm", "kind": "precip"},
    "r95p": {"label": "Very-wet-day precip (>95th pct)", "unit": "mm", "kind": "precip"},
    "cdd": {"label": "Consecutive dry days", "unit": "days", "kind": "dry"},
    "hot_days": {"label": "Hot days (Tmax > 35°C)", "unit": "days/yr", "kind": "heat"},
}
_HORIZON_FACTOR = {"2030s": 0.4, "2050s": 0.7, "2080s": 1.0}


def extremes(aoi, scenario="ssp585", horizon="2050s", model="ensemble") -> dict[str, Any]:
    """ETCCDI extreme-climate indices (Zhang et al., 2011), estimated by scaling
    latitude-based baselines with the CMIP6 mean-change signal. Extremes intensify
    faster than the mean (Clausius-Clapeyron ~7%/°C for heavy precip), captured by
    an amplification factor. Deterministic; full daily ETCCDI is on the roadmap."""
    import numpy as np

    norm = aoi_mod.normalize(aoi, aoi_mod.COARSE_MAX_AREA_KM2)  # CMIP6 is regional-scale
    if scenario not in SCENARIOS:
        scenario = "ssp585"
    if horizon not in HORIZONS:
        horizon = "2050s"
    lat = abs(norm["centroid"][1])
    hf = _HORIZON_FACTOR[horizon]
    warming = _SIGNAL[scenario]["tas"] * hf  # °C
    wetting = _SIGNAL[scenario]["pr"] * hf   # fractional change in mean precip

    base = {
        "rx1day": float(np.interp(lat, [0, 15, 30, 45], [165, 110, 75, 55])),
        "r95p": float(np.interp(lat, [0, 15, 30, 45], [720, 460, 290, 180])),
        "cdd": float(np.interp(lat, [0, 15, 30, 45], [35, 70, 110, 150])),
        "hot_days": float(np.interp(lat, [0, 15, 30, 45], [150, 105, 60, 18])),
    }

    indices = []
    for key, meta in EXTREME_INDICES.items():
        b = base[key]
        if meta["kind"] == "precip":
            proj = b * (1 + wetting * 1.8)        # heavy precip amplifies vs. mean
        elif meta["kind"] == "dry":
            proj = b * (1 + 0.05 + warming * 0.02)  # longer dry spells in a warmer climate
        else:  # heat
            proj = b + warming * 9.0               # ~9 extra hot days per °C (mid-latitude est.)
        delta = proj - b
        indices.append({
            "key": key, "label": meta["label"], "unit": meta["unit"],
            "baseline": round(b, 1), "projected": round(proj, 1),
            "delta": round(delta, 1),
            "pct_change": round(delta / max(b, 1e-6) * 100, 1),
        })

    return {
        "module": "climate",
        "product": "extremes",
        "source": gee.mode(),
        "scenario": scenario,
        "horizon": horizon,
        "model": model,
        "indices": indices,
        "reference": "ETCCDI indices (Zhang et al., 2011); CMIP6 mean-change scaling",
        "aoi": {"bbox": norm["bbox"], "centroid": norm["centroid"]},
    }
