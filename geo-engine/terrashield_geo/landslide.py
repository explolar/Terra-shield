"""LandslideAI — data-driven landslide susceptibility (NOT an AHP overlay).

A learned classifier (Random Forest / XGBoost / Gradient Boosting) trained on a
landslide inventory (presence) vs sampled absence over standard conditioning
factors. Reports F1 / precision / recall / ROC-AUC / accuracy under k-fold
cross-validation, SHAP feature importance, and a susceptibility probability map.

  * LIVE  — conditioning factors from GEE (SRTM terrain, TWI, distance-to-drainage,
            ESA WorldCover, CHIRPS rainfall, NDVI). Labels from a user landslide-
            inventory FeatureCollection (presence) + sampled pseudo-absence. Pass
            the Earth Engine asset id via ``inventory_asset``. The map is produced
            by an in-GEE RandomForest (probability) so it tiles like other layers.
  * DEMO  — deterministic synthetic factors + a slope/rainfall/TWI-driven label;
            trains a real sklearn model and predicts the grid.

References: Reichenbach et al. (2018) Earth-Sci. Rev. (landslide-susceptibility ML
review); Lundberg & Lee (2017) SHAP, NeurIPS.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

from . import aoi as aoi_mod
from . import demo, gee, tiles

log = logging.getLogger("terrashield.geo.landslide")

# Conditioning factors (order is the model's feature order).
FACTORS = ["slope", "elevation", "aspect", "curvature", "twi",
           "dist_river", "rainfall", "ndvi", "landcover"]
FACTOR_LABELS = {
    "slope": "Slope", "elevation": "Elevation", "aspect": "Aspect",
    "curvature": "Curvature", "twi": "Topographic Wetness Index",
    "dist_river": "Distance to drainage", "rainfall": "Rainfall",
    "ndvi": "NDVI (vegetation)", "landcover": "Land cover",
}
MODELS = ("random_forest", "xgboost", "gbm")

SUSCEPTIBILITY_CLASSES = [
    {"label": "Very low", "color": "#1a9850", "min": 0.0, "max": 0.2},
    {"label": "Low", "color": "#91cf60", "min": 0.2, "max": 0.4},
    {"label": "Moderate", "color": "#fee08b", "min": 0.4, "max": 0.6},
    {"label": "High", "color": "#fc8d59", "min": 0.6, "max": 0.8},
    {"label": "Very high", "color": "#d73027", "min": 0.8, "max": 1.0},
]
_VIZ = {"min": 0, "max": 1,
        "palette": ["#1a9850", "#91cf60", "#fee08b", "#fc8d59", "#d73027"]}

# Bundled national landslide inventory (presence points, WGS84) — used as labels
# so the platform is self-contained (no manual GEE asset upload).
_INVENTORY_PATH = Path(__file__).parent / "data" / "landslide_inventory.json"
_INVENTORY: list[list[float]] | None = None


def _inventory() -> list[list[float]]:
    global _INVENTORY
    if _INVENTORY is None:
        try:
            _INVENTORY = json.loads(_INVENTORY_PATH.read_text())["points"]
        except Exception as exc:  # pragma: no cover
            log.warning("landslide inventory unavailable: %s", exc)
            _INVENTORY = []
    return _INVENTORY


def _inventory_in_bbox(bbox, cap: int = 4000) -> list[list[float]]:
    mnx, mny, mxx, mxy = bbox
    pts = [p for p in _inventory() if mnx <= p[0] <= mxx and mny <= p[1] <= mxy]
    if len(pts) > cap:  # subsample to keep the Earth Engine request reasonable
        pts = pts[:: len(pts) // cap + 1]
    return pts


def _presence_points(bbox, target: int = 30):
    """Inventory points around the AOI, expanding a buffer until there are enough
    to train a regional model. Returns (points, buffer_degrees)."""
    pts: list[list[float]] = []
    for buf in (0.0, 0.3, 0.6, 1.0):
        b = [bbox[0] - buf, bbox[1] - buf, bbox[2] + buf, bbox[3] + buf]
        pts = _inventory_in_bbox(b, cap=2500)
        if len(pts) >= target:
            return pts, buf
    return pts, 1.0


def _make_model(name: str):
    if name == "xgboost":
        try:
            from xgboost import XGBClassifier

            return XGBClassifier(n_estimators=300, max_depth=4, learning_rate=0.1,
                                 subsample=0.9, eval_metric="logloss", n_jobs=-1)
        except Exception:  # pragma: no cover
            name = "random_forest"
    if name == "gbm":
        from sklearn.ensemble import GradientBoostingClassifier

        return GradientBoostingClassifier(n_estimators=200, max_depth=3, random_state=42)
    from sklearn.ensemble import RandomForestClassifier

    return RandomForestClassifier(n_estimators=300, n_jobs=-1, random_state=42)


def _train(X: np.ndarray, y: np.ndarray, model_name: str):
    """Cross-validated metrics + fitted model + SHAP importance."""
    import shap
    from sklearn.model_selection import cross_validate

    if len(np.unique(y)) < 2:  # guard degenerate labels
        y = y.copy()
        y[: max(1, len(y) // 5)] = 1 - int(y[0])

    model = _make_model(model_name)
    n_splits = 5 if len(y) >= 50 else 3
    metrics: dict[str, Any] = {}
    try:
        cv = cross_validate(model, X, y, cv=n_splits,
                            scoring=["accuracy", "f1", "precision", "recall", "roc_auc"])

        def mean(k):
            v = cv.get(f"test_{k}")
            return round(float(np.nanmean(v)), 3) if v is not None else None

        metrics = {"f1": mean("f1"), "precision": mean("precision"),
                   "recall": mean("recall"), "roc_auc": mean("roc_auc"),
                   "accuracy": mean("accuracy")}
    except Exception as exc:  # pragma: no cover
        log.warning("landslide CV failed: %s", exc)

    model.fit(X, y)

    try:
        explainer = shap.TreeExplainer(model)
        sv = explainer.shap_values(X)
        if isinstance(sv, list):
            sv = sv[-1]
        mean_abs = np.abs(np.asarray(sv)).mean(axis=0).ravel()
    except Exception as exc:  # pragma: no cover
        log.warning("landslide SHAP failed (%s); using impurity importance", exc)
        mean_abs = np.asarray(getattr(model, "feature_importances_", np.ones(len(FACTORS))))

    total = float(mean_abs.sum()) or 1.0
    importance = sorted(
        [{"factor": FACTORS[i], "label": FACTOR_LABELS[FACTORS[i]],
          "importance": round(float(mean_abs[i] / total), 4)} for i in range(len(FACTORS))],
        key=lambda d: -d["importance"],
    )
    metrics["n_samples"] = int(len(y))
    metrics["positive_rate"] = round(float(y.mean()), 3)
    return metrics, model, importance


def _class_stats(prob: np.ndarray) -> dict[str, Any]:
    return {
        "mean_susceptibility": round(float(prob.mean()), 3),
        "high_susceptibility_pct": round(float((prob >= 0.6).mean()) * 100, 1),
    }


def susceptibility(aoi: dict[str, Any], model: str = "random_forest",
                   inventory_asset: str | None = None, n_samples: int = 1000) -> dict[str, Any]:
    norm = aoi_mod.normalize(aoi)
    if model not in MODELS:
        model = "random_forest"
    live_error = None
    if gee.is_live():
        try:
            return _susceptibility_live(norm, model, inventory_asset, n_samples)
        except Exception as exc:  # pragma: no cover
            live_error = f"{type(exc).__name__}: {exc}"
            log.warning("landslide live failed, demo fallback: %s", live_error)
    res = _susceptibility_demo(norm, model, n_samples)
    if live_error:
        res["live_error"] = live_error  # surfaced so a live failure is diagnosable
    return res


def _susceptibility_demo(norm, model_name, n_samples) -> dict[str, Any]:
    bbox = norm["bbox"]
    n = 24
    rng = np.random.default_rng(abs(hash(tuple(round(b, 3) for b in bbox))) % (2**32))
    fields = {name: demo.smooth_field(bbox, n, salt=f"landslide:{name}") for name in FACTORS}

    # Proxy "inventory" label: steep slope + high rainfall + high TWI, low vegetation.
    w = np.array([0.32, 0.05, 0.02, 0.10, 0.16, -0.06, 0.22, -0.10, 0.04])
    ii = rng.integers(0, n, size=n_samples)
    jj = rng.integers(0, n, size=n_samples)
    X = np.column_stack([fields[name][ii, jj] for name in FACTORS])
    score = X @ w + rng.normal(0, 0.08, n_samples)
    y = (score > np.quantile(score, 0.7)).astype(int)  # ~30% landslide presence

    metrics, fitted, importance = _train(X, y, model_name)
    full = np.column_stack([fields[name].ravel() for name in FACTORS])
    prob = fitted.predict_proba(full)[:, 1].reshape(n, n)
    grid = demo.field_to_grid(bbox, prob.round(3), value_key="susceptibility")

    return {
        "module": "landslide", "product": "susceptibility", "source": "demo",
        "model": model_name, "tile_url": None, "grid": grid,
        "legend": [{"label": c["label"], "color": c["color"]} for c in SUSCEPTIBILITY_CLASSES],
        "metrics": metrics, "feature_importance": importance,
        "top_factor": importance[0]["factor"],
        "explainability": "SHAP (Lundberg & Lee, 2017)",
        "validation": "stratified k-fold cross-validation",
        "inventory": "synthetic proxy (demo); live uses the national inventory",
        "stats": {**_class_stats(prob),
                  "inventory_points_in_aoi": len(_inventory_in_bbox(bbox)),
                  "area_km2": norm["area_km2"]},
        "aoi": {"bbox": bbox, "centroid": norm["centroid"]},
    }


def _factor_stack(ee, geom):  # pragma: no cover
    dem = ee.Image("USGS/SRTMGL1_003").clip(geom)
    terrain = ee.Terrain.products(dem)
    slope = terrain.select("slope").rename("slope")
    aspect = terrain.select("aspect").rename("aspect")
    elevation = dem.rename("elevation")
    curvature = dem.convolve(ee.Kernel.laplacian8()).rename("curvature")
    # TWI from a flow-accumulation proxy (MERIT upstream area / local slope).
    upa = ee.Image("MERIT/Hydro/v1_0_1").select("upa").clip(geom)
    twi = upa.add(1).log().divide(slope.multiply(3.14159 / 180).tan().add(0.01)).rename("twi")
    water = ee.Image("JRC/GSW1_4/GlobalSurfaceWater").select("occurrence").gt(20)
    dist_river = water.fastDistanceTransform(256).sqrt().rename("dist_river")
    rainfall = (ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
                .filterDate("2014-01-01", "2024-01-01").select("precipitation")
                .sum().divide(10).clip(geom).rename("rainfall"))
    ndvi = (ee.ImageCollection("MODIS/061/MOD13A2")
            .filterDate("2023-01-01", "2024-01-01").select("NDVI")
            .mean().multiply(0.0001).rename("ndvi"))
    landcover = ee.Image("ESA/WorldCover/v200/2021").select("Map").rename("landcover")
    return ee.Image.cat([slope, elevation, aspect, curvature, twi,
                         dist_river, rainfall, ndvi, landcover]).clip(geom)


def _susceptibility_live(norm, model_name, inventory_asset, n_samples) -> dict[str, Any]:  # pragma: no cover
    ee = gee.get_ee()
    geom = aoi_mod.to_ee_geometry(norm)

    # Presence labels: a user-supplied EE asset, else the bundled national
    # inventory. Sparse AOIs auto-expand a buffer so we still train a real
    # *regional* model and then predict susceptibility for the AOI.
    if inventory_asset:
        train_geom = geom
        presence = ee.FeatureCollection(inventory_asset).filterBounds(geom).map(
            lambda f: f.set("label", 1))
        n_pos = 500
        inv_label = inventory_asset
    else:
        pts, buf = _presence_points(norm["bbox"])
        if len(pts) < 10:
            raise ValueError(f"only {len(pts)} inventory points within {buf:g} deg of the AOI")
        bb = norm["bbox"]
        train_geom = ee.Geometry.Rectangle([bb[0] - buf, bb[1] - buf, bb[2] + buf, bb[3] + buf])
        presence = ee.FeatureCollection(
            [ee.Feature(ee.Geometry.Point(p), {"label": 1}) for p in pts])
        n_pos = len(pts)
        scope = "this AOI" if buf == 0 else f"a ~{buf:g} deg region"
        inv_label = f"national landslide inventory ({len(pts)} presence pts, {scope})"

    # Factor stack over the training region; pseudo-absence sampled there too.
    stack = _factor_stack(ee, train_geom)
    absence = ee.FeatureCollection.randomPoints(train_geom, max(n_pos, 50), 42).map(
        lambda f: f.set("label", 0))
    points = presence.merge(absence)

    samples = stack.sampleRegions(collection=points, properties=["label"], scale=30,
                                  tileScale=4, geometries=False).getInfo()
    rows, ys = [], []
    for f in samples.get("features", []):
        p = f["properties"]
        if all(p.get(k) is not None for k in FACTORS) and p.get("label") is not None:
            rows.append([float(p[k]) for k in FACTORS])
            ys.append(int(p["label"]))
    if len(rows) < 20:
        raise ValueError(f"only {len(rows)} usable samples after factor extraction")

    # Core real-data result: cross-validated metrics on the sampled factors.
    metrics, _fitted, importance = _train(np.array(rows, float), np.array(ys, int), model_name)

    # Susceptibility map via an in-GEE RandomForest (probability). Non-fatal: if the
    # map step fails, the run still returns LIVE, real-data metrics.
    tile_url = None
    stats = {"area_km2": norm["area_km2"]}
    try:
        training = stack.sampleRegions(collection=points, properties=["label"],
                                       scale=30, tileScale=4)
        clf = (ee.Classifier.smileRandomForest(200)
               .setOutputMode("PROBABILITY")
               .train(training, "label", FACTORS))
        prob_img = stack.classify(clf).rename("susceptibility").clip(geom)
        # Bilinear → a smooth, interpolated susceptibility surface (not blocky).
        tile_url = tiles.image_tile_url(prob_img, _VIZ, resample="bilinear")
        mean = ee.Number(prob_img.reduceRegion(ee.Reducer.mean(), geom, 90,
                         maxPixels=1e9, bestEffort=True, tileScale=4).values().get(0))
        stats["mean_susceptibility"] = round(float(mean.getInfo() or 0), 3)
    except Exception as exc:
        log.warning("landslide map tile failed (metrics still live): %s", exc)

    return {
        "module": "landslide", "product": "susceptibility", "source": "live",
        "model": model_name, "tile_url": tile_url, "grid": None,
        "legend": [{"label": c["label"], "color": c["color"]} for c in SUSCEPTIBILITY_CLASSES],
        "metrics": metrics, "feature_importance": importance,
        "top_factor": importance[0]["factor"],
        "explainability": "SHAP (Lundberg & Lee, 2017)",
        "validation": "stratified k-fold cross-validation",
        "inventory": inv_label,
        "stats": stats,
        "aoi": {"bbox": norm["bbox"], "centroid": norm["centroid"]},
    }
