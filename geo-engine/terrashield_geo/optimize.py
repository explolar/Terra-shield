"""ResilienceOR — operations-research & optimization layer.

Climate risk is not just *measured*, it is *acted on* under constraints. This
module turns hazard layers into decisions:

  * ``ahp_weights``      — Analytic Hierarchy Process: derive defensible factor
                           weights from pairwise judgements + a consistency check
                           (Saaty, 1980). Used by FloodAI's weighted overlay.
  * ``topsis``           — rank AOIs/districts by multi-criteria risk (Hwang &
                           Yoon, 1981).
  * ``locate_shelters``  — Maximal Covering Location Problem: site p relief
                           centres to cover the most exposed population
                           (Church & ReVelle, 1974). Greedy w/ submodular bound.
  * ``evacuation_route`` — flood-aware shortest path (Dijkstra) on a road graph
                           where flooded edges are penalised/blocked.
  * ``mitigation_plan``  — 0/1 knapsack: pick interventions maximising risk
                           reduction under a budget (Bellman DP).

Everything is pure-Python + NumPy (no solver dependency) with documented
complexity, so it runs anywhere. For large exact instances, swap the greedy/DP
for an ILP (PuLP/OR-Tools) behind the same signatures.
"""
from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, field
from typing import Any, Iterable

import numpy as np

# Saaty's Random Consistency Index by matrix order.
_RANDOM_INDEX = {1: 0.0, 2: 0.0, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24,
                 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49}


# --------------------------------------------------------------------------- #
# 1) Analytic Hierarchy Process  —  O(n^2)
# --------------------------------------------------------------------------- #
def ahp_weights(matrix: list[list[float]], labels: list[str] | None = None) -> dict[str, Any]:
    """Derive priority weights from a pairwise-comparison matrix.

    The matrix must be square, positive and reciprocal (a[i][j] == 1/a[j][i]).
    Weights are the normalised principal eigenvector, approximated by the
    geometric-mean method (stable and exact for consistent matrices). The
    Consistency Ratio (CR) tells you whether the judgements are coherent: CR <=
    0.10 is the accepted threshold (Saaty, 1980).
    """
    a = np.asarray(matrix, dtype=float)
    n = a.shape[0]
    if a.ndim != 2 or a.shape[0] != a.shape[1]:
        raise ValueError("AHP matrix must be square")
    if np.any(a <= 0):
        raise ValueError("AHP matrix entries must be positive")

    # Geometric mean of each row -> normalise = principal eigenvector estimate.
    geo_mean = np.prod(a, axis=1) ** (1.0 / n)
    weights = geo_mean / geo_mean.sum()

    # Consistency: lambda_max from (A w)_i / w_i averaged.
    aw = a @ weights
    lambda_max = float(np.mean(aw / weights))
    ci = (lambda_max - n) / (n - 1) if n > 1 else 0.0
    ri = _RANDOM_INDEX.get(n, 1.49)
    cr = ci / ri if ri > 0 else 0.0

    labels = labels or [f"c{i}" for i in range(n)]
    return {
        "labels": labels,
        "weights": {labels[i]: round(float(weights[i]), 4) for i in range(n)},
        "lambda_max": round(lambda_max, 4),
        "consistency_index": round(ci, 4),
        "consistency_ratio": round(cr, 4),
        "consistent": cr <= 0.10,
        "note": "CR <= 0.10 indicates acceptable judgement consistency (Saaty, 1980).",
    }


# --------------------------------------------------------------------------- #
# 2) TOPSIS multi-criteria ranking  —  O(m*k)
# --------------------------------------------------------------------------- #
def topsis(
    alternatives: list[str],
    matrix: list[list[float]],
    weights: list[float],
    benefit: list[bool],
) -> dict[str, Any]:
    """Rank alternatives by closeness to the ideal solution.

    ``matrix`` is m alternatives x k criteria. ``benefit[j]`` is True if larger
    is better for criterion j (e.g. preparedness), False if smaller is better
    (e.g. flood risk, exposed population).
    """
    x = np.asarray(matrix, dtype=float)
    w = np.asarray(weights, dtype=float)
    w = w / w.sum()
    m, k = x.shape

    norm = np.sqrt((x**2).sum(axis=0))
    norm[norm == 0] = 1.0
    v = (x / norm) * w  # weighted normalised matrix

    ideal_best = np.where(benefit, v.max(axis=0), v.min(axis=0))
    ideal_worst = np.where(benefit, v.min(axis=0), v.max(axis=0))

    d_best = np.sqrt(((v - ideal_best) ** 2).sum(axis=1))
    d_worst = np.sqrt(((v - ideal_worst) ** 2).sum(axis=1))
    closeness = d_worst / (d_best + d_worst + 1e-12)

    order = np.argsort(-closeness)
    ranking = [
        {"alternative": alternatives[i], "score": round(float(closeness[i]), 4),
         "rank": int(rank + 1)}
        for rank, i in enumerate(order)
    ]
    return {"ranking": ranking, "best": alternatives[int(order[0])]}


# --------------------------------------------------------------------------- #
# 3) Maximal Covering Location Problem (relief shelters)  —  greedy O(p*S*D)
# --------------------------------------------------------------------------- #
@dataclass
class DemandPoint:
    lon: float
    lat: float
    weight: float  # e.g. exposed population


@dataclass
class CandidateSite:
    id: str
    lon: float
    lat: float


def _haversine_km(lon1, lat1, lon2, lat2) -> float:
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    h = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def locate_shelters(
    demand: list[DemandPoint],
    sites: list[CandidateSite],
    p: int,
    radius_km: float,
) -> dict[str, Any]:
    """Choose ``p`` sites maximising covered demand within ``radius_km``.

    MCLP is NP-hard; the greedy algorithm is the classic (1 - 1/e) ≈ 0.632
    approximation because coverage is monotone submodular (Nemhauser et al.,
    1978). Each step picks the site adding the most still-uncovered weight.
    """
    if p <= 0 or not sites or not demand:
        return {"chosen": [], "covered_weight": 0.0, "coverage_pct": 0.0}

    # Precompute coverage sets: site index -> set(demand indices within radius).
    cover: list[set[int]] = []
    for s in sites:
        covered = {
            di for di, d in enumerate(demand)
            if _haversine_km(s.lon, s.lat, d.lon, d.lat) <= radius_km
        }
        cover.append(covered)

    weights = np.array([d.weight for d in demand], dtype=float)
    total = float(weights.sum()) or 1.0
    chosen: list[str] = []
    covered_demand: set[int] = set()

    for _ in range(min(p, len(sites))):
        best_gain, best_idx = -1.0, -1
        for si, cset in enumerate(cover):
            if sites[si].id in chosen:
                continue
            gain = weights[list(cset - covered_demand)].sum() if cset - covered_demand else 0.0
            if gain > best_gain:
                best_gain, best_idx = gain, si
        if best_idx < 0 or best_gain <= 0:
            break
        chosen.append(sites[best_idx].id)
        covered_demand |= cover[best_idx]

    covered_w = float(weights[list(covered_demand)].sum()) if covered_demand else 0.0
    return {
        "chosen": chosen,
        "covered_weight": round(covered_w, 1),
        "coverage_pct": round(covered_w / total * 100, 1),
        "uncovered_pct": round((1 - covered_w / total) * 100, 1),
        "approx_guarantee": "greedy ≥ (1 - 1/e) of optimal (submodular coverage)",
    }


# --------------------------------------------------------------------------- #
# 4) Flood-aware evacuation routing (Dijkstra)  —  O(E log V)
# --------------------------------------------------------------------------- #
@dataclass
class RoadGraph:
    """Adjacency-list weighted graph. edges: node -> list[(neighbor, base_cost, flooded?)]."""

    adj: dict[str, list[tuple[str, float, bool]]] = field(default_factory=dict)

    def add_edge(self, u: str, v: str, cost: float, flooded: bool = False) -> None:
        self.adj.setdefault(u, []).append((v, cost, flooded))
        self.adj.setdefault(v, []).append((u, cost, flooded))


def evacuation_route(
    graph: RoadGraph,
    source: str,
    targets: Iterable[str],
    flood_penalty: float = 1e6,
) -> dict[str, Any]:
    """Least-cost path from ``source`` to the nearest safe ``target``.

    Flooded edges are not deleted but heavily penalised so a route through water
    is only chosen if there is genuinely no alternative — surfacing "no safe
    route" honestly instead of silent failure.
    """
    targets = set(targets)
    dist: dict[str, float] = {source: 0.0}
    prev: dict[str, str] = {}
    pq: list[tuple[float, str]] = [(0.0, source)]
    settled: set[str] = set()

    while pq:
        d, u = heapq.heappop(pq)
        if u in settled:
            continue
        settled.add(u)
        if u in targets:
            path = _reconstruct(prev, source, u)
            return {
                "reachable": True,
                "target": u,
                "cost": round(d, 3),
                "path": path,
                "uses_flooded_edge": d >= flood_penalty,
                "warning": "route crosses flooded road(s)" if d >= flood_penalty else None,
            }
        for v, cost, flooded in graph.adj.get(u, []):
            w = cost + (flood_penalty if flooded else 0.0)
            nd = d + w
            if nd < dist.get(v, math.inf):
                dist[v] = nd
                prev[v] = u
                heapq.heappush(pq, (nd, v))

    return {"reachable": False, "target": None, "cost": math.inf, "path": [],
            "warning": "no route to any safe target"}


def _reconstruct(prev: dict[str, str], source: str, target: str) -> list[str]:
    path = [target]
    while path[-1] != source:
        path.append(prev[path[-1]])
    return list(reversed(path))


# --------------------------------------------------------------------------- #
# 5) Budget-constrained mitigation (0/1 knapsack)  —  DP O(n*B)
# --------------------------------------------------------------------------- #
@dataclass
class Intervention:
    id: str
    cost: float            # currency units
    risk_reduction: float  # abstract reduction value used by the offline knapsack
    effectiveness: float = 0.0  # share (0-1) of exposed population this protects


def mitigation_plan(
    interventions: list[Intervention],
    budget: float,
    granularity: float = 1.0,
) -> dict[str, Any]:
    """Select interventions maximising total risk reduction within ``budget``.

    Classic 0/1 knapsack via Bellman dynamic programming. Costs are discretised
    to ``granularity`` units to bound the table; coarser granularity = faster.
    """
    if budget <= 0 or not interventions:
        return {"selected": [], "total_cost": 0.0, "total_risk_reduction": 0.0}

    B = int(round(budget / granularity))
    items = [(max(1, int(round(it.cost / granularity))), it.risk_reduction, it)
             for it in interventions]

    # dp[b] = best risk reduction with capacity b; keep choice for reconstruction.
    dp = [0.0] * (B + 1)
    take = [[False] * (B + 1) for _ in items]
    for i, (c, val, _it) in enumerate(items):
        for b in range(B, c - 1, -1):
            if dp[b - c] + val > dp[b]:
                dp[b] = dp[b - c] + val
                take[i][b] = True

    # Reconstruct.
    selected, b = [], B
    for i in range(len(items) - 1, -1, -1):
        if take[i][b]:
            selected.append(items[i][2].id)
            b -= items[i][0]
    selected.reverse()

    chosen = [it for it in interventions if it.id in selected]
    return {
        "selected": selected,
        "total_cost": round(sum(it.cost for it in chosen), 2),
        "total_risk_reduction": round(sum(it.risk_reduction for it in chosen), 2),
        "budget": budget,
        "budget_used_pct": round(sum(it.cost for it in chosen) / budget * 100, 1),
    }


# --------------------------------------------------------------------------- #
# AOI bridges — derive OR inputs from a single AOI (deterministic, offline-safe)
# --------------------------------------------------------------------------- #
def default_flood_ahp() -> dict[str, Any]:
    """AHP weights for the canonical 11-factor flood model (Saaty eigenvector + CR).

    Single source of truth lives in ``flood_factors`` so the /optimize endpoint and
    the FloodAI engine always report identical weights.
    """
    from . import flood_factors

    return flood_factors.ahp_report()


def shelters_for_aoi(aoi: dict, p: int = 3, radius_km: float = 8.0,
                     grid_n: int = 12) -> dict[str, Any]:
    """Site relief shelters (MCLP) over an AOI. Uses REAL exposed population
    (WorldPop × flood susceptibility) when online; falls back to a deterministic
    demand surface if GEE is unavailable."""
    from . import aoi as aoi_mod
    from . import gee

    norm = aoi_mod.normalize(aoi)
    if gee.is_live():  # production: demand from real population at flood risk
        try:
            return _shelters_live(norm, p, radius_km, grid_n)
        except Exception as exc:  # pragma: no cover  — fall back to demo demand
            import logging

            logging.getLogger("terrashield.geo.optimize").warning(
                "live shelter demand failed, demo fallback: %s", exc
            )
    return _shelters_demo(norm, p, radius_km, grid_n)


def _shelters_live(norm: dict, p: int, radius_km: float,
                   grid_n: int = 12) -> dict[str, Any]:  # pragma: no cover
    """Demand = WorldPop population masked by moderate-to-high flood susceptibility
    (composite ≥ 3), summed per grid cell in one batched GEE call. Candidate sites
    are the cell centroids; the MCLP greedy then picks the p that cover the most
    exposed population within ``radius_km``."""
    from . import aoi as aoi_mod
    from . import flood_factors, gee

    ee = gee.get_ee()
    bbox = norm["bbox"]
    geom = aoi_mod.to_ee_geometry(norm)
    min_lon, min_lat, max_lon, max_lat = bbox
    dlon = (max_lon - min_lon) / grid_n
    dlat = (max_lat - min_lat) / grid_n

    pop = ee.ImageCollection("WorldPop/GP/100m/pop").filter(
        ee.Filter.eq("year", 2020)
    ).mosaic()
    composite, _factors, _ahp = flood_factors.compute_susceptibility(geom)
    exposed = pop.updateMask(composite.gte(3)).rename("pop")

    cells, centroids = [], []
    for i in range(grid_n):
        for j in range(grid_n):
            lon0 = min_lon + j * dlon
            lat1 = max_lat - i * dlat
            cells.append(ee.Feature(
                ee.Geometry.Rectangle([lon0, lat1 - dlat, lon0 + dlon, lat1]),
                {"i": i, "j": j}))
            centroids.append((i, j, lon0 + dlon / 2, lat1 - dlat / 2))

    red = exposed.reduceRegions(
        collection=ee.FeatureCollection(cells), reducer=ee.Reducer.sum(),
        scale=100, tileScale=4,
    ).getInfo()
    pop_by_ij = {(f["properties"]["i"], f["properties"]["j"]): (f["properties"].get("pop") or 0.0)
                 for f in red["features"]}

    demand, sites = [], []
    for i, j, clon, clat in centroids:
        w = float(pop_by_ij.get((i, j), 0.0))
        if w > 0:
            demand.append(DemandPoint(clon, clat, weight=round(w, 1)))
        sites.append(CandidateSite(id=f"S{i}-{j}", lon=clon, lat=clat))

    if not demand:
        raise ValueError("no exposed population found in this AOI")

    result = locate_shelters(demand, sites, p, radius_km)
    chosen_sites = [s for s in sites if s.id in result["chosen"]]
    result["shelters_geojson"] = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "properties": {"id": s.id, "type": "shelter"},
             "geometry": {"type": "Point", "coordinates": [s.lon, s.lat]}}
            for s in chosen_sites
        ],
    }
    result["source"] = "live"
    result["exposed_population"] = int(sum(d.weight for d in demand))
    result["demand_points"] = len(demand)
    result["candidate_sites"] = len(sites)
    result["radius_km"] = radius_km
    result["aoi"] = {"bbox": bbox, "centroid": norm["centroid"]}
    return result


def _shelters_demo(norm: dict, p: int = 3, radius_km: float = 8.0,
                   grid_n: int = 12) -> dict[str, Any]:
    """Deterministic demand surface (offline fallback): exposed = pop × low-elevation."""
    from . import demo
    bbox = norm["bbox"]
    pop = demo.smooth_field(bbox, grid_n, salt="infra:pop")
    hazard = demo.smooth_field(bbox, grid_n, salt="flood:elevation")  # low elev ~ exposed
    min_lon, min_lat, max_lon, max_lat = bbox
    dlon = (max_lon - min_lon) / grid_n
    dlat = (max_lat - min_lat) / grid_n

    demand, sites = [], []
    for i in range(grid_n):
        for j in range(grid_n):
            lon = min_lon + (j + 0.5) * dlon
            lat = max_lat - (i + 0.5) * dlat
            exposed = float(pop[i, j] * hazard[i, j])
            if exposed > 0.25:
                demand.append(DemandPoint(lon, lat, weight=round(exposed * 1000, 1)))
            if (i + j) % 3 == 0:  # candidate sites on a sparser lattice
                sites.append(CandidateSite(id=f"S{i}-{j}", lon=lon, lat=lat))

    result = locate_shelters(demand, sites, p, radius_km)
    chosen_sites = [s for s in sites if s.id in result["chosen"]]
    result["shelters_geojson"] = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "properties": {"id": s.id, "type": "shelter"},
             "geometry": {"type": "Point", "coordinates": [s.lon, s.lat]}}
            for s in chosen_sites
        ],
    }
    result["demand_points"] = len(demand)
    result["candidate_sites"] = len(sites)
    result["radius_km"] = radius_km
    result["aoi"] = {"bbox": bbox, "centroid": norm["centroid"]}
    return result


def evacuation_for_aoi(aoi: dict, grid_n: int = 10) -> dict[str, Any]:
    """Flood-aware evacuation routing. Uses the REAL OSM road network (Overpass)
    with a GEE flood penalty when online; falls back to a deterministic lattice
    if Overpass/GEE is unavailable.

    Reports human-readable outputs (distance in km, segment count, whether the
    safest available route still crosses flooding) rather than the internal
    penalised path cost.
    """
    from . import aoi as aoi_mod
    from . import gee

    if gee.is_live():  # production: route on the real road network
        try:
            return _evacuation_live(aoi_mod.normalize(aoi))
        except Exception as exc:  # pragma: no cover  — fall back to the lattice
            import logging

            logging.getLogger("terrashield.geo.optimize").warning(
                "OSM evacuation failed, lattice fallback: %s", exc
            )
    return _evacuation_lattice(aoi, grid_n)


def _evacuation_live(norm: dict, flood_penalty: float = 1e6) -> dict[str, Any]:  # pragma: no cover
    """Evacuation on the REAL OSM road network with a GEE flood penalty: edges whose
    midpoint falls in high flood susceptibility (composite ≥ 4, AHP classes 4-5) are
    penalised so the route avoids flooding when a dry alternative exists. Dijkstra to
    the nearest boundary exit. Falls back to the lattice if the road graph is too thin.
    """
    from . import aoi as aoi_mod
    from . import flood_factors, gee, roads

    ee = gee.get_ee()
    bbox = norm["bbox"]
    g = roads.build_graph(roads.fetch_roads(bbox), max_edges=20000)
    if g.number_of_edges() < 5:
        raise ValueError("too few OSM roads in this AOI")

    # Sample flood susceptibility at every edge midpoint in one batched GEE call,
    # then penalise edges that cross high-susceptibility terrain.
    geom = aoi_mod.to_ee_geometry(norm)
    composite, _factors, _ahp = flood_factors.compute_susceptibility(geom)
    edges = list(g.edges())
    feats = [
        ee.Feature(ee.Geometry.Point([(u[1] + v[1]) / 2, (u[0] + v[0]) / 2]), {"idx": i})
        for i, (u, v) in enumerate(edges)
    ]
    sampled = composite.rename("susc").reduceRegions(
        collection=ee.FeatureCollection(feats), reducer=ee.Reducer.first(),
        scale=90, tileScale=4,
    ).getInfo()
    susc_by_idx = {f["properties"]["idx"]: f["properties"].get("susc")
                   for f in sampled["features"]}

    n_flooded = 0
    for i, (u, v) in enumerate(edges):
        susc = susc_by_idx.get(i)
        if susc is not None and susc >= 4:
            g[u][v]["weight"] += flood_penalty
            n_flooded += 1

    route = roads.route_to_exit(g, bbox, flood_penalty=flood_penalty)
    route["source"] = "live"
    route["aoi"] = {"bbox": bbox, "centroid": norm["centroid"]}
    route["stats"] = {
        "road_segments": g.number_of_edges(),
        "flooded_segments": n_flooded,
        "method": "Dijkstra on OSM roads; edges in high flood susceptibility penalised",
    }
    return route


def _evacuation_lattice(aoi: dict, grid_n: int = 10) -> dict[str, Any]:
    """Synthetic-lattice evacuation fallback (deterministic; works without GEE).
    Builds a lattice road graph, flags flooded edges from the susceptibility
    surface, and routes the most at-risk core node to the nearest safe exit."""
    from . import aoi as aoi_mod
    from . import demo

    norm = aoi_mod.normalize(aoi)
    bbox = norm["bbox"]
    risk = demo.smooth_field(bbox, grid_n, salt="flood:elevation")
    min_lon, min_lat, max_lon, max_lat = bbox
    dlon = (max_lon - min_lon) / (grid_n - 1)
    dlat = (max_lat - min_lat) / (grid_n - 1)
    flood_threshold = 0.62

    def node(i, j):
        return f"{i}_{j}"

    def coord(i, j):
        return [min_lon + j * dlon, max_lat - i * dlat]

    def edge_flooded(i, j, ni, nj):
        return (risk[i, j] + risk[ni, nj]) / 2 > flood_threshold

    g = RoadGraph()
    for i in range(grid_n):
        for j in range(grid_n):
            for di, dj in ((0, 1), (1, 0)):
                ni, nj = i + di, j + dj
                if ni < grid_n and nj < grid_n:
                    # Physical edge length (km) is the real traversal cost.
                    length = _haversine_km(*coord(i, j), *coord(ni, nj))
                    g.add_edge(node(i, j), node(ni, nj), cost=length,
                               flooded=edge_flooded(i, j, ni, nj))

    # Source = the most at-risk neighbourhood within the inner core (away from the
    # border) so the route is representative and non-trivial; km-weighted Dijkstra
    # then finds the shortest path to a safe exit, routing around flooding.
    lo, hi = max(1, grid_n // 4), min(grid_n - 1, 3 * grid_n // 4)
    core = [(risk[i, j], i, j) for i in range(lo, hi) for j in range(lo, hi)]
    _, si, sj = max(core) if core else (0, grid_n // 2, grid_n // 2)
    source = node(si, sj)
    targets = [
        node(i, j) for i in range(grid_n) for j in range(grid_n)
        if (i in (0, grid_n - 1) or j in (0, grid_n - 1)) and risk[i, j] < 0.45
    ] or [node(0, 0)]

    route = evacuation_route(g, source, targets)

    # Derive human-readable metrics along the chosen path.
    path = route["path"]
    route_km, crosses = 0.0, False
    for a, b in zip(path, path[1:]):
        ai, aj = map(int, a.split("_"))
        bi, bj = map(int, b.split("_"))
        route_km += _haversine_km(*coord(ai, aj), *coord(bi, bj))
        if edge_flooded(ai, aj, bi, bj):
            crosses = True

    route["route_km"] = round(route_km, 2)
    route["segments"] = max(len(path) - 1, 0)
    route["crosses_flood"] = crosses
    route["uses_flooded_edge"] = crosses
    route["route_geojson"] = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {"type": "evacuation_route", "route_km": round(route_km, 2),
                           "crosses_flood": crosses},
            "geometry": {
                "type": "LineString",
                "coordinates": [coord(int(n.split("_")[0]), int(n.split("_")[1])) for n in path],
            },
        }] if path else [],
    }
    route["source"] = source
    route["aoi"] = {"bbox": bbox, "centroid": norm["centroid"]}
    return route


DEFAULT_INTERVENTIONS = [
    Intervention("levee_upgrade", cost=120.0, risk_reduction=45.0, effectiveness=0.35),
    Intervention("drainage_expansion", cost=80.0, risk_reduction=30.0, effectiveness=0.22),
    Intervention("early_warning_network", cost=25.0, risk_reduction=22.0, effectiveness=0.18),
    Intervention("wetland_restoration", cost=40.0, risk_reduction=18.0, effectiveness=0.12),
    Intervention("road_elevation", cost=95.0, risk_reduction=28.0, effectiveness=0.20),
    Intervention("retention_ponds", cost=55.0, risk_reduction=20.0, effectiveness=0.15),
]


def mitigation_for_aoi(aoi: dict, budget: float,
                       interventions: list[Intervention] | None = None) -> dict[str, Any]:
    """Budget-constrained mitigation grounded in the AOI's REAL flood-exposed
    population. Each intervention protects ``effectiveness`` × exposed_population
    people; the 0/1 knapsack picks the subset maximising protected population within
    ``budget``. Falls back to the abstract risk-reduction index when exposure can't
    be computed (offline) or interventions carry no effectiveness fraction."""
    from . import infra

    items = interventions or DEFAULT_INTERVENTIONS
    exposed, source = 0, "demo"
    try:
        exp = infra.exposure(aoi, "flood")
        exposed = int(exp.get("stats", {}).get("population_exposed", 0) or 0)
        source = exp.get("source", "demo")
    except Exception:  # pragma: no cover
        pass

    if exposed > 0 and all(getattr(it, "effectiveness", 0) > 0 for it in items):
        scaled = [Intervention(it.id, it.cost,
                               risk_reduction=round(it.effectiveness * exposed, 1),
                               effectiveness=it.effectiveness)
                  for it in items]
        plan = mitigation_plan(scaled, budget)
        # Protection is not additively independent — cap the headline at the
        # exposed population so we never claim to protect more people than exist.
        plan["total_risk_reduction"] = min(plan["total_risk_reduction"], float(exposed))
        plan["units"] = "people protected (flood-exposed)"
        plan["exposed_population"] = exposed
    else:
        plan = mitigation_plan(items, budget)
        plan["units"] = "relative risk-reduction index"
    plan["source"] = source
    return plan
