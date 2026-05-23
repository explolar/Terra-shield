<div align="center">

# 🌍 TerraShield AI

### The AI Operating System for Climate Risk & Resilience

![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-backend-009688?logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js%2014-frontend-000?logo=nextdotjs&logoColor=white)
![Earth Engine](https://img.shields.io/badge/Google%20Earth%20Engine-geodata-34A853?logo=googleearth&logoColor=white)
![Leaflet](https://img.shields.io/badge/Leaflet-maps-199900?logo=leaflet&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-containerized-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/license-Apache%202.0-lightgrey)

**Flood intelligence · Climate projections · Drought stress · Infrastructure risk — unified, queryable, deployable.**

</div>

---

## What is TerraShield AI?

TerraShield AI turns scattered Earth-observation data, climate model output, and hydrology into **one operational decision system** for climate risk. Instead of a researcher juggling rasters in a notebook, a planner asks a question — *"How does flood risk in this district change under SSP585?"* — and gets a map, a number, and an explanation.

It is built as a **modular platform**, not a single model: a geospatial compute engine, a typed API, an interactive map workspace, and a GenAI copilot that orchestrates them.

> **Status:** Active development. FloodAI is the flagship vertical (deepest). All seven modules expose working, typed APIs with deterministic offline analytics (live Earth Engine is a config flip). National coverage: every Indian state + 482 districts are resolvable by name. Tests: 22 geo-engine + 10 backend, green. Deepening on the [roadmap](docs/roadmap.md).

---

## Core Modules

| Module | Purpose | Key inputs | Depth |
|--------|---------|-----------|:-----:|
| 🌊 **FloodAI** | Paper-grade **11-factor AHP-MCDM** susceptibility (Saaty eigenvector + CR validation, per-factor layers), Otsu SAR inundation extent, road-access disruption, + Area-of-Applicability reliability | dist-to-river, HAND, rainfall, slope, elevation, drainage density, TWI, LULC, soil, NDVI, curvature, Sentinel-1 | **Flagship** |
| 🌡️ **ClimateLens** | CMIP6 / SSP future-climate projections & anomalies | NEX-GDDP-CMIP6 (SSP245/585), ERA5 | Working |
| 🌵 **DroughtAI** | Meteorological + vegetation drought (SPI, NDVI/VCI anomaly) | CHIRPS, MODIS/Sentinel-2 | Working |
| 🛣️ **InfraRisk** | Population / infrastructure exposure under hazard | ESA WorldCover, WorldPop, OSM | Working |
| 🧮 **ResilienceOR** | Operations research: AHP weights, TOPSIS ranking, relief-shelter siting (MCLP), evacuation routing (Dijkstra), mitigation knapsack | hazard layers + constraints | Working |
| 🤖 **GeoCopilot** | Natural-language assistant (Llama) that resolves any of India's 482 districts, runs analytics & explains results — grounded, never invents numbers | tool-calling over the platform APIs | Working |
| ⚙️ **EarthData Engine** | The shared geospatial backend: GEE auth, tiling, AOI, indices — with deterministic offline demo mode | Google Earth Engine | Working |

See [`docs/modules.md`](docs/modules.md) for the per-module API contract and [`docs/engineering.md`](docs/engineering.md) for the algorithms, data structures, and complexity.

---

## Architecture (at a glance)

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend  ·  Next.js 14 + Tailwind + Leaflet + Recharts      │
│  Map workspace · module panels · GeoCopilot chat              │
└───────────────────────────┬─────────────────────────────────┘
                            │  typed REST (JSON / GeoJSON / tile URLs)
┌───────────────────────────▼─────────────────────────────────┐
│  Backend  ·  FastAPI (async)                                  │
│  /flood /climate /drought /infra /optimize /copilot /earthdata │
│  config · logging · TTL cache · rate limiting · CORS          │
└───────────────────────────┬─────────────────────────────────┘
                            │  imports
┌───────────────────────────▼─────────────────────────────────┐
│  geo-engine (EarthData Engine)  ·  Python package             │
│  GEE auth+init · AOI · spectral indices · flood/climate/      │
│  drought/infra compute · tile (mapid) serving                 │
│  → graceful demo fallback when GEE creds are absent           │
└───────────────────────────┬─────────────────────────────────┘
                            │
        Google Earth Engine · NEX-GDDP-CMIP6 · CHIRPS · Sentinel-1/2 · SRTM · OSM
```

Full diagram and data-flow: [`docs/architecture.md`](docs/architecture.md).

---

## Repository layout

```
terra-shield/
├── backend/         FastAPI service — thin orchestration + API contract
│   └── app/{core,api/routes,schemas,services}   # services/ holds llm.py (Llama) + copilot.py
├── geo-engine/      EarthData Engine — geospatial compute library (terrashield_geo)
│   └── terrashield_geo/   gee · aoi · flood · climate · drought · infra · optimize · data/
├── frontend/        Next.js 14 map workspace + module panels (+ public/geo India boundaries)
├── infra/           Dockerfiles, docker-compose, deploy notes
├── scripts/         build_geo_assets.py (shapefile→GeoJSON+gazetteer), dev.ps1
├── data/            india_shape/ (source boundaries)
├── docs/            architecture · modules · engineering · roadmap · research-notes · oss-landscape
├── notebooks/       research / validation notebooks
└── .github/         CI workflows
```

---

## Quick start (local)

> The platform runs **without** Google Earth Engine credentials — the geo-engine returns deterministic demo layers so you can develop the full UX offline. Add GEE creds to switch to live data.

```bash
# 1) Backend + geo-engine
cd backend
python -m venv .venv && . .venv/Scripts/activate      # Windows: .venv\Scripts\Activate.ps1
pip install -e ../geo-engine -e .[dev]
python -m uvicorn app.main:app --reload --port 8000
# → http://localhost:8000/docs   (interactive API)
# (use `python -m uvicorn` — the bare `uvicorn` command needs the Scripts dir on PATH)

# 2) Frontend  (second terminal)
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

Or the whole stack with Docker:

```bash
docker compose -f infra/docker-compose.yml up --build
```

### Enabling live Earth Engine data

```bash
# Option A: local OAuth
earthengine authenticate
export TERRASHIELD_GEE_PROJECT=your-gcp-project   # PowerShell: $env:TERRASHIELD_GEE_PROJECT="..."

# Option B: service account (CI / Cloud Run)
export TERRASHIELD_GEE_SA_KEY=/path/to/service-account.json
```

See [`.env.example`](.env.example) for all configuration.

---

## Roadmap

A focused, phase-based plan (foundation → flood → climate → copilot → deploy → polish) lives in [`docs/roadmap.md`](docs/roadmap.md). The guiding principle: **one killer vertical (FloodAI) end-to-end first, then breadth.**

---

## License

Apache 2.0 — see [`LICENSE`](LICENSE). Earth-observation datasets retain their original licenses (see [`docs/modules.md`](docs/modules.md)).

<div align="center">
<sub>Built in India. Built for a warming world.</sub>
</div>
