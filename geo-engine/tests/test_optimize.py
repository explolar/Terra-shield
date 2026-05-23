import pytest

from terrashield_geo import optimize as opt


# ---- AHP ----------------------------------------------------------------- #
def test_ahp_perfectly_consistent_matrix():
    # a_ij = w_i / w_j for w = [0.5, 0.25, 0.25] is perfectly consistent (CR=0).
    m = [[1, 2, 2], [0.5, 1, 1], [0.5, 1, 1]]
    res = opt.ahp_weights(m, ["a", "b", "c"])
    assert res["consistent"] is True
    assert res["consistency_ratio"] == pytest.approx(0.0, abs=1e-6)
    assert res["weights"]["a"] == pytest.approx(0.5, abs=1e-3)
    assert sum(res["weights"].values()) == pytest.approx(1.0, abs=1e-6)


def test_ahp_default_flood_is_consistent():
    res = opt.default_flood_ahp()
    assert res["consistent"] is True
    assert res["consistency_ratio"] <= 0.10
    assert res["n_factors"] == 11
    # Distance to river is the highest-priority factor in the 11-factor model.
    assert res["weights"]["distance_to_river"] == max(res["weights"].values())


def test_ahp_rejects_non_positive():
    with pytest.raises(ValueError):
        opt.ahp_weights([[1, 0], [0, 1]])


# ---- TOPSIS -------------------------------------------------------------- #
def test_topsis_ranks_lowest_risk_best_when_cost_criteria():
    # all criteria are "cost" (smaller is better); the all-min alternative wins.
    res = opt.topsis(
        ["safe", "mid", "bad"],
        [[0.1, 100], [0.5, 500], [0.9, 900]],
        weights=[0.5, 0.5],
        benefit=[False, False],
    )
    assert res["best"] == "safe"
    assert res["ranking"][0]["alternative"] == "safe"
    assert res["ranking"][-1]["alternative"] == "bad"


# ---- Knapsack ------------------------------------------------------------ #
def test_knapsack_finds_known_optimum():
    items = [
        opt.Intervention("A", cost=120, risk_reduction=45),
        opt.Intervention("B", cost=80, risk_reduction=30),
        opt.Intervention("C", cost=25, risk_reduction=22),
        opt.Intervention("D", cost=40, risk_reduction=18),
        opt.Intervention("E", cost=55, risk_reduction=20),
    ]
    res = opt.mitigation_plan(items, budget=200)
    # Optimal under budget 200 is B+C+D+E = cost 200, reduction 90.
    assert res["total_risk_reduction"] == pytest.approx(90.0)
    assert res["total_cost"] <= 200
    assert set(res["selected"]) == {"B", "C", "D", "E"}


# ---- MCLP coverage ------------------------------------------------------- #
def test_mclp_coverage_is_monotonic_in_p():
    demand = [opt.DemandPoint(lon=i * 0.1, lat=0.0, weight=1.0) for i in range(20)]
    sites = [opt.CandidateSite(id=f"S{i}", lon=i * 0.1, lat=0.0) for i in range(20)]
    c1 = opt.locate_shelters(demand, sites, p=1, radius_km=10)["coverage_pct"]
    c3 = opt.locate_shelters(demand, sites, p=3, radius_km=10)["coverage_pct"]
    assert c3 >= c1
    assert 0 <= c3 <= 100


# ---- Dijkstra ------------------------------------------------------------ #
def test_dijkstra_shortest_path_simple_graph():
    g = opt.RoadGraph()
    g.add_edge("A", "B", 1)
    g.add_edge("B", "C", 1)
    g.add_edge("A", "C", 5)
    res = opt.evacuation_route(g, "A", ["C"])
    assert res["reachable"] is True
    assert res["cost"] == pytest.approx(2.0)
    assert res["path"] == ["A", "B", "C"]


def test_dijkstra_prefers_dry_route_over_flooded():
    g = opt.RoadGraph()
    g.add_edge("A", "X", 1, flooded=True)   # direct but flooded
    g.add_edge("A", "B", 1)
    g.add_edge("B", "X", 1)                  # longer but dry
    res = opt.evacuation_route(g, "A", ["X"])
    assert res["path"] == ["A", "B", "X"]
    assert res["uses_flooded_edge"] is False


def test_dijkstra_unreachable():
    g = opt.RoadGraph()
    g.add_edge("A", "B", 1)
    res = opt.evacuation_route(g, "A", ["Z"])
    assert res["reachable"] is False
