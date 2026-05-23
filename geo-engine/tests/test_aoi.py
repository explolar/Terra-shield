import math

import pytest

from terrashield_geo import aoi as aoi_mod


def test_bbox_normalize_centroid_and_area():
    norm = aoi_mod.normalize({"type": "bbox", "bbox": [73.9, 17.6, 74.3, 18.0]})
    assert norm["centroid"] == [74.1, 17.8]
    assert norm["area_km2"] > 0
    # ~0.4deg x 0.4deg near 17.8N -> roughly 44km x 44km ~ 1900 km2
    assert 1500 < norm["area_km2"] < 2400


def test_bbox_area_matches_manual():
    bbox = [0, 0, 1, 1]  # 1deg square at equator
    area = aoi_mod.bbox_area_km2(bbox)
    expected = (math.pi / 180 * 6371.0088) ** 2
    assert area == pytest.approx(expected, rel=0.01)


def test_invalid_bbox_order_raises():
    with pytest.raises(aoi_mod.AOIError):
        aoi_mod.normalize({"type": "bbox", "bbox": [74.3, 18.0, 73.9, 17.6]})


def test_too_large_aoi_raises():
    with pytest.raises(aoi_mod.AOIError):
        aoi_mod.normalize({"type": "bbox", "bbox": [-100, -40, 100, 40]})


def test_geojson_bbox_extraction():
    poly = {
        "type": "geojson",
        "geojson": {
            "type": "Polygon",
            "coordinates": [[[73.9, 17.6], [74.3, 17.6], [74.3, 18.0], [73.9, 18.0], [73.9, 17.6]]],
        },
    }
    norm = aoi_mod.normalize(poly)
    assert norm["bbox"] == [73.9, 17.6, 74.3, 18.0]
