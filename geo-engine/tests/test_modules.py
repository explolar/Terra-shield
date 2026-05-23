"""Demo-mode behaviour of the analytic modules (no GEE required)."""
import numpy as np

from terrashield_geo import climate, demo, drought, flood, infra

AOI = {"type": "bbox", "bbox": [73.9, 17.6, 74.3, 18.0]}


def test_demo_field_is_deterministic():
    a = demo.smooth_field([73.9, 17.6, 74.3, 18.0], 16, "x")
    b = demo.smooth_field([73.9, 17.6, 74.3, 18.0], 16, "x")
    assert np.array_equal(a, b)
    assert a.min() >= 0 and a.max() <= 1


def test_demo_field_changes_with_aoi():
    a = demo.smooth_field([73.9, 17.6, 74.3, 18.0], 16, "x")
    b = demo.smooth_field([80.0, 20.0, 80.4, 20.4], 16, "x")
    assert not np.array_equal(a, b)


def test_flood_susceptibility_shape_and_reliability():
    r = flood.susceptibility(AOI, rainfall_scenario="extreme")
    assert r["source"] == "demo"
    assert r["product"] == "susceptibility"
    assert 0 <= r["stats"]["mean"] <= 1
    assert "reliability" in r and 0 <= r["reliability"]["applicable_pct"] <= 100
    assert len(r["grid"]["features"]) == 24 * 24
    assert "confidence" in r["grid"]["features"][0]["properties"]
    assert abs(sum(r["weights"].values()) - 1.0) < 1e-6


def test_flood_weights_normalize():
    r = flood.susceptibility(AOI, weights={"elevation": 10, "slope": 10})
    assert abs(sum(r["weights"].values()) - 1.0) < 1e-6


def test_flood_ahp_matrix_sets_weights():
    from terrashield_geo import flood_factors

    r = flood.susceptibility(AOI, ahp_matrix=flood_factors.AHP_MATRIX)
    assert r["ahp"]["consistent"] is True
    assert len(r["weights"]) == 11
    assert r["weights"]["distance_to_river"] == max(r["weights"].values())


def test_climate_projection_signal_direction():
    wet = climate.projection(AOI, "ssp585", "pr", "2080s")
    mild = climate.projection(AOI, "ssp245", "pr", "2030s")
    assert wet["pct_change"] > mild["pct_change"]  # stronger scenario/horizon -> more change
    assert len(wet["timeseries"]) > 10


def test_drought_spi_in_range():
    r = drought.spi(AOI, 3)
    assert -3 <= r["stats"]["mean_spi"] <= 3
    assert r["stats"]["class"]


def test_infra_exposure_subset_of_total():
    r = infra.exposure(AOI)
    assert r["stats"]["population_exposed"] <= r["stats"]["population_total"]


def test_climate_extremes_increase_under_warming():
    r = climate.extremes(AOI, "ssp585", "2080s")
    assert len(r["indices"]) == 4
    hot = next(i for i in r["indices"] if i["key"] == "hot_days")
    rx = next(i for i in r["indices"] if i["key"] == "rx1day")
    assert hot["projected"] >= hot["baseline"]   # more hot days in a warmer world
    assert rx["projected"] >= rx["baseline"]     # heavier 1-day extremes


def test_infra_road_criticality():
    r = infra.road_criticality(AOI)
    assert r["stats"]["segments"] > 0
    vals = [f["properties"]["criticality"] for f in r["grid"]["features"]]
    assert max(vals) <= 1.0 and min(vals) >= 0.0
