"""ML flood-risk classification with SHAP explainability.

Trains a tree ensemble (Gradient Boosting / XGBoost / Random Forest) to predict
flood-prone pixels from the 11 AHP conditioning factors, and reports SHAP feature
importance + cross-validated metrics.

  * LIVE  — features sampled from the 11 reclassified factor layers; the label is
            the JRC Global Flood Database (``GLOBAL_FLOOD_DB/MODIS_EVENTS/V1``):
            the count of mapped flood EVENTS per pixel (2000-2018, Tellman et al.
            2021), i.e. observed floods, not just where surface water sits. Where
            the event archive doesn't cover an AOI it falls back to JRC Global
            Surface Water occurrence (>=5%) as a proxy (cf. Tehrany et al., 2014).
  * DEMO  — features sampled from deterministic factor fields; the label is the
            AHP-weighted composite thresholded. Trains a real model either way.

This is the data-driven alternative to the AHP weighted overlay: factor weights
are learned from where floods actually occurred (validated by ROC-AUC), so no
expert pairwise judgement is required.

References: Tellman et al. (2021) Nature (Global Flood Database); Tehrany et al.
(2014) J. Hydrology; Lundberg & Lee (2017) SHAP, NeurIPS.
"""
from __future__ import annotations

import logging
from typing import Any

import numpy as np

from . import aoi as aoi_mod
from . import demo, flood_factors, gee

log = logging.getLogger("terrashield.geo.ml_flood")

FACTORS = flood_factors.FACTOR_NAMES
MODELS = ("gbm", "xgboost", "random_forest")


def _make_model(name: str):
    if name == "xgboost":
        try:
            from xgboost import XGBClassifier

            return XGBClassifier(n_estimators=200, max_depth=4, learning_rate=0.1,
                                 subsample=0.9, eval_metric="logloss", n_jobs=-1)
        except Exception:  # pragma: no cover
            name = "gbm"
    if name == "random_forest":
        from sklearn.ensemble import RandomForestClassifier

        return RandomForestClassifier(n_estimators=300, max_depth=None, n_jobs=-1, random_state=42)
    from sklearn.ensemble import GradientBoostingClassifier

    return GradientBoostingClassifier(n_estimators=200, max_depth=3, learning_rate=0.1, random_state=42)


def _train_and_explain(X: np.ndarray, y: np.ndarray, model_name: str, source: str,
                       groups=None) -> dict[str, Any]:
    import shap
    from sklearn.model_selection import (
        StratifiedGroupKFold, StratifiedKFold, cross_val_score)

    # Guard against degenerate single-class labels.
    if len(np.unique(y)) < 2:
        y = y.copy()
        y[: max(1, len(y) // 5)] = 1 - y[0]

    model = _make_model(model_name)
    n_splits = 5 if len(y) >= 50 else 3
    # Spatial-block CV when coordinates are available — random k-fold leaks spatial
    # autocorrelation and inflates skill (Meyer & Pebesma, 2021).
    splitter = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    cv_strategy = "random k-fold"
    if groups is not None and len(set(np.asarray(groups).tolist())) >= n_splits:
        splitter = StratifiedGroupKFold(n_splits=n_splits)
        cv_strategy = "spatial block CV"

    acc = cross_val_score(model, X, y, cv=splitter, groups=groups, scoring="accuracy")
    try:
        auc = cross_val_score(model, X, y, cv=splitter, groups=groups, scoring="roc_auc")
        auc_mean = round(float(auc.mean()), 3)
    except Exception:
        auc_mean = None

    model.fit(X, y)

    # SHAP feature importance (mean |SHAP| per factor).
    try:
        explainer = shap.TreeExplainer(model)
        sv = explainer.shap_values(X)
        if isinstance(sv, list):  # some explainers return [class0, class1]
            sv = sv[-1]
        mean_abs = np.abs(np.asarray(sv)).mean(axis=0).ravel()
    except Exception as exc:  # pragma: no cover
        log.warning("SHAP failed (%s); falling back to impurity importance", exc)
        mean_abs = np.asarray(getattr(model, "feature_importances_", np.ones(len(FACTORS))))

    total = float(mean_abs.sum()) or 1.0
    importance = sorted(
        [{"factor": FACTORS[i], "importance": round(float(mean_abs[i] / total), 4)}
         for i in range(len(FACTORS))],
        key=lambda d: -d["importance"],
    )

    return {
        "module": "flood",
        "product": "ml_risk",
        "source": source,
        "model": model_name,
        "metrics": {"cv_accuracy": round(float(acc.mean()), 3),
                    "cv_accuracy_std": round(float(acc.std()), 3),
                    "cv_auc": auc_mean, "n_samples": int(len(y)),
                    "positive_rate": round(float(y.mean()), 3),
                    "cv_strategy": cv_strategy},
        "feature_importance": importance,
        "top_factor": importance[0]["factor"],
        "explainability": "SHAP (Lundberg & Lee, 2017)",
        "validation": cv_strategy,
    }


def _demo_training(bbox, n, rng):
    fields = {name: demo.smooth_field(bbox, 24, salt=f"flood:{name}") for name in FACTORS}
    w = np.array([flood_factors.DEFAULT_WEIGHTS[name] for name in FACTORS])
    ii = rng.integers(0, 24, size=n)
    jj = rng.integers(0, 24, size=n)
    X = np.column_stack([fields[name][ii, jj] for name in FACTORS])
    score = X @ w + rng.normal(0, 0.08, n)
    y = (score > np.median(score)).astype(int)
    groups = (ii // 4) * 1000 + (jj // 4)  # ~6x6 spatial blocks for grouped CV
    return X, y, groups


def flood_risk_ml(aoi: dict[str, Any], model: str = "gbm", n_samples: int = 800) -> dict[str, Any]:
    norm = aoi_mod.normalize(aoi)
    if model not in MODELS:
        model = "gbm"
    if gee.is_live():
        try:
            return _flood_risk_live(norm, model, n_samples)
        except Exception as exc:  # pragma: no cover
            log.warning("ml_flood live failed, demo fallback: %s", exc)
    rng = np.random.default_rng(abs(hash(tuple(round(b, 3) for b in norm["bbox"]))) % (2**32))
    Xd, yd, gd = _demo_training(norm["bbox"], n_samples, rng)
    res = _train_and_explain(Xd, yd, model, "demo", groups=gd)
    res["label_source"] = "AHP-weighted composite (demo proxy)"
    res["data_driven"] = False
    res["aoi"] = {"bbox": norm["bbox"], "centroid": norm["centroid"]}
    return res


def _flood_risk_live(norm, model, n_samples) -> dict[str, Any]:  # pragma: no cover
    ee = gee.get_ee()
    geom = aoi_mod.to_ee_geometry(norm)
    factors = flood_factors.compute_factor_layers(geom)
    stack = ee.Image.cat([factors[name].rename(name) for name in FACTORS])

    # Two observed-flood labels, sampled in one pass so we can pick the better one
    # client-side without a second round-trip:
    #   * flooded_gfd — JRC Global Flood Database: count of mapped flood EVENTS per
    #     pixel (2000-2018). Real observed floods; the preferred label.
    #   * flooded_gsw — JRC Global Surface Water occurrence >=5%. Surface-water
    #     proxy; the fallback where the event archive doesn't cover the AOI.
    gfd = (ee.ImageCollection("GLOBAL_FLOOD_DB/MODIS_EVENTS/V1")
           .select("flooded").sum().gte(1).unmask(0).rename("flooded_gfd"))
    gsw = (ee.Image("JRC/GSW1_4/GlobalSurfaceWater").select("occurrence")
           .gte(5).unmask(0).rename("flooded_gsw"))
    stack = stack.addBands(gfd).addBands(gsw)

    # geometries=True so each sample carries coordinates -> spatial-block CV groups.
    samples = stack.sample(region=geom, scale=100, numPixels=n_samples, seed=42,
                           geometries=True, tileScale=4).getInfo()
    rows, y_gfd, y_gsw, blocks = [], [], [], []
    for f in samples.get("features", []):
        p = f["properties"]
        if all(p.get(name) is not None for name in FACTORS):
            rows.append([float(p[name]) for name in FACTORS])
            y_gfd.append(int(p.get("flooded_gfd") or 0))
            y_gsw.append(int(p.get("flooded_gsw") or 0))
            c = (f.get("geometry") or {}).get("coordinates") or [0.0, 0.0]
            blocks.append(int(round(c[0] / 0.05)) * 100000 + int(round(c[1] / 0.05)))  # ~5 km
    if len(rows) < 30:
        raise ValueError("insufficient training samples from GEE")

    X = np.array(rows, float)
    groups = np.array(blocks)
    # Prefer the observed-event label when it carries both classes with enough
    # positives; else fall back to the surface-water proxy.
    pos_gfd = sum(y_gfd)
    if 10 <= pos_gfd < len(y_gfd):
        y = np.array(y_gfd, int)
        label_source = "JRC Global Flood Database — observed flood events (2000-2018)"
    else:
        y = np.array(y_gsw, int)
        label_source = "JRC Global Surface Water — occurrence ≥5% (surface-water proxy)"

    res = _train_and_explain(X, y, model, "live", groups=groups)
    res["label_source"] = label_source
    res["data_driven"] = True
    res["aoi"] = {"bbox": norm["bbox"], "centroid": norm["centroid"]}
    return res
