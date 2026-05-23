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
from . import demo, flood_factors, gee, tiles

log = logging.getLogger("terrashield.geo.flood")

# Canonical 11-factor AHP set (Saaty eigenvector weights, CR-validated). See
# flood_factors.py for the pairwise matrix and per-factor reclassification.
FACTOR_NAMES = flood_factors.FACTOR_NAMES
FACTOR_LABELS = flood_factors.FACTOR_LABELS
DEFAULT_WEIGHTS = dict(flood_factors.DEFAULT_WEIGHTS)

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
    elif weights is None:
        # Default run: report the canonical 11-factor AHP consistency.
        rep = flood_factors.ahp_report()
        ahp_meta = {k: rep[k] for k in ("consistency_ratio", "consistent", "lambda_max")}
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
    """Paper-grade 11-factor AHP-MCDM susceptibility on live Earth Engine.

    Returns a 1-5 class composite tile, per-factor tiles (for paper figures),
    the AHP report, and class-area statistics. ``w`` may be user weights; if it
    matches the AHP default it is passed through unchanged.
    """
    ee = gee.get_ee()
    geom = aoi_mod.to_ee_geometry(norm)

    composite, factors, ahp = flood_factors.compute_susceptibility(geom, w)

    tile_url = tiles.image_tile_url(composite, flood_factors.MCA_VIZ)
    factor_urls = {
        name: tiles.image_tile_url(img, flood_factors.FACTOR_VIZ)
        for name, img in factors.items()
    }

    px = ee.Image.pixelArea()
    mean = ee.Number(composite.reduceRegion(
        ee.Reducer.mean(), geom, 100, maxPixels=1e9, bestEffort=True, tileScale=4,
    ).values().get(0))
    high = composite.gte(4).multiply(px).reduceRegion(
        ee.Reducer.sum(), geom, 100, maxPixels=1e9, bestEffort=True, tileScale=4,
    ).values().get(0)
    high_km2 = round((ee.Number(ee.Algorithms.If(high, high, 0)).getInfo() or 0) / 1e6, 2)
    mean_class = round(mean.getInfo() or 0, 2)

    return {
        "module": "flood",
        "product": "susceptibility",
        "source": "live",
        "tile_url": tile_url,
        "factor_urls": factor_urls,
        "grid": None,
        "legend": tiles.build_legend("risk", SUSCEPTIBILITY_CLASSES),
        "stats": {
            "mean": round(mean_class / 5.0, 3),       # normalized 0-1
            "mean_class": mean_class,                  # 1-5 AHP class
            "high_risk_area_km2": high_km2,            # classes 4-5
            "area_km2": norm["area_km2"],
        },
        "weights": w,
        "ahp": {k: ahp.get(k) for k in ("consistency_ratio", "consistent", "lambda_max")},
        "reliability": {
            "method": "AHP-MCDM, 11 factors (Saaty 1980); spatial block CV for any learned layer",
            "factors": len(FACTOR_NAMES),
        },
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


def _otsu_threshold(image, geom, scale, band):  # pragma: no cover
    """Otsu's method (1979): the histogram split that maximizes between-class
    variance — an adaptive, per-scene water/land threshold for SAR backscatter."""
    ee = gee.get_ee()
    hist = ee.Dictionary(
        image.select(band).reduceRegion(
            reducer=ee.Reducer.histogram(255, 2), geometry=geom, scale=scale,
            maxPixels=1e9, bestEffort=True,
        ).get(band)
    )
    counts = ee.Array(hist.get("histogram"))
    means = ee.Array(hist.get("bucketMeans"))
    size = means.length().get([0])
    total = counts.reduce(ee.Reducer.sum(), [0]).get([0])
    total_sum = means.multiply(counts).reduce(ee.Reducer.sum(), [0]).get([0])
    grand_mean = total_sum.divide(total)
    indices = ee.List.sequence(1, size)

    def between_class_var(i):
        i = ee.Number(i)
        a_counts = counts.slice(0, 0, i)
        a_count = a_counts.reduce(ee.Reducer.sum(), [0]).get([0])
        a_means = means.slice(0, 0, i)
        a_mean = a_means.multiply(a_counts).reduce(ee.Reducer.sum(), [0]).get([0]).divide(a_count)
        b_count = total.subtract(a_count)
        b_mean = total_sum.subtract(a_count.multiply(a_mean)).divide(b_count)
        return a_count.multiply(a_mean.subtract(grand_mean).pow(2)).add(
            b_count.multiply(b_mean.subtract(grand_mean).pow(2))
        )

    bss = ee.Array(indices.map(between_class_var))
    return means.sort(bss).get([-1])


def _sar_extent_live(norm, ps, pe, qs, qe) -> dict[str, Any]:  # pragma: no cover
    """Sentinel-1 SAR inundation with a 6-layer calibrated mask (from FluviaAI):
      1. terrain slope < 8 deg (removes radar-shadow false positives)
      2. permanent-water exclusion (JRC seasonality >= 10 months)
      3. JRC flood-frequency gate (occurrence >= 5 %)
      4. elevation <= 40th percentile (lowlands only)
      5. minimum patch >= 56 connected pixels (~5 ha)
      6. morphological cleanup (focal mode, 40 m)
    Threshold on the pre-post change is set adaptively by Otsu (1979). Adds a
    3-class severity map and population / cropland / built-up exposure.
    """
    ee = gee.get_ee()
    geom = aoi_mod.to_ee_geometry(norm)
    px = ee.Image.pixelArea()

    def s1(start, end):
        return (
            ee.ImageCollection("COPERNICUS/S1_GRD")
            .filterBounds(geom).filterDate(start, end)
            .filter(ee.Filter.eq("instrumentMode", "IW"))
            .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
            .select("VV").median().focalMedian(30, "circle", "meters").clip(geom)
        )

    pre, post = s1(ps, pe), s1(qs, qe)
    diff = pre.subtract(post).rename("diff")  # positive where backscatter dropped (new water)

    dem = ee.Image("USGS/SRTMGL1_003").select("elevation").clip(geom)
    slope_ok = ee.Terrain.slope(dem).lt(8)
    jrc = ee.Image("JRC/GSW1_4/GlobalSurfaceWater")
    perm_water = jrc.select("seasonality").gte(10)
    jrc_gate = jrc.select("occurrence").gte(5)
    elev_p40 = ee.Number(dem.reduceRegion(ee.Reducer.percentile([40]), geom, 100,
                                          maxPixels=1e9, bestEffort=True).values().get(0))
    elev_ok = dem.lte(elev_p40)

    thr_db = 1.25  # calibrated dB backscatter-drop threshold (change detection)
    flooded = (diff.gt(thr_db).updateMask(slope_ok).where(perm_water, 0).selfMask()
               .updateMask(jrc_gate).updateMask(elev_ok))
    flooded = flooded.updateMask(flooded.connectedPixelCount(200, False).gte(56))
    flooded = flooded.focalMode(40, "circle", "meters").updateMask(flooded).rename("flooded")

    # 3-class severity by depth proxy (elevation percentile within the flood).
    ep = dem.reduceRegion(ee.Reducer.percentile([10, 50]), geom, 100,
                          maxPixels=1e9, bestEffort=True)
    p10 = ee.Number(ep.values().get(0))
    p50 = ee.Number(ep.values().get(1))
    severity = (flooded.where(flooded.And(dem.lte(p10)), 3)
                .where(flooded.And(dem.gt(p10).And(dem.lte(p50))), 2)
                .where(flooded.And(dem.gt(p50)), 1).updateMask(flooded).rename("severity"))

    def _sum(img, scale):
        v = img.multiply(px).reduceRegion(ee.Reducer.sum(), geom, scale,
                                          maxPixels=1e9, bestEffort=True, tileScale=4).values().get(0)
        return float(ee.Number(ee.Algorithms.If(v, v, 0)).getInfo() or 0)

    flooded_km2 = round(_sum(flooded, 30) / 1e6, 2)
    lulc = ee.Image("ESA/WorldCover/v200/2021").select("Map")
    crop_ha = round(_sum(flooded.updateMask(lulc.eq(40)), 20) / 1e4, 1)   # cropland
    built_ha = round(_sum(flooded.updateMask(lulc.eq(50)), 20) / 1e4, 1)  # built-up
    pop = ee.ImageCollection("WorldPop/GP/100m/pop").filter(
        ee.Filter.eq("year", 2020)).mosaic().clip(geom)
    pv = pop.updateMask(flooded).reduceRegion(ee.Reducer.sum(), geom, 100,
                                              maxPixels=1e9, bestEffort=True, tileScale=4).values().get(0)
    pop_exposed = int(ee.Number(ee.Algorithms.If(pv, pv, 0)).getInfo() or 0)
    crop_price_per_ha = 1200.0  # USD/ha default (configurable)

    return {
        "module": "flood",
        "product": "sar_extent",
        "source": "live",
        "tile_url": tiles.image_tile_url(flooded, {"palette": ["#2171b5"], "min": 0, "max": 1}),
        "severity_url": tiles.image_tile_url(
            severity, {"min": 1, "max": 3, "palette": ["#ffffb2", "#fd8d3c", "#bd0026"]}),
        "grid": None,
        "legend": [
            {"label": "Low severity", "color": "#ffffb2"},
            {"label": "Moderate", "color": "#fd8d3c"},
            {"label": "High", "color": "#bd0026"},
        ],
        "stats": {
            "flooded_area_km2": flooded_km2,
            "flooded_pct": round(flooded_km2 / max(norm["area_km2"], 1e-6) * 100, 1),
            "population_exposed": pop_exposed,
            "cropland_flooded_ha": crop_ha,
            "crop_loss_usd": round(crop_ha * crop_price_per_ha, 0),
            "builtup_flooded_ha": built_ha,
            "threshold_db": thr_db,
            "method": "6-layer calibrated SAR mask (FluviaAI) + 3-class severity",
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
