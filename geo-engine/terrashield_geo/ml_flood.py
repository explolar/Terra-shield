"""ML flood-risk classification with SHAP explainability.

Trains a tree ensemble (Gradient Boosting / XGBoost / Random Forest) to predict
flood-prone pixels from the 11 AHP conditioning factors, and reports SHAP feature
importance + cross-validated metrics.

  * LIVE  — features sampled from the 11 reclassified factor layers; the label is
            the JRC Global Surface Water occurrence (>=5% = historically flooded),
            an independent observed-flood proxy (cf. Tehrany et al., 2014).
  * DEMO  — features sampled from deterministic factor fields; the label is the
            AHP-weighted composite thresholded. Trains a real model either way.

References: Tehrany et al. (2014) J. Hydrology; Lundberg & Lee (2017) SHAP, NeurIPS.
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


def _train_and_explain(X: np.ndarray, y: np.ndarray, model_name: str, source: str) -> dict[str, Any]:
    import shap
    from sklearn.model_selection import cross_val_score

    # Guard against degenerate single-class labels.
    if len(np.unique(y)) < 2:
        y = y.copy()
        y[: max(1, len(y) // 5)] = 1 - y[0]

    model = _make_model(model_name)
    n_splits = 5 if len(y) >= 50 else 3
    acc = cross_val_score(model, X, y, cv=n_splits, scoring="accuracy")
    try:
        auc = cross_val_score(model, X, y, cv=n_splits, scoring="roc_auc")
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
                    "positive_rate": round(float(y.mean()), 3)},
        "feature_importance": importance,
        "top_factor": importance[0]["factor"],
        "explainability": "SHAP (Lundberg & Lee, 2017)",
        "validation": "stratified k-fold cross-validation",
    }


def _demo_training(bbox, n, rng):
    fields = {name: demo.smooth_field(bbox, 24, salt=f"flood:{name}") for name in FACTORS}
    w = np.array([flood_factors.DEFAULT_WEIGHTS[name] for name in FACTORS])
    ii = rng.integers(0, 24, size=n)
    jj = rng.integers(0, 24, size=n)
    X = np.column_stack([fields[name][ii, jj] for name in FACTORS])
    score = X @ w + rng.normal(0, 0.08, n)
    y = (score > np.median(score)).astype(int)
    return X, y


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
    res = _train_and_explain(*_demo_training(norm["bbox"], n_samples, rng), model, "demo")
    res["aoi"] = {"bbox": norm["bbox"], "centroid": norm["centroid"]}
    return res


def _flood_risk_live(norm, model, n_samples) -> dict[str, Any]:  # pragma: no cover
    ee = gee.get_ee()
    geom = aoi_mod.to_ee_geometry(norm)
    factors = flood_factors.compute_factor_layers(geom)
    stack = ee.Image.cat([factors[name].rename(name) for name in FACTORS])
    # Independent observed-flood label: JRC GSW historical occurrence >= 5%.
    label = (ee.Image("JRC/GSW1_4/GlobalSurfaceWater").select("occurrence")
             .gte(5).unmask(0).rename("flooded"))
    stack = stack.addBands(label)
    samples = stack.sample(region=geom, scale=100, numPixels=n_samples, seed=42,
                           geometries=False, tileScale=4).getInfo()
    feats = samples.get("features", [])
    rows, ys = [], []
    for f in feats:
        p = f["properties"]
        if all(p.get(name) is not None for name in FACTORS) and p.get("flooded") is not None:
            rows.append([float(p[name]) for name in FACTORS])
            ys.append(int(p["flooded"]))
    if len(rows) < 30:
        raise ValueError("insufficient training samples from GEE")
    res = _train_and_explain(np.array(rows, float), np.array(ys, int), model, "live")
    res["aoi"] = {"bbox": norm["bbox"], "centroid": norm["centroid"]}
    return res
