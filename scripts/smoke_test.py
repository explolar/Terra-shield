"""TerraShield AI — full-platform smoke test / demo report.

Exercises every module through the FastAPI app (in-process, demo mode) and prints
a readable report. Great for a quick "does everything work?" check or a live demo.

Run:  python scripts/smoke_test.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make the backend importable when run from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)
AOI = {"type": "bbox", "bbox": [73.9, 17.6, 74.3, 18.0]}  # Satara, Maharashtra


def section(title: str) -> None:
    print(f"\n{'─' * 64}\n  {title}\n{'─' * 64}")


def main() -> None:
    print("=" * 64)
    print("  TerraShield AI — platform smoke test")
    print("=" * 64)
    root = client.get("/").json()
    print(f"  {root['name']} · EarthData Engine = {root['earthdata_engine'].upper()}")
    print(f"  modules: {', '.join(root['modules'])}")

    section("FloodAI")
    f = client.post("/api/v1/flood/susceptibility",
                    json={"aoi": AOI, "rainfall_scenario": "extreme"}).json()
    print(f"  susceptibility: mean={f['stats']['mean']} "
          f"high-risk={f['stats'].get('high_risk_pct')}% "
          f"reliability={f['reliability']['applicable_pct']}% applicable")
    sar = client.post("/api/v1/flood/sar-extent", json={"aoi": AOI}).json()
    print(f"  SAR extent: {sar['stats']['flooded_area_km2']} km² flooded")
    road = client.post("/api/v1/flood/road-risk", json={"aoi": AOI}).json()
    print(f"  road risk: {road['stats']['roads_disrupted']}/{road['stats']['roads_total']} segments disrupted")

    section("ClimateLens")
    c = client.post("/api/v1/climate/projection",
                    json={"aoi": AOI, "scenario": "ssp585", "variable": "pr", "horizon": "2050s"}).json()
    print(f"  precip SSP585 2050s: {c['baseline']} -> {c['projected']} {c['unit']} ({c['pct_change']:+}%)")

    section("DroughtAI")
    spi = client.post("/api/v1/drought/spi", json={"aoi": AOI, "scale_months": 3}).json()
    print(f"  SPI-3: mean={spi['stats']['mean_spi']} ({spi['stats']['class']})")

    section("InfraRisk")
    infra = client.post("/api/v1/infra/exposure", json={"aoi": AOI}).json()
    print(f"  exposure: {infra['stats']['population_exposed']:,}/{infra['stats']['population_total']:,} people")

    section("ResilienceOR")
    ahp = client.get("/api/v1/optimize/ahp/default").json()
    print(f"  AHP weights (CR={ahp['consistency_ratio']}, consistent={ahp['consistent']})")
    sh = client.post("/api/v1/optimize/shelters", json={"aoi": AOI, "num_shelters": 3, "radius_km": 8}).json()
    print(f"  shelters: 3 centres cover {sh['coverage_pct']}% of exposed demand")
    ev = client.post("/api/v1/optimize/evacuation", json={"aoi": AOI}).json()
    print(f"  evacuation: {ev['route_km']} km, {ev['segments']} segments, crosses_flood={ev['crosses_flood']}")
    mit = client.post("/api/v1/optimize/mitigation", json={"budget": 200}).json()
    print(f"  mitigation: risk reduction {mit['total_risk_reduction']} at {mit['budget_used_pct']}% budget")

    section("GeoCopilot")
    for q in ["How will flood risk in Satara change under SSP585 by 2050?",
              "Where should we place 4 relief shelters in Kolhapur?",
              "3-month drought outlook for Nagpur"]:
        a = client.post("/api/v1/copilot/ask", json={"question": q}).json()
        print(f"  Q: {q}\n     -> [{a['tool']}] {a['answer'][:140]}")

    print("\n" + "=" * 64)
    print("  ✓ all modules responded")
    print("=" * 64)


if __name__ == "__main__":
    main()
