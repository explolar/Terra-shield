"""Real OSM road network via the Overpass API — no key, no GEE.

Powers InfraRisk road-criticality (edge betweenness) and ResilienceOR evacuation
routing on actual roads instead of a synthetic lattice. Network calls are guarded
with a mirror fallback; callers fall back to the demo lattice if Overpass is down.
"""
from __future__ import annotations

import logging
import math

log = logging.getLogger("terrashield.geo.roads")

OVERPASS_URLS = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
)
# Overpass 406s requests without a descriptive User-Agent.
_HEADERS = {
    "User-Agent": "TerraShield/1.0 (climate-risk platform; contact admin@terrashield.app)",
    "Accept": "application/json",
}
# Major roads only — keeps the graph small enough for fast betweenness.
ROAD_TYPES = "motorway|trunk|primary|secondary|tertiary"


def haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    (la1, lo1), (la2, lo2) = a, b
    p1, p2 = math.radians(la1), math.radians(la2)
    dp, dl = math.radians(la2 - la1), math.radians(lo2 - lo1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(h))


def fetch_roads(bbox, timeout: int = 25) -> list[dict]:
    """Fetch OSM road ways (with geometry) for the bbox. Raises if Overpass is down."""
    import httpx  # backend dependency; imported lazily so the package loads without it

    min_lon, min_lat, max_lon, max_lat = bbox
    query = (
        f"[out:json][timeout:{timeout}];"
        f'(way["highway"~"^({ROAD_TYPES})$"]({min_lat},{min_lon},{max_lat},{max_lon}););'
        f"out geom;"
    )
    last = None
    for url in OVERPASS_URLS:
        try:
            r = httpx.post(url, data={"data": query}, headers=_HEADERS, timeout=timeout + 10)
            r.raise_for_status()
            return r.json().get("elements", [])
        except Exception as exc:  # try the next mirror
            last = exc
            log.warning("overpass %s failed: %s", url, exc)
    raise RuntimeError(f"overpass unavailable: {last}")


def build_graph(elements: list[dict], max_edges: int = 4000):
    """Undirected road graph: nodes = (lat, lon) vertices, edges weighted by km."""
    import networkx as nx

    g = nx.Graph()
    for way in elements:
        geom = way.get("geometry") or []
        for a, b in zip(geom, geom[1:]):
            na = (round(a["lat"], 5), round(a["lon"], 5))
            nb = (round(b["lat"], 5), round(b["lon"], 5))
            if na == nb:
                continue
            g.add_edge(na, nb, weight=haversine_km(na, nb))
            if g.number_of_edges() >= max_edges:
                return g
    return g


def road_criticality_osm(bbox, max_features: int = 1500) -> dict:
    """Rank real OSM road segments by edge-betweenness centrality (the share of
    shortest paths that use each segment). High-betweenness roads are the network's
    critical links — losing them fragments emergency access most (Gauthier et al.,
    2018). Returns GeoJSON LineString features + summary counts."""
    import networkx as nx

    g = build_graph(fetch_roads(bbox))
    if g.number_of_edges() < 5:
        raise ValueError("too few OSM roads in this AOI")

    # Approximate betweenness via k source samples when the graph is large.
    k = min(g.number_of_nodes(), 200) if g.number_of_nodes() > 300 else None
    bc = nx.edge_betweenness_centrality(g, k=k, weight="weight", normalized=True, seed=42)
    vmax = max(bc.values()) or 1.0

    ranked = sorted(bc.items(), key=lambda kv: -kv[1])[:max_features]
    features, n_critical = [], 0
    for (u, v), c in ranked:
        crit = c / vmax
        tier = "critical" if crit > 0.66 else "important" if crit > 0.33 else "normal"
        n_critical += tier == "critical"
        features.append({
            "type": "Feature",
            "properties": {"criticality": round(crit, 3), "tier": tier},
            # nodes are (lat, lon); GeoJSON wants [lon, lat]
            "geometry": {"type": "LineString",
                         "coordinates": [[u[1], u[0]], [v[1], v[0]]]},
        })
    return {"features": features, "n_segments": g.number_of_edges(), "n_critical": n_critical}
