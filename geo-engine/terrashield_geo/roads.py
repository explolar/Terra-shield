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


def route_to_exit(g, bbox, flood_penalty: float = 1e6) -> dict:
    """Evacuation route on a prebuilt road graph: shortest km-weighted Dijkstra path
    from the AOI-centre node to the nearest boundary 'exit' node. Edges already
    bumped by ``flood_penalty`` (flooded) are avoided when a dry route exists.

    OSM road graphs are fragmented (ways only connect where they share an exact
    node), so we route within the largest connected component — that guarantees a
    path between the chosen source and exits exists."""
    import networkx as nx

    if g.number_of_nodes() < 6:
        raise ValueError("too few OSM road nodes in this AOI")
    g = g.subgraph(max(nx.connected_components(g), key=len))
    if g.number_of_nodes() < 6:
        raise ValueError("largest road component too small in this AOI")
    min_lon, min_lat, max_lon, max_lat = bbox
    clat, clon = (min_lat + max_lat) / 2, (min_lon + max_lon) / 2
    nodes = list(g.nodes())

    def nearest(la, lo):
        return min(nodes, key=lambda n: haversine_km(n, (la, lo)))

    source = nearest(clat, clon)
    exits = {nearest(min_lat, clon), nearest(max_lat, clon),
             nearest(clat, min_lon), nearest(clat, max_lon)} - {source}
    best = None
    for ex in exits:
        try:
            length, path = nx.single_source_dijkstra(g, source, ex, weight="weight")
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            continue
        if best is None or length < best[0]:
            best = (length, path)
    if best is None:
        return {"reachable": False, "warning": "no route to a boundary exit",
                "route_km": 0.0, "segments": 0, "crosses_flood": False,
                "uses_flooded_edge": False,
                "route_geojson": {"type": "FeatureCollection", "features": []}}

    length, path = best
    real_km = round(sum(haversine_km(path[i], path[i + 1]) for i in range(len(path) - 1)), 2)
    crosses = length >= flood_penalty
    return {
        "reachable": True,
        "route_km": real_km,
        "segments": len(path) - 1,
        "crosses_flood": crosses,
        "uses_flooded_edge": crosses,
        "warning": "safest available route still crosses flooding" if crosses else None,
        "route_geojson": {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "properties": {"type": "evacuation_route", "route_km": real_km,
                               "crosses_flood": crosses},
                "geometry": {"type": "LineString",
                             "coordinates": [[n[1], n[0]] for n in path]},
            }],
        },
    }


def evacuation_osm(bbox) -> dict:
    """Build the real OSM road graph and route to the nearest exit (no flood penalty).
    Uses a higher edge cap than criticality — Dijkstra is cheap and a fuller graph
    keeps the network connected so a route can be found."""
    return route_to_exit(build_graph(fetch_roads(bbox), max_edges=20000), bbox)
