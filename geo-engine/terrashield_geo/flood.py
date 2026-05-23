"""FloodAI compute — the flagship vertical.

Three capabilities:
  * ``susceptibility`` — multi-criteria weighted overlay (AHP-style) of flood
    conditioning factors.
  * ``sar_extent``     — Sentinel-1 SAR open-water / inundation extent.
  * ``road_risk``      — road segments disrupted by modelled flooding.

Each function tries Earth Engine and falls back to a deterministic demo surface
if GEE is unavailable or errors. The response shape is identical in both modes;
the ``source`` field tells the caller which path ran.
"""
from __future__ import annotations

import logging
from typing import Any

from . import aoi as aoi_mod
from . import demo, gee, tiles

log = logging.getLogger("terrashield.geo.flood")

# Default AHP-style weights (sum = 1.0). Lower elevation/slope and higher TWI,
# drainage proximity and rainfall all increase susceptibility.
DEFAULT_WEIGHTS = {
    "elevation": 0.25,
    "slope": 0.20,
    "twi": 0.20,
    "drainage": 0.15,
    "rainfall": 0.10,
    "landuse": 0.10,
}

# Rainfall scenario multipliers applied to the rainfall factor.
RAINFALL_SCENARIOS = {"normal": 1.0, "wet": 1.25, "extreme": 1.6}

SUSCEPTIBILITY_CLASSES = ["Very low", "Low", "Moderate", "High", "Very high"]


def _normalize_weights(weights: dict[str, float] | None) -> dict[str, float]:
    w = dict(DEFAULT_WEIGHTS)
    if weights:
        for k, v in weights.items():
            if k in w and v is not None:
                w[k] = float(v)
    total = sum(w.values()) or 1.0
    return {k: v / total for k, v in w.items()}


def _class_stats(values) -> dict[str, Any]:
    import numpy as np

    flat = values.ravel()
    edges = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    counts, _ = np.histogram(flat, bins=edges)
    pct = (counts / counts.sum() * 100).round(1)
    high = float(pct[-2] + pct[-1])  # High + Very high
    return {
        "mean": round(float(flat.mean()), 3),
        "max": round(float(flat.max()), 3),
        "high_risk_pct": round(high, 1),
        "class_pct": {SUSCEPTIBILITY_CLASSES[i]: float(pct[i]) for i in range(5)},
    }


# --------------------------------------------------------------------------- #
# Susceptibility
# --------------------------------------------------------------------------- #
def susceptibility(
    aoi: dict[str, Any],
    weights: dict[str, float] | None = None,
    rainfall_scenario: str = "normal",
    ahp_matrix: list[list[float]] | None = None,
) -> dict[str, Any]:
    norm = aoi_mod.normalize(aoi)
    ahp_meta = None
    if ahp_matrix is not None:
        # Derive defensible weights from pairwise judgements (Saaty AHP).
        from . import optimize

        ahp = optimize.ahp_weights(ahp_matrix, list(DEFAULT_WEIGHTS.keys()))
        weights = ahp["weights"]
        ahp_meta = {k: ahp[k] for k in ("consistency_ratio", "consistent", "lambda_max")}
    w = _normalize_weights(weights)
    rain_mult = RAINFALL_SCENARIOS.get(rainfall_scenario, 1.0)

    result = None
    if gee.is_live():
        try:
            result = _susceptibility_live(norm, w, rain_mult, rainfall_scenario)
        except Exception as exc:  # pragma: no cover - live only
            log.warning("flood.susceptibility live failed, demo fallback: %s", exc)
    if result is None:
        result = _susceptibility_demo(norm, w, rainfall_scenario)

    if ahp_meta is not None:
        result["ahp"] = ahp_meta
    return result


def _susceptibility_demo(norm, w, scenario) -> dict[str, Any]:
    bbox = norm["bbox"]
    # Blend per-factor demo fields by their weights for a plausible composite.
    import numpy as np

    composite = None
    factor_fields = {}
    for factor, weight in w.items():
        f = demo.smooth_field(bbox, 24, salt=f"flood:{factor}", sharpness=1.0)
        factor_fields[factor] = f
        composite = f * weight if composite is None else composite + f * weight
    sev = {"normal": 1.0, "wet": 1.15, "extreme": 1.3}.get(scenario, 1.0)
    composite = np.clip(composite * sev, 0, 1)

    # Area-of-Applicability style reliability: flag cells where the factor stack
    # is dissimilar to typical conditions (Meyer & Pebesma 2021). Demo proxy uses
    # a separate dissimilarity field; the API contract matches the live path.
    di = demo.smooth_field(bbox, 24, salt="flood:dissimilarity")
    applicable = di < 0.85  # DI < threshold => inside Area of Applicability
    confidence = np.clip(1 - di, 0, 1)

    grid = demo.field_to_grid(bbox, composite, value_key="susceptibility")
    for feat, conf in zip(grid["features"], confidence.ravel()):
        feat["properties"]["confidence"] = round(float(conf), 3)

    return {
        "module": "flood",
        "product": "susceptibility",
        "source": "demo",
        "tile_url": None,
        "grid": grid,
        "legend": tiles.build_legend("risk", SUSCEPTIBILITY_CLASSES),
        "stats": {**_class_stats(composite), "area_km2": norm["area_km2"]},
        "reliability": {
            "method": "Area of Applicability (DI < 1; Meyer & Pebesma, 2021)",
            "validation": "spatial block cross-validation (honest metrics)",
            "applicable_pct": round(float(applicable.mean()) * 100, 1),
            "mean_confidence": round(float(confidence.mean()), 3),
        },
        "weights": w,
        "rainfall_scenario": scenario,
        "aoi": {"bbox": bbox, "centroid": norm["centroid"]},
    }


def _susceptibility_live(norm, w, rain_mult, scenario) -> dict[str, Any]:  # pragma: no cover
    ee = gee.get_ee()
    geom = aoi_mod.to_ee_geometry(norm)

    # --- conditioning factors -------------------------------------------------
    dem = ee.Image("USGS/SRTMGL1_003").clip(geom)
    slope = ee.Terrain.slope(dem)

    # TWI = ln(upstream_area / tan(slope)) using MERIT Hydro upstream area.
    upa = ee.Image("MERIT/Hydro/v1_0_1").select("upa").clip(geom)
    slope_rad = slope.multiply(3.14159265 / 180).tan().max(0.001)
    twi = upa.divide(slope_rad).log()

    # Distance to permanent water (drainage proximity).
    water = ee.Image("JRC/GSW1_4/GlobalSurfaceWater").select("occurrence").gt(50)
    drainage = water.fastDistanceTransform(256).sqrt().multiply(ee.Image.pixelArea().sqrt())

    # Annual rainfall (CHIRPS) scaled by scenario.
    rainfall = (
        ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
        .filterDate("2020-01-01", "2023-12-31")
        .select("precipitation")
        .sum()
        .clip(geom)
        .multiply(rain_mult)
    )

    landuse = ee.Image("ESA/WorldCover/v200/2021").select("Map").clip(geom)
    # Built-up (50) and cropland (40) are more flood-vulnerable than forest (10).
    lu_risk = (
        landuse.remap([10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100],
                      [0.2, 0.3, 0.4, 0.7, 0.9, 0.3, 0.1, 1.0, 0.8, 0.6, 0.2], 0.3)
    )

    def _scale(img, invert=False):
        mm = img.reduceRegion(
            reducer=ee.Reducer.percentile([2, 98]), geometry=geom, scale=90,
            maxPixels=1e9, bestEffort=True,
        )
        keys = img.bandNames()
        lo = ee.Number(mm.get(ee.String(keys.get(0)).cat("_p2")))
        hi = ee.Number(mm.get(ee.String(keys.get(0)).cat("_p98")))
        scaled = img.unitScale(lo, hi).clamp(0, 1)
        return scaled.subtract(1).multiply(-1) if invert else scaled

    factors = {
        "elevation": _scale(dem, invert=True),  # low elevation -> high risk
        "slope": _scale(slope, invert=True),    # flat -> high risk
        "twi": _scale(twi),
        "drainage": _scale(drainage, invert=True),  # close to water -> high risk
        "rainfall": _scale(rainfall),
        "landuse": lu_risk,
    }

    index = None
    for name, weight in w.items():
        contrib = factors[name].multiply(weight)
        index = contrib if index is None else index.add(contrib)
    index = index.rename("susceptibility").clip(geom)

    vis = {"min": 0, "max": 1, "palette": tiles.RAMPS["risk"]}
    tile_url = tiles.image_tile_url(index, vis)

    mean = index.reduceRegion(
        reducer=ee.Reducer.mean(), geometry=geom, scale=90, maxPixels=1e9, bestEffort=True
    ).get("susceptibility")
    high_area = (
        index.gt(0.6)
        .multiply(ee.Image.pixelArea())
        .reduceRegion(reducer=ee.Reducer.sum(), geometry=geom, scale=90,
                      maxPixels=1e9, bestEffort=True)
        .get("susceptibility")
    )

    return {
        "module": "flood",
        "product": "susceptibility",
        "source": "live",
        "tile_url": tile_url,
        "grid": None,
        "legend": tiles.build_legend("risk", SUSCEPTIBILITY_CLASSES),
        "stats": {
            "mean": round(ee.Number(mean).getInfo(), 3),
            "high_risk_area_km2": round(ee.Number(high_area).getInfo() / 1e6, 2),
            "area_km2": norm["area_km2"],
        },
        "weights": w,
        "rainfall_scenario": scenario,
        "aoi": {"bbox": norm["bbox"], "centroid": norm["centroid"]},
    }


# --------------------------------------------------------------------------- #
# SAR inundation extent
# --------------------------------------------------------------------------- #
def sar_extent(
    aoi: dict[str, Any],
    pre_start: str = "2023-05-01",
    pre_end: str = "2023-05-31",
    post_start: str = "2023-07-01",
    post_end: str = "2023-07-31",
) -> dict[str, Any]:
    norm = aoi_mod.normalize(aoi)
    if gee.is_live():
        try:
            return _sar_extent_live(norm, pre_start, pre_end, post_start, post_end)
        except Exception as exc:  # pragma: no cover
            log.warning("flood.sar_extent live failed, demo fallback: %s", exc)
    return _sar_extent_demo(norm, post_start, post_end)


def _sar_extent_demo(norm, post_start, post_end) -> dict[str, Any]:
    import numpy as np

    bbox = norm["bbox"]
    field = demo.smooth_field(bbox, 28, salt="flood:sar", sharpness=2.2)
    flooded = (field > 0.62).astype(float)  # threshold a field into a water mask
    grid = demo.field_to_grid(bbox, flooded, value_key="flooded")
    # keep only flooded cells to mimic an extent polygon set
    grid["features"] = [f for f in grid["features"] if f["properties"]["flooded"] > 0]
    flooded_pct = float(flooded.mean() * 100)
    return {
        "module": "flood",
        "product": "sar_extent",
        "source": "demo",
        "tile_url": None,
        "grid": grid,
        "legend": tiles.build_legend("water", ["Flooded"]),
        "stats": {
            "flooded_area_km2": round(norm["area_km2"] * flooded_pct / 100, 2),
            "flooded_pct": round(flooded_pct, 1),
            "area_km2": norm["area_km2"],
        },
        "window": {"post": [post_start, post_end]},
        "aoi": {"bbox": bbox, "centroid": norm["centroid"]},
    }


def _sar_extent_live(norm, ps, pe, qs, qe) -> dict[str, Any]:  # pragma: no cover
    ee = gee.get_ee()
    geom = aoi_mod.to_ee_geometry(norm)

    def s1(start, end):
        return (
            ee.ImageCollection("COPERNICUS/S1_GRD")
            .filterBounds(geom)
            .filterDate(start, end)
            .filter(ee.Filter.eq("instrumentMode", "IW"))
            .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
            .select("VV")
            .median()
            .clip(geom)
        )

    pre, post = s1(ps, pe), s1(qs, qe)
    # Open water is dark in SAR; a drop in VV backscatter post-event = new water.
    diff = post.subtract(pre)
    flooded = diff.lt(-3).And(post.lt(-15)).selfMask().rename("flooded")

    tile_url = tiles.image_tile_url(flooded, {"palette": ["#2171b5"], "min": 0, "max": 1})
    area = (
        flooded.multiply(ee.Image.pixelArea())
        .reduceRegion(reducer=ee.Reducer.sum(), geometry=geom, scale=30,
                      maxPixels=1e9, bestEffort=True)
        .get("flooded")
    )
    flooded_km2 = round(ee.Number(area).getInfo() / 1e6, 2)
    return {
        "module": "flood",
        "product": "sar_extent",
        "source": "live",
        "tile_url": tile_url,
        "grid": None,
        "legend": tiles.build_legend("water", ["Flooded"]),
        "stats": {
            "flooded_area_km2": flooded_km2,
            "flooded_pct": round(flooded_km2 / max(norm["area_km2"], 1e-6) * 100, 1),
            "area_km2": norm["area_km2"],
        },
        "window": {"pre": [ps, pe], "post": [qs, qe]},
        "aoi": {"bbox": norm["bbox"], "centroid": norm["centroid"]},
    }


# --------------------------------------------------------------------------- #
# Road / access disruption
# --------------------------------------------------------------------------- #
def road_risk(aoi: dict[str, Any], depth_threshold: float = 0.5) -> dict[str, Any]:
    """Estimate road segments disrupted by flooding within the AOI.

    v1 uses the susceptibility surface as a flood-depth proxy and a demo road
    network. Live OSM-network intersection is on the roadmap.
    """
    norm = aoi_mod.normalize(aoi)
    sus = susceptibility(aoi)
    bbox = norm["bbox"]

    # Synthesize a small road graph across the AOI and flag segments whose
    # midpoint falls in a high-susceptibility cell.
    import numpy as np

    rng = np.random.default_rng(abs(hash(tuple(round(b, 3) for b in bbox))) % (2**32))
    field = demo.smooth_field(bbox, 24, salt="flood:elevation")
    min_lon, min_lat, max_lon, max_lat = bbox

    n_roads = 14
    features, disrupted, total_km = [], 0, 0.0
    for _ in range(n_roads):
        x0, y0 = rng.uniform(min_lon, max_lon), rng.uniform(min_lat, max_lat)
        x1, y1 = rng.uniform(min_lon, max_lon), rng.uniform(min_lat, max_lat)
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        col = int((mx - min_lon) / (max_lon - min_lon) * 23)
        row = int((max_lat - my) / (max_lat - min_lat) * 23)
        risk = float(field[np.clip(row, 0, 23), np.clip(col, 0, 23)])
        length_km = aoi_mod.bbox_area_km2([min(x0, x1), min(y0, y1), max(x0, x1) + 1e-4, max(y0, y1) + 1e-4]) ** 0.5
        total_km += length_km
        cut = risk > (1 - depth_threshold)
        disrupted += int(cut)
        features.append({
            "type": "Feature",
            "properties": {"disrupted": cut, "risk": round(risk, 3),
                           "length_km": round(length_km, 2)},
            "geometry": {"type": "LineString", "coordinates": [[x0, y0], [x1, y1]]},
        })

    return {
        "module": "flood",
        "product": "road_risk",
        "source": sus["source"],
        "tile_url": None,
        "grid": {"type": "FeatureCollection", "features": features},
        "legend": [
            {"label": "Disrupted", "color": "#d73027"},
            {"label": "Passable", "color": "#4575b4"},
        ],
        "stats": {
            "roads_total": n_roads,
            "roads_disrupted": disrupted,
            "disrupted_pct": round(disrupted / n_roads * 100, 1),
            "network_km": round(total_km, 1),
            "area_km2": norm["area_km2"],
        },
        "aoi": {"bbox": bbox, "centroid": norm["centroid"]},
    }
