# Changelog

All notable changes to TerraShield AI are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/). Versioning: SemVer.

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
