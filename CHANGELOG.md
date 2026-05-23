# Changelog

All notable changes to TerraShield AI are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/). Versioning: SemVer.

## [0.2.0] — Live data, FluviaAI depth, water modules (unreleased)

### Added
- **Live Google Earth Engine** paths verified across FloodAI, ClimateLens,
  DroughtAI, InfraRisk, GroundwaterAI (project-configurable; demo fallback intact).
- **FloodAI depth** (from the FluviaAI methodology):
  - **11-factor AHP-MCDM** susceptibility (`flood_factors.py`) — Saaty matrix,
    eigenvector weights, CR validation (CR≈0.026), per-factor 1–5 layers.
  - **6-layer calibrated SAR** mask + 3-class severity + crop-loss / built-up /
    population exposure.
  - **Multi-year** flood-extent trend (2019–2024).
  - **ML flood-risk** classifiers (GBM/XGBoost/RF) + **SHAP** (`ml_flood.py`),
    labelled by JRC historical flood occurrence.
- **ClimateLens**: ETCCDI extreme indices (Rx1day, R95p, CDD, hot-days).
- **DroughtAI**: scientifically-correct gamma-fit SPI (McKee 1993).
- **InfraRisk**: road-network criticality via edge-betweenness (NetworkX).
- **WeatherCast** (new module): Open-Meteo 1–16 day rainfall/weather forecast +
  heavy-rain flood watch (free, no key).
- **GroundwaterAI** (new module): NASA GRACE/GRACE-FO water-storage anomaly,
  depletion trend (cm/yr) → stress class, CHIRPS−ET recharge proxy.
- **GeoCopilot**: Llama (Groq/Ollama) wired and grounded; tools for every module;
  **guardrails** — input cleaning + prompt-injection filter + output caps
  (`core/sanitize.py`); per-call AOI cap so coarse (GRACE/CMIP6) data works at
  state/basin scale.
- **Frontend**: light/white responsive theme; India boundary overlays; UI panels
  for all 9 modules incl. 11-slider AHP + per-factor toggles, SAR severity, multi-year,
  ML+SHAP, extremes, criticality, WeatherCast, GroundwaterAI.

### Changed
- Tests grew to **27 geo-engine + 13 backend** (all green).

## [0.1.0] — Foundation (unreleased)

### Added
- **Monorepo**: `backend` (FastAPI), `geo-engine` (`terrashield_geo`),
  `frontend` (Next.js 14), `infra`, `docs`, `scripts`.
- **EarthData Engine** (`geo-engine`): single Earth Engine gateway with a
  deterministic **demo fallback** so the whole stack runs offline; AOI utils,
  spectral indices, tile/legend helpers, dataset catalog.
- **FloodAI**: AHP-weighted multi-criteria susceptibility, Sentinel-1 SAR extent,
  road-access disruption, and an Area-of-Applicability reliability mask.
- **ClimateLens**: NEX-GDDP-CMIP6 SSP245/585 projections + anomaly maps.
- **DroughtAI**: SPI (1/3/6/12-month) and NDVI/VCI vegetation stress.
- **InfraRisk**: population / infrastructure exposure overlays.
- **ResilienceOR**: operations-research layer — AHP (consistency-checked),
  TOPSIS, Maximal Covering Location (relief shelters), Dijkstra evacuation
  routing, 0/1 knapsack mitigation; with AOI bridges.
- **GeoCopilot**: grounded NL agent over the platform tools, **Llama** via Groq
  or Ollama (works without an LLM too); resolves all 32 states + 482 districts
  via a gazetteer built from the official India shapefile.
- **Frontend**: premium dark map workspace, module panels, charts, GeoCopilot
  chat, India boundary overlays + state AOI presets.
- **Backend platform**: TTL cache, per-IP token-bucket rate limiting, request-id
  logging, typed error envelope, CORS, OpenAPI docs.
- **Infra**: backend + frontend Dockerfiles, docker-compose, GitHub Actions CI,
  Makefile, Windows dev launcher.
- **Tests**: 22 geo-engine + 10 backend, green.
- **Docs**: architecture, module API contract, engineering deep-dive (algorithms,
  data structures, complexity), research notes, OSS landscape, roadmap.
