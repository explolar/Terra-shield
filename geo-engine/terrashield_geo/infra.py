"""InfraRisk compute — infrastructure & population exposure to hazards.

v1 computes exposure overlays: how much road network, built-up area and
population fall within a hazard footprint. Routing-based access loss is on the
roadmap. Live path uses ESA WorldCover + WorldPop; demo path is deterministic.
"""
from __future__ import annotations

import logging
from typing import Any

from . import aoi as aoi_mod
from . import demo, gee

log = logging.getLogger("terrashield.geo.infra")


def road_criticality(aoi: dict[str, Any], grid_n: int = 9) -> dict[str, Any]:
    """Rank road segments by edge-betweenness centrality. Uses the REAL OSM road
    network (Overpass) when online; falls back to a synthetic lattice if Overpass
    is unavailable. (Gauthier et al., 2018; road-criticality literature.)"""
    norm = aoi_mod.normalize(aoi)
    if gee.is_live():  # production: try real roads
        try:
            from . import roads

            r = roads.road_criticality_osm(norm["bbox"])
            return {
                "module": "infra", "product": "road_criticality", "source": "live",
                "tile_url": None,
                "grid": {"type": "FeatureCollection", "features": r["features"]},
                "legend": [
                    {"label": "Critical", "color": "#b91c1c"},
                    {"label": "Important", "color": "#f59e0b"},
                    {"label": "Normal", "color": "#64748b"},
                ],
                "stats": {
                    "segments": r["n_segments"],
                    "critical_segments": r["n_critical"],
                    "method": "edge betweenness centrality on OSM roads (NetworkX)",
                    "area_km2": norm["area_km2"],
                },
                "aoi": {"bbox": norm["bbox"], "centroid": norm["centroid"]},
            }
        except Exception as exc:  # pragma: no cover
            log.warning("OSM criticality failed, lattice fallback: %s", exc)
    return _criticality_lattice(aoi, grid_n)


def _criticality_lattice(aoi: dict[str, Any], grid_n: int = 9) -> dict[str, Any]:
    """Synthetic-lattice fallback when real OSM roads aren't available (offline)."""
    import networkx as nx
    import numpy as np

    norm = aoi_mod.normalize(aoi)
    bbox = norm["bbox"]
    min_lon, min_lat, max_lon, max_lat = bbox
    dlon = (max_lon - min_lon) / (grid_n - 1)
    dlat = (max_lat - min_lat) / (grid_n - 1)
    # Deterministic terrain field perturbs edge lengths so the lattice isn't trivial.
    field = demo.smooth_field(bbox, grid_n, salt="infra:roads")

    def coord(i, j):
        return [round(min_lon + j * dlon, 5), round(max_lat - i * dlat, 5)]

    g = nx.Graph()
    for i in range(grid_n):
        for j in range(grid_n):
            for di, dj in ((0, 1), (1, 0)):
                ni, nj = i + di, j + dj
                if ni < grid_n and nj < grid_n:
                    w = 1.0 + float(field[i, j] + field[ni, nj])  # longer through rough terrain
                    g.add_edge((i, j), (ni, nj), weight=w)

    bc = nx.edge_betweenness_centrality(g, weight="weight", normalized=True)
    vmax = max(bc.values()) or 1.0
    features = []
    for (u, v), c in sorted(bc.items(), key=lambda kv: -kv[1]):
        crit = c / vmax
        features.append({
            "type": "Feature",
            "properties": {"criticality": round(crit, 3),
                           "tier": "critical" if crit > 0.66 else "important" if crit > 0.33 else "normal"},
            "geometry": {"type": "LineString", "coordinates": [coord(*u), coord(*v)]},
        })

    n_critical = sum(1 for f in features if f["properties"]["tier"] == "critical")
    return {
        "module": "infra",
        "product": "road_criticality",
        "source": "demo",
        "tile_url": None,
        "grid": {"type": "FeatureCollection", "features": features},
        "legend": [
            {"label": "Critical", "color": "#b91c1c"},
            {"label": "Important", "color": "#f59e0b"},
            {"label": "Normal", "color": "#64748b"},
        ],
        "stats": {
            "segments": len(features),
            "critical_segments": n_critical,
            "method": "edge betweenness centrality (NetworkX)",
            "area_km2": norm["area_km2"],
        },
        "aoi": {"bbox": bbox, "centroid": norm["centroid"]},
    }


def exposure(aoi: dict[str, Any], hazard: str = "flood") -> dict[str, Any]:
    norm = aoi_mod.normalize(aoi)
    if gee.is_live():
        try:
            return _exposure_live(norm, hazard)
        except Exception as exc:  # pragma: no cover
            log.warning("infra.exposure live failed, demo fallback: %s", exc)
    return _exposure_demo(norm, hazard)


def _exposure_demo(norm, hazard) -> dict[str, Any]:
    import numpy as np

    bbox = norm["bbox"]
    hazard_field = demo.smooth_field(bbox, 22, salt=f"infra:hazard:{hazard}", sharpness=1.6)
    builtup_field = demo.smooth_field(bbox, 22, salt="infra:builtup")
    pop_density = demo.smooth_field(bbox, 22, salt="infra:pop")

    exposed_mask = hazard_field > 0.55
    area = norm["area_km2"]
    # Synthesize totals scaled to AOI area for plausibility.
    total_pop = int(area * np.interp(float(pop_density.mean()), [0, 1], [200, 4000]))
    exposed_pop = int(total_pop * float((exposed_mask * pop_density).sum() / max(pop_density.sum(), 1e-6)))
    total_built_km2 = round(area * float(builtup_field.mean()) * 0.3, 2)
    exposed_built_km2 = round(total_built_km2 * float(exposed_mask.mean()), 2)

    grid = demo.field_to_grid(bbox, (hazard_field * builtup_field).round(3), value_key="exposure")
    return {
        "module": "infra",
        "product": "exposure",
        "source": "demo",
        "hazard": hazard,
        "tile_url": None,
        "grid": grid,
        "legend": [
            {"label": "High exposure", "color": "#67000d"},
            {"label": "Moderate", "color": "#fb6a4a"},
            {"label": "Low", "color": "#fee5d9"},
        ],
        "stats": {
            "population_total": total_pop,
            "population_exposed": exposed_pop,
            "population_exposed_pct": round(exposed_pop / max(total_pop, 1) * 100, 1),
            "builtup_km2": total_built_km2,
            "builtup_exposed_km2": exposed_built_km2,
            "area_km2": area,
        },
        "aoi": {"bbox": bbox, "centroid": norm["centroid"]},
    }


def _exposure_live(norm, hazard) -> dict[str, Any]:  # pragma: no cover
    from . import flood_factors

    ee = gee.get_ee()
    geom = aoi_mod.to_ee_geometry(norm)

    pop = ee.ImageCollection("WorldPop/GP/100m/pop").filter(
        ee.Filter.eq("year", 2020)
    ).mosaic().clip(geom)
    builtup = ee.Image("ESA/WorldCover/v200/2021").select("Map").eq(50).clip(geom)

    # Real hazard footprint: high flood susceptibility (AHP classes 4-5) from the
    # same 11-factor model FloodAI uses — not a bottom-of-elevation proxy.
    composite, _factors, _ahp = flood_factors.compute_susceptibility(geom)
    hazard_mask = composite.gte(4)

    def _sum(img, scale):
        d = img.reduceRegion(reducer=ee.Reducer.sum(), geometry=geom, scale=scale,
                             maxPixels=1e9, bestEffort=True, tileScale=4)
        v = d.values().get(0)
        return ee.Number(ee.Algorithms.If(v, v, 0)).getInfo()

    # Coarser scales for much faster reductions (population/built-up totals stay
    # representative at AOI scale).
    built_km2_img = builtup.multiply(ee.Image.pixelArea()).divide(1e6)
    total_pop = _sum(pop, 300)
    exposed_pop = _sum(pop.updateMask(hazard_mask), 300)
    built_total = _sum(built_km2_img, 100)
    built_exposed = _sum(built_km2_img.updateMask(hazard_mask), 100)

    return {
        "module": "infra",
        "product": "exposure",
        "source": "live",
        "hazard": hazard,
        "tile_url": None,
        "grid": None,
        "legend": [{"label": "Exposed", "color": "#67000d"}],
        "stats": {
            "population_total": int(total_pop),
            "population_exposed": int(exposed_pop),
            "population_exposed_pct": round(exposed_pop / max(total_pop, 1) * 100, 1),
            "builtup_km2": round(built_total, 2),
            "builtup_exposed_km2": round(built_exposed, 2),
            "area_km2": norm["area_km2"],
        },
        "aoi": {"bbox": norm["bbox"], "centroid": norm["centroid"]},
    }
