"""Tile-URL generation and legend builders.

``image_tile_url`` turns a styled ``ee.Image`` into an XYZ tile-URL template that
Leaflet streams directly from Google's edge — no rasters cross our backend. Used
on the live path only. Legends work in both modes.
"""
from __future__ import annotations

from typing import Any

# Reusable color ramps (low → high).
RAMPS: dict[str, list[str]] = {
    "risk": ["#1a9850", "#91cf60", "#d9ef8b", "#fee08b", "#fc8d59", "#d73027", "#7f0000"],
    "water": ["#f7fbff", "#c6dbef", "#6baed6", "#2171b5", "#08306b"],
    "precip": ["#ffffcc", "#a1dab4", "#41b6c4", "#2c7fb8", "#253494"],
    "temp": ["#313695", "#74add1", "#fee090", "#f46d43", "#a50026"],
    "drought": ["#730000", "#e60000", "#ffaa00", "#fcd37f", "#ffffff"],  # D4→none
    "vegetation": ["#a50026", "#fdae61", "#ffffbf", "#a6d96a", "#1a9641"],
}


def build_legend(
    ramp: str,
    labels: list[str],
    vmin: float = 0.0,
    vmax: float = 1.0,
) -> list[dict[str, Any]]:
    """Build a discrete legend from a ramp and class labels."""
    colors = RAMPS.get(ramp, RAMPS["risk"])
    n = len(labels)
    step = (vmax - vmin) / n
    out = []
    for k, label in enumerate(labels):
        color = colors[min(int(k / max(n - 1, 1) * (len(colors) - 1)), len(colors) - 1)]
        out.append(
            {
                "label": label,
                "color": color,
                "min": round(vmin + k * step, 3),
                "max": round(vmin + (k + 1) * step, 3),
            }
        )
    return out


def image_tile_url(image: Any, vis_params: dict[str, Any], resample: str | None = "bilinear") -> str:
    """Return an XYZ tile-URL template for a styled ``ee.Image`` (live path).

    ``resample`` ("bilinear" | "bicubic") renders every layer as a smooth,
    interpolated surface instead of blocky native pixels. Pass ``None`` to keep
    nearest-neighbour (e.g. for a strictly categorical layer you want crisp).
    """
    img = image.resample(resample) if resample else image
    styled = img.visualize(**vis_params)
    mapid = styled.getMapId()
    # Newer earthengine-api returns a ready tile_fetcher with the template.
    fetcher = mapid.get("tile_fetcher")
    if fetcher is not None:
        return fetcher.url_format
    return mapid["tile_fetcher"].url_format
