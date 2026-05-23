# TerraShield AI — Roadmap

Guiding principle: **one killer vertical end-to-end before breadth.** A platform
that does FloodAI brilliantly beats six shallow demos. The module stubs exist so
the architecture is real from day one — but depth lands one module at a time.

## Phase 0 — Foundation ✅ (this scaffold)
- Monorepo: `backend` · `geo-engine` · `frontend` · `infra` · `docs`
- FastAPI app factory, 6 module routers, typed schemas, services layer
- geo-engine with GEE gateway + **demo fallback** (whole stack runs offline)
- Next.js map workspace + module panels + typed API client
- Docker, docker-compose, GitHub Actions CI, architecture diagrams

## Phase 1 — FloodAI depth (flagship)
- [ ] Real weighted-overlay susceptibility on live GEE (DEM/slope/TWI/drainage/LULC)
- [ ] Sentinel-1 SAR pre/post change + Otsu threshold inundation extent
- [ ] Road-access disruption (OSM × flood depth × WorldPop)
- [ ] U-Net SAR segmentation experiment on Sen1Floods11 (notebook → served model)
- [ ] Validation: confusion vs. Copernicus EMS / historical flood footprints

## Phase 2 — ClimateLens depth
- [ ] NEX-GDDP-CMIP6 district projections (SSP245/585, 2030s/50s/80s)
- [ ] Anomaly maps + extreme indices (R95p, heatwave days, dry-spell length)
- [ ] District comparison dashboard + downloadable report
- [ ] (Optional) ingest your WRF MTP downscaled outputs as a premium layer

## Phase 3 — DroughtAI + InfraRisk
- [ ] SPI (1/3/6/12-mo) from CHIRPS, D0–D4 classification, time series
- [ ] NDVI/VCI vegetation-stress anomaly
- [ ] InfraRisk exposure overlays; emergency-access routing impact

## Phase 4 — GeoCopilot (GenAI layer)
- [ ] Intent router → tool-calling agent over platform APIs
- [ ] RAG over climate reports / datasets (LlamaIndex or LangChain)
- [ ] Grounded NL answers + auto-rendered layers + citations

## Phase 5 — Deployment & engineering polish
- [ ] Dockerized services on Cloud Run, ADC for Earth Engine
- [ ] CI/CD: lint + test + build + deploy on push
- [ ] Caching (Redis), structured logging, rate limiting, error envelopes
- [ ] Load/perf pass; cold-start mitigation

## Phase 6 — Visualization & storytelling
- [ ] Architecture + workflow diagrams (done in `docs/`, refine)
- [ ] Demo video + narrated case study (a real flood event)
- [ ] Landing page polish; public live URL

## Tooling decisions (from the OSS scan — see [`oss-landscape.md`](oss-landscape.md))

Don't re-implement solved science. Adopt, behind our own module interfaces:

- **ClimateLens →** `xclim` + `xarray` + `intake-esm` (Apache-2.0): ETCCDI extreme
  indices, **quantile-delta-mapping** bias correction (Cannon et al., 2015 —
  trend-preserving, not naive QM), and CMIP6 ingestion. Closes the biggest
  "implement-from-spec" gap.
- **DroughtAI →** `climate_indices` (BSD, NOAA-used): reference SPI/SPEI with the
  proper gamma fit, replacing the current z-score approximation.
- **FloodAI / EarthData →** `TerraTorch` + `TorchGeo` for fine-tuning **Prithvi-EO-2.0**
  on Sen1Floods11; `STURM-Flood` U-Net baselines (~0.92 F1 on Sentinel-2).

## Publication targets (parallel track)
1. **FloodAI** — multi-criteria + SAR susceptibility for an Indian basin (applied RS journal / conference).
2. **ClimateLens × WRF** — downscaled extreme-precip projections (your MTP → paper).
3. **GeoCopilot** — agentic GenAI for geospatial risk querying (workshop paper).
