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

**Flood · Climate · Drought · Groundwater · Weather · Infrastructure risk — plus operations-research decisions and a Llama copilot. Unified, queryable, deployable.**

</div>

---

## What is TerraShield AI?

TerraShield AI turns scattered Earth-observation data, climate model output, and hydrology into **one operational decision system** for climate risk. Instead of a researcher juggling rasters in a notebook, a planner asks a question — *"How does flood risk in this district change under SSP585?"* — and gets a map, a number, and an explanation.

It is built as a **modular platform**, not a single model: a geospatial compute engine, a typed API, an interactive map workspace, and a GenAI copilot that orchestrates them.

> **Status:** Active development. **9 modules** expose working, typed APIs with a deterministic offline demo mode *and* live Google Earth Engine paths (verified live across FloodAI, ClimateLens, DroughtAI, InfraRisk, GroundwaterAI). FloodAI is the deepest vertical (11-factor AHP, calibrated SAR, multi-year, ML+SHAP). National coverage: every Indian state + 482 districts resolvable by name in GeoCopilot. **Tests: 27 geo-engine + 13 backend, green.** Deepening on the [roadmap](docs/roadmap.md).

---

## Core Modules

| Module | Purpose | Key inputs |
|--------|---------|-----------|
| 🌊 **FloodAI** | **11-factor AHP-MCDM** susceptibility (Saaty eigenvector + CR validation, per-factor layers, AOA reliability) · **6-layer calibrated SAR** inundation + 3-class severity + crop/built-up/population exposure · **multi-year** trend (2019–24) · **ML risk** (GBM/XGBoost/RF + SHAP) · road-access disruption | dist-to-river, HAND, rainfall, slope, elevation, drainage density, TWI, LULC, soil, NDVI, curvature; Sentinel-1; JRC GSW; WorldPop |
| 🌡️ **ClimateLens** | CMIP6 / SSP projections & anomalies · **ETCCDI extreme indices** (Rx1day, R95p, CDD, hot-days) | NEX-GDDP-CMIP6 (SSP245/585) |
| 🌵 **DroughtAI** | Gamma-fit **SPI** (1/3/6/12-mo) + NDVI/**VCI** vegetation stress | CHIRPS, MODIS |
| 🛣️ **InfraRisk** | Population / built-up **exposure** · **road-network criticality** (edge betweenness) | ESA WorldCover, WorldPop, SRTM |
| 🧮 **ResilienceOR** | AHP weights, TOPSIS ranking, relief-shelter siting (MCLP), evacuation routing (Dijkstra), mitigation knapsack | hazard layers + constraints |
| 🌦️ **WeatherCast** | 1–16 day **rainfall/weather forecast** + heavy-rain flood watch | Open-Meteo (free, no key) |
| 💧 **GroundwaterAI** | **GRACE** terrestrial water-storage anomaly, **depletion trend** (cm/yr) → stress class, recharge proxy | NASA GRACE/GRACE-FO, CHIRPS, MODIS ET |
| 🤖 **GeoCopilot** | Natural-language assistant (**Llama** via Groq/Ollama) — resolves any of India's 482 districts, calls the right tool, explains results; **grounded** (never invents numbers), input cleaned + guardrailed | tool-calling over the platform APIs |
| ⚙️ **EarthData Engine** | Shared geospatial backend: GEE auth, tiling, AOI, indices, 492-place India gazetteer — deterministic offline demo mode | Google Earth Engine |

See [`docs/modules.md`](docs/modules.md) for the per-module API contract and [`docs/engineering.md`](docs/engineering.md) for the algorithms, data structures, and complexity.

### Ask GeoCopilot (natural language → live analysis)
```
"How will flood risk in Satara change under SSP585 by 2050?"
"Show the most critical roads in Mumbai"
"Where should we place 4 relief shelters in Kolhapur?"
"Groundwater depletion in Punjab"      ·  "Heatwave days in Delhi under SSP585"
"Rainfall forecast for Pune next week" ·  "Train an XGBoost flood-risk model for Patna"
```

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
│  /flood /climate /drought /infra /optimize /weather           │
│  /groundwater /copilot /earthdata                             │
│  config · logging · TTL cache · rate limiting · CORS · guardrails │
└───────────────────────────┬─────────────────────────────────┘
                            │  imports
┌───────────────────────────▼─────────────────────────────────┐
│  geo-engine (EarthData Engine)  ·  Python package             │
│  gee · aoi · indices · flood · flood_factors(AHP) · ml_flood  │
│  climate · drought · infra · groundwater · optimize · tiles   │
│  → graceful demo fallback when GEE creds are absent           │
└───────────────────────────┬─────────────────────────────────┘
                            │
   GEE · NEX-GDDP-CMIP6 · CHIRPS · Sentinel-1/2 · SRTM/MERIT · GRACE · JRC GSW
   WorldPop · ESA WorldCover · MODIS · OSM · Open-Meteo (forecast)
```

Full diagram and data-flow: [`docs/architecture.md`](docs/architecture.md).

---

## Repository layout

```
terra-shield/
├── backend/         FastAPI service — thin orchestration + API contract
│   └── app/{core,api/routes,schemas,services}   # core/sanitize.py (guardrails),
│                                                # services/{llm,copilot,weather}.py
├── geo-engine/      EarthData Engine — geospatial compute library (terrashield_geo)
│   └── terrashield_geo/   gee · aoi · indices · flood · flood_factors · ml_flood ·
│                          climate · drought · infra · groundwater · optimize · data/
├── frontend/        Next.js 14 map workspace + 9 module panels (+ public/geo India boundaries)
├── infra/           Dockerfiles, docker-compose, GitHub Actions deploy notes
├── scripts/         build_geo_assets.py (shapefile→GeoJSON+gazetteer), smoke_test.py, dev.ps1/.bat
├── data/            india_shape/ (source boundaries)
├── docs/            architecture · modules · engineering · roadmap · research-notes ·
│                    oss-landscape · feature-backlog
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

### Enabling the Llama copilot (optional)

GeoCopilot works without an LLM (deterministic grounded answers). To have **Llama** write the prose, set in `.env`:

```bash
TERRASHIELD_LLM_PROVIDER=groq          # or "ollama" for local
TERRASHIELD_LLM_API_KEY=gsk_...        # from console.groq.com (free)
TERRASHIELD_LLM_MODEL=llama-3.3-70b-versatile
```

The LLM is **grounded** (it may only phrase engine-computed numbers) and guardrailed (input cleaning + prompt-injection filter + output caps in [`backend/app/core/sanitize.py`](backend/app/core/sanitize.py)).

### Quick check (no servers)

```bash
python scripts/smoke_test.py     # exercises every module and prints a report
```

---

## Roadmap

A focused, phase-based plan (foundation → flood → climate → copilot → deploy → polish) lives in [`docs/roadmap.md`](docs/roadmap.md). The guiding principle: **one killer vertical (FloodAI) end-to-end first, then breadth.**

---

## License

Apache 2.0 — see [`LICENSE`](LICENSE). Earth-observation datasets retain their original licenses (see [`docs/modules.md`](docs/modules.md)).

<div align="center">
<sub>Built in India. Built for a warming world.</sub>
</div>
