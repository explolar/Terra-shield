# TerraShield AI — Module Specs & API Contract

All endpoints are prefixed with `/api/v1`. Compute endpoints accept an **AOI**
(GeoJSON polygon or bbox) and return some mix of: a Leaflet **tile URL**, summary
**stats**, a **legend**, and optionally **GeoJSON** vectors.

Shared request fragment:

```jsonc
"aoi": {                       // one of: geojson | bbox
  "type": "bbox",
  "bbox": [minLon, minLat, maxLon, maxLat]
}
```

Shared layer response fragment:

```jsonc
{
  "tile_url": "https://earthengine.googleapis.com/.../{z}/{x}/{y}",
  "legend": [{ "label": "Very high", "color": "#7f0000", "min": 0.8, "max": 1.0 }],
  "stats": { "mean": 0.42, "area_km2": 318.7, "high_risk_pct": 12.4 },
  "source": "live" | "demo"   // tells the UI whether GEE creds were active
}
```

---

## ⚙️ EarthData Engine — `/earthdata`

The shared backend. Most calls go through it indirectly, but it exposes utilities.

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/earthdata/status` | GEE init status: `live` / `demo`, project, dataset availability |
| POST | `/earthdata/aoi/validate` | Validate + normalize an AOI, return area & centroid |
| GET | `/earthdata/basemaps` | Available basemap tile layers |
| GET | `/earthdata/datasets` | Catalog of datasets the platform uses (id, license, resolution) |

---

## 🌊 FloodAI — `/flood` *(flagship)*

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/flood/susceptibility` | Multi-criteria flood-susceptibility index map |
| POST | `/flood/sar-extent` | Sentinel-1 SAR open-water / inundation extent |
| POST | `/flood/road-risk` | Road segments disrupted by flooding + access loss |

**Susceptibility** — weighted overlay (AHP-style) of conditioning factors:
elevation, slope, Topographic Wetness Index (TWI), drainage proximity, rainfall
intensity, land use, soil/permeability. Weights are user-tunable; defaults sum to 1.

```jsonc
// POST /flood/susceptibility
{
  "aoi": { "type": "bbox", "bbox": [73.9, 17.6, 74.3, 18.0] },
  "weights": { "elevation": 0.25, "slope": 0.2, "twi": 0.2,
               "drainage": 0.15, "rainfall": 0.1, "landuse": 0.1 },
  "rainfall_scenario": "extreme"   // normal | wet | extreme
}
// → { layer: <LayerResponse>, factor_layers: {elevation: tile_url, ...} }
```

**SAR extent** — pre/post Sentinel-1 VV change + threshold (Otsu) to delineate
inundation; returns extent tiles + a flooded-area estimate (km²).

**Road-risk** — overlays modelled flood depth with OSM road network and
settlements (WorldPop) to flag inaccessible segments and population cut off.

References: Sen1Floods11 (Bonafilia 2020); STURM-Flood (2025); AHP flood
susceptibility (Saaty); TWI (Beven & Kirkby 1979).

---

## 🌡️ ClimateLens — `/climate`

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/climate/projection` | Future climate for an AOI under an SSP, vs. baseline |
| POST | `/climate/anomaly` | Anomaly map (e.g. Δ precipitation, Δ Tmax) for a horizon |
| GET | `/climate/scenarios` | Available SSPs, variables, models, horizons |

Data: **NEX-GDDP-CMIP6** (NASA, 0.25°, daily, 1950–2100) via Earth Engine
`NASA/GDDP-CMIP6`. Variables: `pr` (precip), `tas`/`tasmax`/`tasmin`.
Scenarios: `ssp245`, `ssp585`. Horizons: `2030s`, `2050s`, `2080s` vs `1995–2014`.

```jsonc
// POST /climate/projection
{
  "aoi": { "type": "bbox", "bbox": [73.9, 17.6, 74.3, 18.0] },
  "scenario": "ssp585", "variable": "pr", "horizon": "2050s",
  "model": "ensemble"
}
// → { baseline, projected, delta, pct_change, timeseries: [...], layer }
```

---

## 🌵 DroughtAI — `/drought`

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/drought/spi` | Standardized Precipitation Index (1/3/6/12-month) |
| POST | `/drought/vegetation` | NDVI / VCI anomaly (vegetation stress) |

Data: **CHIRPS** (rainfall, SPI) and **MODIS MOD13 / Sentinel-2** (NDVI → VCI).
SPI follows McKee et al. (1993): fit gamma to the precip accumulation, transform
to standard normal; classify D0–D4.

---

## 🛣️ InfraRisk — `/infra`

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/infra/exposure` | Roads / buildings / population exposed to a hazard layer |
| POST | `/infra/access` | Emergency-access routing impact under flooding |

Data: **OSM** (roads, buildings), **WorldPop** (population). v1 computes exposure
overlays; routing-based access loss is on the roadmap.

---

## 🤖 GeoCopilot — `/copilot`

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/copilot/ask` | NL question → tool plan → executed analytics → summary |
| GET | `/copilot/tools` | The geospatial tools the agent can call |

The copilot is an **agent over the platform's own APIs**: it parses intent,
resolves the AOI/scenario, calls FloodAI/ClimateLens/DroughtAI tools, and returns
a grounded natural-language answer plus the layers to render. v1 ships a
deterministic intent router + tool-calling skeleton; RAG over climate reports and
LLM summarization deepen on the roadmap.

```jsonc
// POST /copilot/ask
{ "question": "How will flood risk in Satara change under SSP585 by 2050?" }
// → { answer, plan: [...tool calls...], layers: [...], citations: [...] }
```

---

## Added since v0.1 (v0.2)

| Module | Method | Path | Purpose |
|--------|--------|------|---------|
| FloodAI | POST | `/flood/multiyear` | Annual peak flood extent 2019–2024 + trend |
| FloodAI | POST | `/flood/ml-risk` | ML flood-risk (GBM/XGBoost/RF) + SHAP importance |
| ClimateLens | POST | `/climate/extremes` | ETCCDI indices (Rx1day, R95p, CDD, hot-days) |
| InfraRisk | POST | `/infra/criticality` | Road-network edge-betweenness criticality |
| WeatherCast | POST | `/weather/forecast` | Open-Meteo 1–16 day forecast + flood watch |
| GroundwaterAI | POST | `/groundwater/storage` | GRACE storage anomaly + depletion trend |

- **FloodAI/susceptibility** now uses the **11-factor AHP** model (`flood_factors.py`)
  and returns `factor_urls` (per-factor tiles) + `ahp` (CR/λmax) on the live path.
- **FloodAI/sar-extent** now uses the 6-layer calibrated mask and returns
  `severity_url` + exposure stats (population, cropland + crop-loss USD, built-up).
- Coarse modules (ClimateLens, GroundwaterAI) accept AOIs up to **1,000,000 km²**
  (state/basin scale); fine modules keep the 50,000 km² cap.
- **GeoCopilot** input is cleaned + injection-filtered; LLM output is bounded
  (`backend/app/core/sanitize.py`).

## Data sources & licenses

| Dataset | Use | Resolution | License |
|---------|-----|-----------|---------|
| SRTM / MERIT Hydro | DEM, slope, TWI, drainage | 30 m | Public domain / open |
| Sentinel-1 GRD | SAR flood extent | 10 m | Copernicus open |
| Sentinel-2 SR | NDVI / land cover | 10 m | Copernicus open |
| CHIRPS | rainfall, SPI | ~5 km | Open (UCSB/USGS) |
| NEX-GDDP-CMIP6 | climate projections | 0.25° | CC-BY-SA 4.0 |
| ESA WorldCover | land use | 10 m | CC-BY 4.0 |
| WorldPop | population | 100 m | CC-BY 4.0 |
| OpenStreetMap | roads, buildings | vector | ODbL |
| NASA GRACE/GRACE-FO | groundwater / water storage anomaly | ~3° mascon | Open (NASA) |
| MODIS MOD13/MOD16 | NDVI/VCI, evapotranspiration | 500 m–1 km | Open (NASA) |
| JRC Global Surface Water | permanent water, flood frequency | 30 m | Open (EC JRC) |
| Open-Meteo | weather / rainfall forecast | ~11 km | CC-BY 4.0 (free, no key) |
