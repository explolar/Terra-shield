"""Area-of-interest parsing, validation, and geometry helpers.

Works without Earth Engine. ``to_ee_geometry`` is only used on the live path.
"""
from __future__ import annotations

import math
from typing import Any

_EARTH_RADIUS_KM = 6371.0088
MAX_AOI_AREA_KM2 = 50_000.0  # guard rail against accidental continent-sized AOIs


class AOIError(ValueError):
    """Raised when an AOI is malformed or out of bounds."""


def normalize(aoi: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize an AOI dict.

    Accepts either::

        {"type": "bbox", "bbox": [minLon, minLat, maxLon, maxLat]}
        {"type": "geojson", "geojson": <Polygon Feature/Geometry>}

    Returns a dict with ``bbox``, ``centroid``, ``area_km2`` and the original.
    """
    if not isinstance(aoi, dict) or "type" not in aoi:
        raise AOIError("AOI must be a dict with a 'type' of 'bbox' or 'geojson'")

    kind = aoi["type"]
    if kind == "bbox":
        bbox = aoi.get("bbox")
        _validate_bbox(bbox)
    elif kind == "geojson":
        bbox = _bbox_of_geojson(aoi.get("geojson"))
    else:
        raise AOIError(f"unknown AOI type: {kind!r}")

    area = bbox_area_km2(bbox)
    if area > MAX_AOI_AREA_KM2:
        raise AOIError(
            f"AOI too large ({area:,.0f} km²). Max is {MAX_AOI_AREA_KM2:,.0f} km²."
        )

    cx = (bbox[0] + bbox[2]) / 2
    cy = (bbox[1] + bbox[3]) / 2
    return {
        "type": kind,
        "bbox": bbox,
        "centroid": [round(cx, 5), round(cy, 5)],
        "area_km2": round(area, 2),
        "original": aoi,
    }


def _validate_bbox(bbox: Any) -> None:
    if not (isinstance(bbox, (list, tuple)) and len(bbox) == 4):
        raise AOIError("bbox must be [minLon, minLat, maxLon, maxLat]")
    min_lon, min_lat, max_lon, max_lat = bbox
    if not (-180 <= min_lon < max_lon <= 180):
        raise AOIError("longitudes must satisfy -180 <= minLon < maxLon <= 180")
    if not (-90 <= min_lat < max_lat <= 90):
        raise AOIError("latitudes must satisfy -90 <= minLat < maxLat <= 90")


def _bbox_of_geojson(geojson: Any) -> list[float]:
    if not isinstance(geojson, dict):
        raise AOIError("geojson AOI requires a GeoJSON object")
    geom = geojson.get("geometry", geojson)
    coords = geom.get("coordinates")
    if not coords:
        raise AOIError("geojson AOI has no coordinates")

    xs: list[float] = []
    ys: list[float] = []

    def _walk(c: Any) -> None:
        if isinstance(c, (list, tuple)):
            if len(c) == 2 and all(isinstance(v, (int, float)) for v in c):
                xs.append(float(c[0]))
                ys.append(float(c[1]))
            else:
                for sub in c:
                    _walk(sub)

    _walk(coords)
    if not xs:
        raise AOIError("could not extract coordinates from geojson AOI")
    bbox = [min(xs), min(ys), max(xs), max(ys)]
    _validate_bbox(bbox)
    return bbox


def bbox_area_km2(bbox: list[float]) -> float:
    """Approximate area of a lon/lat bbox in km² (spherical)."""
    min_lon, min_lat, max_lon, max_lat = bbox
    lat_rad = math.radians((min_lat + max_lat) / 2)
    km_per_deg_lat = (math.pi / 180) * _EARTH_RADIUS_KM
    km_per_deg_lon = km_per_deg_lat * math.cos(lat_rad)
    height = (max_lat - min_lat) * km_per_deg_lat
    width = (max_lon - min_lon) * km_per_deg_lon
    return abs(width * height)


def to_ee_geometry(aoi: dict[str, Any]):
    """Convert a normalized AOI to an ``ee.Geometry`` (live path only)."""
    from . import gee

    ee = gee.get_ee()
    if ee is None:
        raise AOIError("earthengine-api not available")
    norm = aoi if "bbox" in aoi else normalize(aoi)
    if norm["type"] == "geojson":
        geom = norm["original"]["geojson"]
        geom = geom.get("geometry", geom)
        return ee.Geometry(geom)
    return ee.Geometry.Rectangle(norm["bbox"])
