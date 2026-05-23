"""Deterministic demo data generator (offline mode).

When Earth Engine is unavailable, compute modules render a synthetic but
*deterministic* spatial field over the AOI as a GeoJSON grid. Same AOI → same
output, so the UX, screenshots and tests are stable. This is clearly flagged with
``source: "demo"`` everywhere so it is never confused with live analysis.
"""
from __future__ import annotations

import hashlib
from typing import Any

import numpy as np


def _seed_from_bbox(bbox: list[float], salt: str) -> int:
    key = f"{salt}:" + ",".join(f"{v:.4f}" for v in bbox)
    digest = hashlib.sha256(key.encode()).hexdigest()
    return int(digest[:8], 16)


def smooth_field(bbox: list[float], n: int, salt: str, sharpness: float = 1.0) -> np.ndarray:
    """Generate an n×n field in [0, 1] that varies smoothly across the AOI.

    Built from a few low-frequency sinusoids plus seeded gaussian blobs so it
    reads like a plausible risk surface rather than white noise.
    """
    rng = np.random.default_rng(_seed_from_bbox(bbox, salt))
    ys, xs = np.mgrid[0:n, 0:n] / max(n - 1, 1)

    field = np.zeros((n, n), dtype=float)
    for _ in range(3):  # superpose a few smooth waves
        fx, fy = rng.uniform(0.5, 2.5, size=2)
        px, py = rng.uniform(0, 2 * np.pi, size=2)
        field += np.sin(2 * np.pi * fx * xs + px) * np.cos(2 * np.pi * fy * ys + py)

    for _ in range(rng.integers(2, 4)):  # a couple of hotspots
        cx, cy = rng.uniform(0, 1, size=2)
        sigma = rng.uniform(0.1, 0.3)
        field += 1.5 * np.exp(-(((xs - cx) ** 2 + (ys - cy) ** 2) / (2 * sigma**2)))

    field -= field.min()
    if field.max() > 0:
        field /= field.max()
    if sharpness != 1.0:
        field = np.power(field, sharpness)
    return field


def field_to_grid(
    bbox: list[float],
    values: np.ndarray,
    value_key: str = "value",
) -> dict[str, Any]:
    """Convert an n×n value array to a GeoJSON FeatureCollection of cells."""
    n = values.shape[0]
    min_lon, min_lat, max_lon, max_lat = bbox
    dlon = (max_lon - min_lon) / n
    dlat = (max_lat - min_lat) / n

    features = []
    for i in range(n):
        for j in range(n):
            lon0 = min_lon + j * dlon
            lat0 = max_lat - (i + 1) * dlat  # row 0 at top
            v = float(values[i, j])
            features.append(
                {
                    "type": "Feature",
                    "properties": {value_key: round(v, 4)},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [lon0, lat0],
                            [lon0 + dlon, lat0],
                            [lon0 + dlon, lat0 + dlat],
                            [lon0, lat0 + dlat],
                            [lon0, lat0],
                        ]],
                    },
                }
            )
    return {"type": "FeatureCollection", "features": features}


def grid_layer(
    bbox: list[float],
    salt: str,
    n: int = 24,
    sharpness: float = 1.0,
    value_key: str = "value",
) -> tuple[dict[str, Any], np.ndarray]:
    """Convenience: build a demo grid layer and return (geojson, values)."""
    values = smooth_field(bbox, n, salt, sharpness)
    grid = field_to_grid(bbox, values, value_key=value_key)
    return grid, values
