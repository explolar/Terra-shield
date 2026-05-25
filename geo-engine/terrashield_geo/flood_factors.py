"""Paper-grade 11-factor AHP-MCDM flood-susceptibility engine (live / Earth Engine).

Ported and adapted for TerraShield from the FluviaAI methodology. Implements an
11-factor Analytic Hierarchy Process with a Saaty pairwise matrix, eigenvector
weights, Consistency-Ratio validation, and per-factor 1-5 reclassification.

Factors (literature standard):
  1 Distance to River  - HydroSHEDS flow accumulation
  2 HAND               - Height Above Nearest Drainage (HydroSHEDS conditioned DEM)
  3 Rainfall           - CHIRPS annual precipitation
  4 Slope              - SRTM DEM
  5 Elevation          - SRTM DEM
  6 Drainage Density   - HydroSHEDS stream network
  7 TWI                - Topographic Wetness Index
  8 LULC               - ESA WorldCover v200
  9 Soil Texture       - OpenLandMap USDA texture class
 10 NDVI               - MODIS annual composite
 11 Curvature          - DEM Laplacian

References: Saaty (1980); Tehrany et al. (2014) J. Hydrology; Khosravi et al.
(2018) STOTEN; Nobre et al. (2011) J. Hydrology (HAND).
"""
from __future__ import annotations

import math

import numpy as np

FACTOR_NAMES = [
    "distance_to_river", "hand", "rainfall", "slope", "elevation",
    "drainage_density", "twi", "lulc", "soil", "ndvi", "curvature",
]

FACTOR_LABELS = {
    "distance_to_river": "Distance to River", "hand": "HAND", "rainfall": "Rainfall",
    "slope": "Slope", "elevation": "Elevation", "drainage_density": "Drainage Density",
    "twi": "TWI", "lulc": "LULC", "soil": "Soil Texture", "ndvi": "NDVI",
    "curvature": "Curvature",
}

# Saaty 9-point pairwise comparison matrix (expert/literature consensus).
# Order: dist, hand, rain, slope, elev, drain, twi, lulc, soil, ndvi, curv.
AHP_MATRIX = [
    [1, 2, 3, 3, 4, 4, 5, 6, 7, 8, 9],
    [1 / 2, 1, 2, 2, 3, 3, 4, 4, 5, 6, 7],
    [1 / 3, 1 / 2, 1, 2, 2, 3, 3, 4, 5, 6, 7],
    [1 / 3, 1 / 2, 1 / 2, 1, 1, 2, 2, 3, 4, 5, 6],
    [1 / 4, 1 / 3, 1 / 2, 1, 1, 2, 2, 3, 3, 5, 5],
    [1 / 4, 1 / 3, 1 / 3, 1 / 2, 1 / 2, 1, 1, 2, 3, 4, 5],
    [1 / 5, 1 / 4, 1 / 3, 1 / 2, 1 / 2, 1, 1, 2, 3, 3, 4],
    [1 / 6, 1 / 4, 1 / 4, 1 / 3, 1 / 3, 1 / 2, 1 / 2, 1, 2, 3, 3],
    [1 / 7, 1 / 5, 1 / 5, 1 / 4, 1 / 3, 1 / 3, 1 / 3, 1 / 2, 1, 2, 3],
    [1 / 8, 1 / 6, 1 / 6, 1 / 5, 1 / 5, 1 / 4, 1 / 3, 1 / 3, 1 / 2, 1, 2],
    [1 / 9, 1 / 7, 1 / 7, 1 / 6, 1 / 5, 1 / 5, 1 / 4, 1 / 3, 1 / 3, 1 / 2, 1],
]

_RI = {1: 0, 2: 0, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41,
       9: 1.45, 10: 1.49, 11: 1.51}

# 5-class susceptibility palette (low -> very high).
MCA_VIZ = {"min": 1, "max": 5, "palette": ["1a9850", "91cf60", "ffffbf", "fc8d59", "d73027"]}
FACTOR_VIZ = {"min": 1, "max": 5, "palette": ["2166ac", "67a9cf", "f7f7f7", "ef8a62", "b2182b"]}


def ahp_report(matrix=None) -> dict:
    """Priority weights via the principal-eigenvector method + CR validation."""
    m = np.asarray(matrix if matrix is not None else AHP_MATRIX, dtype=float)
    n = m.shape[0]
    eigvals, eigvecs = np.linalg.eig(m)
    k = int(np.argmax(eigvals.real))
    lam = float(eigvals[k].real)
    w = eigvecs[:, k].real
    w = w / w.sum()
    ci = (lam - n) / (n - 1) if n > 1 else 0.0
    ri = _RI.get(n, 1.49)
    cr = ci / ri if ri > 0 else 0.0
    return {
        "weights": {FACTOR_NAMES[i]: round(float(w[i]), 4) for i in range(n)},
        "lambda_max": round(lam, 4),
        "consistency_index": round(ci, 4),
        "consistency_ratio": round(cr, 4),
        "consistent": bool(cr < 0.10),
        "n_factors": n,
    }


DEFAULT_WEIGHTS = ahp_report()["weights"]


# --------------------------------------------------------------------------- #
# Earth Engine factor computation (live path only)
# --------------------------------------------------------------------------- #
def _reclassify(image, band, geom, invert=False):  # pragma: no cover
    from . import gee

    ee = gee.get_ee()
    p = image.reduceRegion(reducer=ee.Reducer.percentile([20, 40, 60, 80]),
                           geometry=geom, scale=100, bestEffort=True, maxPixels=1e9)
    p20, p40 = ee.Number(p.get(f"{band}_p20")), ee.Number(p.get(f"{band}_p40"))
    p60, p80 = ee.Number(p.get(f"{band}_p60")), ee.Number(p.get(f"{band}_p80"))
    if invert:  # high value = low risk
        return (ee.Image(3).where(image.lte(p20), 5)
                .where(image.gt(p20).And(image.lte(p40)), 4)
                .where(image.gt(p60).And(image.lte(p80)), 2)
                .where(image.gt(p80), 1).clip(geom))
    return (ee.Image(3).where(image.lte(p20), 1)
            .where(image.gt(p20).And(image.lte(p40)), 2)
            .where(image.gt(p60).And(image.lte(p80)), 4)
            .where(image.gt(p80), 5).clip(geom))


def compute_factor_layers(geom):  # pragma: no cover
    """All 11 conditioning factors reclassified to a 1-5 risk scale."""
    from . import gee

    ee = gee.get_ee()
    dem = ee.Image("USGS/SRTMGL1_003").select("elevation").clip(geom)
    slope = ee.Terrain.slope(dem).clip(geom)
    flow_acc = ee.Image("WWF/HydroSHEDS/15ACC").select("b1").clip(geom)
    stream_thr = 100
    f = {}

    # 1. Distance to river (closer = higher risk)
    streams = flow_acc.gt(stream_thr)
    dist_m = streams.fastDistanceTransform(2048).sqrt().multiply(
        ee.Image.pixelArea().sqrt()).rename("dist")
    f["distance_to_river"] = _reclassify(dist_m, "dist", geom, invert=True)

    # 2. HAND (lower = higher risk)
    cond_dem = ee.Image("WWF/HydroSHEDS/15CONDEM").select("b1").clip(geom)
    drainage_elev = cond_dem.updateMask(flow_acc.gt(stream_thr))
    nearest = drainage_elev
    for r in (3, 5, 10, 20, 30, 40):
        nearest = nearest.unmask(nearest.focal_min(radius=r, kernelType="circle", units="pixels"))
    dem_min = cond_dem.reduceRegion(ee.Reducer.min(), geom, 90, bestEffort=True, maxPixels=1e9)
    nearest = nearest.unmask(ee.Number(dem_min.get("b1")))
    hand = cond_dem.subtract(nearest).max(0).rename("hand")
    f["hand"] = (ee.Image(1).where(hand.lte(20), 2).where(hand.lte(10), 3)
                 .where(hand.lte(5), 4).where(hand.lte(2), 5).clip(geom))

    # 3. Rainfall (more = higher risk)
    rain = (ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
            .filterDate("2023-01-01", "2024-01-01").sum().rename("rain").clip(geom))
    f["rainfall"] = _reclassify(rain, "rain", geom, invert=False)

    # 4. Slope (flatter = higher risk)
    f["slope"] = _reclassify(slope.rename("slope"), "slope", geom, invert=True)

    # 5. Elevation (lower = higher risk)
    f["elevation"] = _reclassify(dem.rename("elevation"), "elevation", geom, invert=True)

    # 6. Drainage density (denser = higher risk)
    dd = (flow_acc.gt(stream_thr).selfMask()
          .reduceNeighborhood(ee.Reducer.sum(), ee.Kernel.circle(1500, "meters"))
          .multiply(0.09).divide(math.pi * 1.5 * 1.5).rename("dd").clip(geom))
    f["drainage_density"] = _reclassify(dd, "dd", geom, invert=False)

    # 7. TWI (wetter = higher risk)
    tan_slope = slope.multiply(math.pi / 180).tan().max(0.001)
    twi = flow_acc.max(1).multiply(ee.Image.pixelArea()).divide(tan_slope).log().rename("twi").clip(geom)
    f["twi"] = _reclassify(twi, "twi", geom, invert=False)

    # 8. LULC (built-up / water = higher risk)
    lulc = ee.ImageCollection("ESA/WorldCover/v200").mosaic().select("Map").clip(geom)
    f["lulc"] = lulc.remap([10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100],
                           [1, 2, 3, 4, 5, 4, 1, 5, 5, 4, 3]).clip(geom)

    # 9. Soil texture (clay = higher risk)
    soil = ee.Image("OpenLandMap/SOL/SOL_TEXTURE-CLASS_USDA-TT_M/v02").select("b0").clip(geom)
    f["soil"] = soil.remap([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                           [5, 5, 4, 4, 4, 3, 3, 3, 2, 4, 2, 1]).clip(geom)

    # 10. NDVI (less vegetation = higher risk)
    ndvi = (ee.ImageCollection("MODIS/061/MOD13A2").filterDate("2023-01-01", "2024-01-01")
            .select("NDVI").mean().multiply(0.0001).rename("ndvi").clip(geom))
    f["ndvi"] = _reclassify(ndvi, "ndvi", geom, invert=True)

    # 11. Curvature (concave = higher risk)
    lap = ee.Kernel.fixed(3, 3, [[0, 1, 0], [1, -4, 1], [0, 1, 0]])
    curv = dem.convolve(lap).rename("curv").clip(geom)
    f["curvature"] = _reclassify(curv, "curv", geom, invert=True)

    return f


def compute_susceptibility(geom, weights=None):  # pragma: no cover
    """Weighted AHP composite (1-5) + per-factor layers + AHP report."""
    from . import gee

    ee = gee.get_ee()
    report = ahp_report()
    if weights is None:
        ahp = report
    else:
        # User-tuned weights still report the model's AHP consistency (the CR is a
        # property of the fixed pairwise matrix, not the slider overrides).
        ahp = {**report, "weights": weights}
    w = ahp["weights"]
    factors = compute_factor_layers(geom)
    composite = ee.Image(0).toFloat()
    for name in FACTOR_NAMES:
        composite = composite.add(factors[name].toFloat().multiply(w.get(name, 0)))
    composite = composite.round().clamp(1, 5).clip(geom).rename("susceptibility")
    return composite, factors, ahp
