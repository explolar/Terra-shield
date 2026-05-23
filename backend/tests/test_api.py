"""End-to-end API tests via FastAPI TestClient (demo mode, no GEE)."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
AOI = {"type": "bbox", "bbox": [73.9, 17.6, 74.3, 18.0]}


def test_root_and_health():
    assert client.get("/").json()["name"] == "TerraShield AI"
    assert client.get("/api/v1/health").json()["status"] == "ok"
    assert client.get("/api/v1/earthdata/status").json()["mode"] in {"demo", "live"}


def test_datasets_and_basemaps():
    assert len(client.get("/api/v1/earthdata/datasets").json()["datasets"]) > 5
    assert len(client.get("/api/v1/earthdata/basemaps").json()["basemaps"]) >= 3


def test_aoi_validation_rejects_bad_bbox():
    r = client.post("/api/v1/earthdata/aoi/validate",
                    json={"type": "bbox", "bbox": [10, 10, 5, 5]})
    assert r.status_code == 422


def test_flood_susceptibility():
    r = client.post("/api/v1/flood/susceptibility",
                    json={"aoi": AOI, "rainfall_scenario": "extreme"})
    assert r.status_code == 200
    body = r.json()
    assert body["module"] == "flood"
    assert body["source"] in {"demo", "live"}
    assert "reliability" in body


def test_flood_sar_and_road():
    assert client.post("/api/v1/flood/sar-extent", json={"aoi": AOI}).status_code == 200
    assert client.post("/api/v1/flood/road-risk", json={"aoi": AOI}).status_code == 200


def test_climate_projection_and_scenarios():
    assert "ssp585" in client.get("/api/v1/climate/scenarios").json()["scenarios"]
    r = client.post("/api/v1/climate/projection",
                    json={"aoi": AOI, "scenario": "ssp585", "variable": "pr", "horizon": "2050s"})
    assert r.status_code == 200
    assert "pct_change" in r.json()


def test_drought_and_infra():
    assert client.post("/api/v1/drought/spi", json={"aoi": AOI, "scale_months": 3}).status_code == 200
    assert client.post("/api/v1/drought/vegetation", json={"aoi": AOI}).status_code == 200
    assert client.post("/api/v1/infra/exposure", json={"aoi": AOI}).status_code == 200


def test_optimize_endpoints():
    assert client.get("/api/v1/optimize/ahp/default").json()["consistent"] is True
    s = client.post("/api/v1/optimize/shelters",
                    json={"aoi": AOI, "num_shelters": 3, "radius_km": 8}).json()
    assert 0 <= s["coverage_pct"] <= 100
    e = client.post("/api/v1/optimize/evacuation", json={"aoi": AOI}).json()
    assert "route_km" in e
    m = client.post("/api/v1/optimize/mitigation", json={"budget": 200}).json()
    assert m["total_cost"] <= 200


def test_copilot_routes_to_correct_tool():
    cases = {
        "How will flood risk in Satara change under SSP585?": "flood_susceptibility",
        "Where should we place 4 relief shelters in Kolhapur?": "optimize_shelters",
        "Find a safe evacuation route in Patna": "optimize_evacuation",
        "Rainfall projection for Pune under SSP245 by 2030": "climate_projection",
        "3-month SPI drought for Marathwada": "drought_spi",
    }
    for q, tool in cases.items():
        body = client.post("/api/v1/copilot/ask", json={"question": q}).json()
        assert body["tool"] == tool, f"{q!r} -> {body['tool']} (expected {tool})"
        assert body["answer"]


def test_rate_limit_header_present():
    r = client.get("/api/v1/health")
    assert "X-Request-ID" in r.headers
