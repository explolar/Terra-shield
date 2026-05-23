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
    norm = aoi_mod.normalize(aoi)
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

    coll = ee.ImageCollection("NASA/GDDP-CMIP6")
    if model != "ensemble":
        coll = coll.filter(ee.Filter.eq("model", model))

    def period_mean(scen, y0, y1):
        c = (
            coll.filter(ee.Filter.eq("scenario", scen))
            .filter(ee.Filter.calendarRange(y0, y1, "year"))
            .select(variable)
        )
        img = c.mean().clip(geom)
        if variable == "pr":
            img = img.multiply(86400 * 365)  # kg/m²/s -> mm/yr
        else:
            img = img.subtract(273.15)  # K -> °C
        return img

    base_img = period_mean("historical", BASELINE[0], BASELINE[1])
    proj_img = period_mean(scenario, h0, h1)
    delta_img = proj_img.subtract(base_img).rename("delta")

    def region_mean(img, band):
        return ee.Number(
            img.reduceRegion(reducer=ee.Reducer.mean(), geometry=geom, scale=25000,
                             maxPixels=1e9, bestEffort=True).get(band)
        ).getInfo()

    baseline_val = region_mean(base_img, variable)
    projected_val = region_mean(proj_img, variable)
    delta = projected_val - baseline_val

    vis = {"min": -abs(delta) * 2 or -1, "max": abs(delta) * 2 or 1,
           "palette": tiles.RAMPS[meta["ramp"]]}
    tile_url = tiles.image_tile_url(delta_img, vis)

    return {
        "module": "climate",
        "product": "projection",
        "source": "live",
        "scenario": scenario,
        "variable": variable,
        "variable_label": meta["label"],
        "unit": meta["unit"],
        "horizon": horizon,
        "model": model,
        "baseline": round(baseline_val, 2),
        "projected": round(projected_val, 2),
        "delta": round(delta, 2),
        "pct_change": round(delta / max(abs(baseline_val), 1e-6) * 100, 1),
        "timeseries": [],  # served separately on the live path
        "tile_url": tile_url,
        "grid": None,
        "legend": tiles.build_legend(meta["ramp"], ["Low", "", "Mid", "", "High"]),
        "aoi": {"bbox": norm["bbox"], "centroid": norm["centroid"]},
    }


def anomaly(aoi, scenario="ssp585", variable="pr", horizon="2050s") -> dict[str, Any]:
    """Anomaly map convenience wrapper (delta grid only)."""
    res = projection(aoi, scenario, variable, horizon)
    res["product"] = "anomaly"
    return res
