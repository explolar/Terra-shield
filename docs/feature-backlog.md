# TerraShield AI — Implementation-Ready Feature Backlog

Prioritized, concrete features to add, grouped by module. Every item names its
method/source, the exact file/function it plugs into, the dataset (with GEE asset
id where relevant), effort (S/M/L), impact (High/Med/Low), and whether it is
implementable now (`yes` = pure-Python/NumPy or existing GEE creds; `partial` =
demo-path now, live needs GEE/data wiring; `heavy-deps` = needs GPU / large model
/ PyTorch).

Codebase map (for the "plugs in" column):
- Geo-engine: `geo-engine/terrashield_geo/{flood,climate,drought,infra,optimize,indices,demo,tiles,datasets}.py`
- Routes: `backend/app/api/routes/{flood,climate,drought,infra,optimize,copilot,earthdata}.py`
- Copilot service: `backend/app/services/copilot.py`

---

## ⭐ Top 10 — do these next (best impact/effort, no heavy deps)

| # | Feature | Module | File / where | Effort | Impact | Now? |
|---|---------|--------|--------------|--------|--------|------|
| 1 | ✅ **Otsu thresholding on Sentinel-1** (replace fixed −3 dB / −15 dB) | FloodAI | `flood.py::_sar_extent_live` (new `_otsu_threshold` helper) | S | High | ✅ shipped |
| 2 | ✅ **HAND as a flood conditioning factor** (and SAR false-positive mask) | FloodAI | `flood_factors.py` factor stack; reuse in `_sar_extent_live` | S | High | ✅ shipped |
| 3 | **Flood frequency from JRC GSW history** (recurrence/seasonality factor) | FloodAI | `flood.py::_susceptibility_live` (new factor); `datasets.py` already lists GSW | S | High | yes |
| 4 | ✅ **Proper SPI gamma fit** via `climate_indices` (replace z-score proxy) | DroughtAI | `drought.py::_spi_live`/`_spi_demo` (new `_spi_gamma`) | S | High | ✅ shipped |
| 5 | ✅ **ETCCDI extreme indices** (R95p, CDD, RX1day, heatwave days) | ClimateLens | new `climate.py::extremes()` + `/climate/extremes` route | M | High | ✅ shipped |
| 6 | **p-median / set-cover exact ILP** via PuLP (behind MCLP signature) | ResilienceOR | `optimize.py` new `locate_shelters_ilp`, `set_cover` | M | High | yes (PuLP+CBC) |
| 7 | ✅ **Road-network betweenness criticality** (NetworkX) | InfraRisk | new `infra.py::road_criticality()` + `/infra/criticality` route | M | High | ✅ shipped |
| 8 | **Expected Annual Damage** w/ depth-damage curves (Huizinga 2017) | InfraRisk | new `infra.py::expected_annual_damage()`; feeds knapsack `risk_reduction` | M | High | yes (demo), partial (live) |
| 9 | **SPEI** (P − PET, log-logistic) via `climate_indices` | DroughtAI | `drought.py` new `spei()` + `/drought/spei` route | M | High | yes |
| 10 | **GeoCopilot RAG over method cards / docs** (LlamaIndex + local embeddings) | GeoCopilot | `services/copilot.py` new `retrieve()`; cite in `CITATIONS` | M | High | partial (small embed model) |

> **Status (2026-05-24): items 1, 2, 4, 5, 7 are shipped** (✅ above) — Otsu SAR
> thresholding, the HAND conditioning factor, gamma-fit SPI, ETCCDI extremes, and
> road-network betweenness criticality are all in the codebase. SHAP (X4) also
> shipped in the ML flood path. Remaining open: 3, 6, 8, 9, 10.

Rationale: 1–4 and 9 sharpen the *scientific correctness* of existing live paths
with tiny diffs; 5–8 add genuinely new decision value with permissive-license
libs already in `oss-landscape.md`; 10 closes the biggest GeoCopilot gap without a
GPU. None require PyTorch or model weights.

---

## 🌊 FloodAI

### F1 — Otsu thresholding on Sentinel-1  · S · High · ✅ SHIPPED
Histogram bi-level threshold (Otsu 1979) on VV (or VV+VH) backscatter instead of
the hard-coded `diff.lt(-3).And(post.lt(-15))`. Compute the per-AOI histogram via
`ee.Reducer.histogram`, find the between-class-variance-maximizing cut in Python,
threshold in GEE. Add a permanent-water mask (JRC GSW occurrence > 50) so only
*new* water is reported.
- **Source:** Otsu (1979) *IEEE SMC*; UN-SPIDER GEE Recommended Practice; FLOMPY (kleok), Mahyarona/Flood-Detection-Algorithm-using-GEE.
- **Plugs in:** `flood.py::_sar_extent_live` → new `_otsu_threshold(image, geom)`.
- **Data:** `COPERNICUS/S1_GRD`, mask `JRC/GSW1_4/GlobalSurfaceWater`.
- Demo path keeps the threshold-a-field mock; only the live path changes.

### F2 — HAND (Height Above Nearest Drainage) factor & mask  · S · High · ✅ SHIPPED
Add HAND as a 7th conditioning factor (low HAND = floodplain = high risk) and use
it to suppress SAR false positives (terrain shadow / dry dark surfaces). Use the
ready-made GEE HAND asset rather than recomputing drainage.
- **Source:** Nobre et al. (2011) HAND; DeepSAR Flood Mapper (2025, *GIScience & Remote Sensing*) uses S-1 + HAND; cybergis nfie-floodmap/CFIM.
- **Plugs in:** `flood.py::_susceptibility_live` `factors` dict (`"hand": _scale(hand, invert=True)`); add to `DEFAULT_WEIGHTS` + `DEFAULT_FLOOD_AHP`; reuse mask in `_sar_extent_live`.
- **Data:** `users/gena/global-hand/hand-100` or `MERIT/Hydro` `hnd` band; 90 m.

### F3 — Flood frequency / recurrence from JRC GSW history  · S · High · yes
Use JRC Global Surface Water `recurrence` and `seasonality` bands as a conditioning
factor — pixels that have flooded before are more susceptible. Also returnable as a
standalone "historical flood frequency" layer.
- **Source:** Pekel et al. (2016) *Nature* (JRC GSW).
- **Plugs in:** `flood.py::_susceptibility_live` new factor; optional `flood.py::flood_history()` + `/flood/history` route.
- **Data:** `JRC/GSW1_4/GlobalSurfaceWater` (`recurrence`, `seasonality`); already in `datasets.py`.

### F4 — Flood depth estimation (HAND-based)  · M · Med · yes
Estimate inundation depth = water-surface elevation − DEM within the flooded
extent, using the floodwater-to-HAND method (fill the SAR/extent mask to the
nearest-drainage water level). Feeds InfraRisk depth-damage (I3).
- **Source:** HAND flood-stage method (Nobre 2016; FwDET, Cohen et al. 2018).
- **Plugs in:** `flood.py::sar_extent` → add `depth` output; new `_flood_depth(extent, dem, hand)`.
- **Data:** `USGS/SRTMGL1_003` + HAND; demo path returns a depth field from `smooth_field`.

### F5 — U-Net / Prithvi water segmentation  · L · High · heavy-deps
Learned SAR/optical water masks (water-class IoU ≈ 82.6 on Sen1Floods11 with
Prithvi-EO-2.0-TL). Train via TerraTorch (UPerNet head, Dice/Focal loss for class
imbalance, 448×448 chips). Serve as an alternate `sar_extent` backend.
- **Source:** Szwarcman et al. (2025) Prithvi-EO-2.0 (corpus: `RSE Prithvi Global.txt`, `2412.02732v3.txt`); Bonafilia et al. (2020) Sen1Floods11; Ronneberger et al. (2015) U-Net.
- **Plugs in:** new `flood.py::sar_extent_ml` (offline batch inference → tiles); not in the FastAPI hot path.
- **Caveat:** needs GPU + PyTorch + TorchGeo/TerraTorch + model weights. Mark as R&D track, not v1.

### F6 — SAR feature stack: texture + coherence  · M · Med · partial
Stack VV/VH backscatter + GLCM texture + interferometric coherence (coherence
drops sharply over newly inundated surfaces) instead of intensity alone — improved
separability and speckle robustness.
- **Source:** Dai et al. (2026) *Agronomy* 16:750 (corpus `agronomy-16-00750-v2.txt`) — SAR texture/coherence > backscatter alone, transfers to flood.
- **Plugs in:** `flood.py::_sar_extent_live` (GLCM via `ee.Image.glcmTexture`); coherence needs S-1 SLC (not in GRD asset → external/partial).

---

## 🌡️ ClimateLens

### C1 — ETCCDI extreme indices  · M · High · ✅ SHIPPED
R95p (annual precip on > 95th wet-day pct), CDD (consecutive dry days), RX1day
(max 1-day precip), heatwave days / WSDI (≥ N consecutive days > 90th pct), TXx.
Compute on the NEX-GDDP daily series; report baseline vs horizon deltas.
- **Source:** Zhang et al. (2011) ETCCDI 27-index set; implementable via `xclim` (Apache-2.0) offline or hand-rolled reducers on GEE.
- **Plugs in:** new `climate.py::extremes(aoi, scenario, horizon, index)` + `/climate/extremes` route + `scenarios()` index list.
- **Data:** `NASA/GDDP-CMIP6` daily `pr`/`tasmax`; demo path synthesizes indices from the existing signal.

### C2 — Quantile Delta Mapping bias correction  · M · Med · yes
QDM preserves the model's projected relative change in quantiles (naive quantile
mapping corrupts trends). Apply to precip before extremes/return periods.
- **Source:** Cannon, Sobie & Murdock (2015) *J. Climate* 28(17); `xclim.sdba` / scikit-downscale.
- **Plugs in:** new `climate.py::bias_correct(obs, model_hist, model_fut)` helper used by C1/C3.
- **Data:** CHIRPS as obs reference + NEX-GDDP model series; offline-capable.

### C3 — Multi-model ensemble spread & agreement  · S · Med · yes
Beyond the `ensemble` mean: report inter-model std-dev and a sign-agreement
fraction ("% of models agreeing on the sign of change") — the standard IPCC
robustness signal. Loop the 3 named models already in `scenarios()`.
- **Source:** IPCC AR6 robustness convention; Tebaldi et al. (2011).
- **Plugs in:** `climate.py::projection` add `ensemble_spread`, `agreement_pct` to the response; loop `coll.filter(model)`.
- **Data:** `NASA/GDDP-CMIP6` per-model; demo path fabricates plausible spread.

### C4 — Return-period analysis (GEV)  · M · Med · yes
Fit a Generalized Extreme Value distribution to annual maxima (RX1day) → return
levels for 10/50/100-yr events, baseline vs future. The decision-grade "design
storm" output.
- **Source:** Coles (2001) *Intro to Statistical Modeling of Extreme Values*; `scipy.stats.genextreme`.
- **Plugs in:** new `climate.py::return_period(aoi, index, periods)` + `/climate/return-period` route.
- **Data:** NEX-GDDP `pr` annual maxima; pure SciPy, offline-capable.

### C5 — Add SSP1-2.6 + more models  · S · Low · yes
Broaden `SCENARIOS` to include `ssp126` and expand the model list; trivial config
change that widens scenario coverage.
- **Plugs in:** `climate.py` `SCENARIOS`, `_SIGNAL`, `scenarios()`.
- **Data:** `NASA/GDDP-CMIP6` (has SSP1-2.6).

---

## 🌵 DroughtAI

### D1 — Proper SPI gamma fit  · S · High · ✅ SHIPPED
Replace the historical z-score proxy with a true two-parameter gamma fit per
accumulation window → CDF → standard-normal transform (handles zero-precip via the
mixed distribution). Use the NOAA-grade `climate_indices` library.
- **Source:** McKee et al. (1993) SPI; `climate_indices` (monocongo, BSD-3).
- **Plugs in:** `drought.py::_spi_live` and `_spi_demo` → new `_spi_gamma(series, scale)`.
- **Data:** `UCSB-CHG/CHIRPS/PENTAD` accumulations; gamma fit runs in NumPy/SciPy.
- **Status:** shipped via `_spi_gamma` (SciPy `stats.gamma.fit` + zero-precip mix).
  The *regional* index value uses the gamma fit; the *per-pixel* SPI tile is still
  rendered as a z-score image — turning that tile into a per-pixel gamma map is the
  remaining work.

### D2 — SPEI (climatic water balance)  · M · High · yes
P − PET fit to a log-logistic distribution; captures temperature-driven drying
that SPI misses. PET via Hargreaves (needs tasmax/tasmin only) or Thornthwaite.
- **Source:** Vicente-Serrano et al. (2010) *J. Climate* 23(7); `climate_indices` SPEI + PET.
- **Plugs in:** new `drought.py::spei(aoi, scale)` + `/drought/spei` route; `SPI_CLASSES` reused for classification.
- **Data:** CHIRPS (P) + NEX-GDDP or ERA5 (T for PET).

### D3 — Combined Drought Index (meteorological + vegetation)  · M · Med · yes
Weighted blend of SPI/SPEI (precip) + VCI (vegetation) + optional TCI (thermal) →
a single composite drought severity, with AHP-derived weights (reuse `ahp_weights`).
- **Source:** Kogan VHI = 0.5·VCI + 0.5·TCI; US Drought Monitor blend (Svoboda 2002).
- **Plugs in:** new `drought.py::combined_index(aoi)` calling `spi`+`vegetation`+`optimize.ahp_weights`.
- **Data:** CHIRPS + MODIS `MOD13A2` + MODIS LST `MOD11A2` (TCI); demo-capable.

### D4 — Drought onset / duration / severity run-analysis  · S · Med · yes
Run-theory on the SPI/SPEI time series: detect onset (cross below −1), end
(return above 0), duration (months), and accumulated severity (Σ index). Turns a
single map into an event narrative.
- **Source:** Yevjevich (1967) theory of runs; standard SPI event definition.
- **Plugs in:** `drought.py::spi` add a `timeseries` + `events` block (mirrors climate's timeseries pattern).
- **Data:** CHIRPS monthly series; pure NumPy, offline-capable.

### D5 — TCI (Temperature Condition Index)  · S · Low · partial
`TCI = (LST_max − LST)/(LST_max − LST_min)`; pairs with VCI for VHI. Mirrors the
existing `indices.py::vci` helper.
- **Source:** Kogan (1995).
- **Plugs in:** new `indices.py::tci`; `drought.py::vegetation` add VHI.
- **Data:** `MODIS/061/MOD11A2` LST.

---

## 🛣️ InfraRisk

### I1 — Road-network betweenness criticality  · M · High · ✅ SHIPPED
Build the OSM (or demo lattice) road graph and rank segments by edge-betweenness
centrality + largest-connected-component loss when a flooded link is removed →
flags segments whose failure most degrades emergency access.
- **Source:** road criticality via betweenness (Gauthier et al. 2018; *Chaos* 2024, per research-notes); NetworkX.
- **Plugs in:** new `infra.py::road_criticality(aoi)` + `/infra/criticality` route; reuses `optimize.RoadGraph` topology.
- **Data:** OSM roads (live) or the demo lattice from `optimize.evacuation_for_aoi`; NetworkX, offline-capable.

### I2 — Building-level flood depth (HAND)  · M · Med · partial
Sample F4's HAND-based depth raster at building footprints (OSM/WorldCover
built-up) → per-building inundation depth, the input to depth-damage curves.
- **Source:** HAND flood-stage; FwDET (Cohen et al. 2018).
- **Plugs in:** `infra.py::exposure` add a `depth_by_building` summary; depends on F4.
- **Data:** OSM buildings + HAND + DEM; demo path uses `smooth_field` depths.

### I3 — Expected Annual Damage (depth-damage curves)  · M · High · yes(demo)/partial(live)
Apply fractional depth-damage functions per land-use class to flood depth ×
exposure value, integrate over a set of return-period scenarios → EAD (€/yr). This
is the monetary risk number that makes the knapsack `risk_reduction` real.
- **Source:** Huizinga, De Moel & Szewczyk (2017) *Global flood depth-damage functions*, EUR 28552 EN (JRC); HydroMT-FIAT, physrisk implementations.
- **Plugs in:** new `infra.py::expected_annual_damage(aoi, depth_scenarios)`; output wired into `optimize.Intervention.risk_reduction`.
- **Data:** JRC curves (bundle the CSV — small, public); depth from F4, exposure from `exposure`. Demo-capable end-to-end.

### I4 — Risk = Hazard × Exposure × Vulnerability framing  · S · Med · yes
Make the InfraRisk output explicitly a H×E×V triad (Sendai/GAR-aligned), with the
three factors surfaced separately so users can audit the composite.
- **Source:** UNDRR GAR; Sendai Framework.
- **Plugs in:** `infra.py::exposure` restructure `stats` into `{hazard, exposure, vulnerability, risk}`.
- **Data:** existing layers; offline-capable.

---

## 🧮 ResilienceOR

### R1 — p-median exact ILP (PuLP)  · M · High · yes
Minimize total weighted demand-to-facility distance (vs MCLP's coverage). Exact
optimum on small instances via PuLP+CBC, behind the existing solver signature.
- **Source:** Hakimi (1964) p-median; PuLP/CBC (coin-or).
- **Plugs in:** new `optimize.py::p_median(demand, sites, p)`; option flag in `shelters_for_aoi`.
- **Data:** AOI-derived demand/sites (already built in `shelters_for_aoi`).

### R2 — Set-cover (minimum facilities for full coverage)  · S · High · yes
LSCP: minimize the number of shelters so *every* demand point is covered within
radius (vs MCLP's "best p"). Exact ILP (PuLP) or greedy `ln n`-approx.
- **Source:** Toregas et al. (1971) Location Set Covering Problem.
- **Plugs in:** new `optimize.py::set_cover(demand, sites, radius_km)`.
- **Data:** as R1; pure-Python greedy works without PuLP.

### R3 — Multi-objective shelter siting  · M · Med · yes
Trade off coverage vs cost vs equity (max-min coverage across sub-regions) — a
small Pareto front via weighted-sum or ε-constraint over R1/R2.
- **Source:** disaster-relief multi-objective location-allocation (research-notes ResilienceOR refs).
- **Plugs in:** new `optimize.py::shelter_pareto(...)`; returns a frontier the UI can plot.
- **Data:** as R1; offline-capable.

### R4 — Capacitated routing / VRP  · L · Med · yes
Relief-vehicle routing with capacity + flood-blocked edges (extends Dijkstra to
multi-vehicle, multi-stop). Use OR-Tools routing.
- **Source:** Dantzig & Ramser (1959) VRP; Google OR-Tools.
- **Plugs in:** new `optimize.py::relief_vrp(graph, depot, demands, capacity)`.
- **Data:** `RoadGraph` + demand; OR-Tools (Apache-2.0).

### R5 — Sensor / gauge placement  · M · Med · yes
Place k flood/rain sensors to maximize information / coverage of high-risk cells —
submodular greedy (same machinery as MCLP) over the susceptibility surface.
- **Source:** Krause et al. (2008) near-optimal sensor placement (submodularity).
- **Plugs in:** new `optimize.py::place_sensors(risk_field, k)`; reuse the greedy in `locate_shelters`.
- **Data:** `flood.susceptibility` field; offline-capable.

---

## 🤖 GeoCopilot

### G1 — RAG over method cards / climate reports  · M · High · partial
Index the `docs/*.md` method briefs + per-module method cards in a local vector
store; retrieve top-k passages to ground answers and populate real `citations`
(currently a static dict). Use a small local embedding model (no GPU) + LlamaIndex.
- **Source:** Lewis et al. (2020) RAG; LlamaIndex; pgvector/Qdrant.
- **Plugs in:** `services/copilot.py` new `retrieve(question)`; feed into the LLM `user` prompt; replace static `CITATIONS`.
- **Data:** the four `docs/*.md` files + dataset catalog; CPU-capable with a MiniLM-class embedder.

### G2 — LLM-driven tool selection (replace keyword router)  · M · High · partial
Swap `_choose_tool`'s `if has(...)` keyword cascade for an LLM that picks tool +
arguments from the `TOOLS` manifest (function-calling / ReAct), with the current
keyword router as the deterministic fallback.
- **Source:** Yao et al. (2023) ReAct; Li & Ning (2023) Autonomous GIS / LLM-Geo.
- **Plugs in:** `services/copilot.py::_choose_tool` + `_parse_entities` → `llm.select_tool(question, tools_manifest())`.
- **Data:** existing Llama config (`services/llm.py`); falls back deterministically if disabled.

### G3 — Multi-step plans (tool chaining)  · M · High · partial
Let the agent chain tools — e.g. susceptibility → exposure → shelter siting — as a
real plan, not a single tool call. The `plan` field already exists; make it
executable over several steps with intermediate results passed forward.
- **Source:** ReAct (Yao 2023); GeoBenchX (2025) multi-step eval; LLM-Geo.
- **Plugs in:** `services/copilot.py::ask` loop over a plan list instead of one `tool["fn"]`.
- **Data:** existing tools; deterministic multi-step recipes can ship before LLM planning.

### G4 — Map-action grounding  · S · Med · yes
Have the copilot emit structured map actions (`{action: fit_bounds|add_layer|
set_opacity, ...}`) alongside prose so the answer drives the Leaflet map, not just
text. Layers are already returned; add an `actions` array.
- **Source:** GIS Copilot (Akinboyewa et al. 2025) tool-grounding pattern.
- **Plugs in:** `services/copilot.py::ask` add `actions` to the response.
- **Data:** none; pure response-shaping, offline-capable.

---

## 🧭 Cross-cutting (apply across modules)

### X1 — Spatial block cross-validation utility  · M · High · yes
KMeans on coordinates → GroupKFold so any future model reports honest (spatially
blocked) skill, not autocorrelation-inflated random-CV. Corpus shows R² collapse
0.96 (random) → 0.02–0.27 (spatial).
- **Source:** Meyer et al. (2019); Roberts et al. (2017); Kumar et al. (2025, corpus `1-s2.0-S266701002500294X-main.txt`); OpenLandMap 100×100 km blocks + LOYO (corpus `openlandmap2026_soildb.txt`).
- **Plugs in:** new `geo-engine/terrashield_geo/validation.py::spatial_block_cv(X, y, coords)`.
- **Data:** any tabular sample set; pure scikit-learn.

### X2 — Area of Applicability (DI) for all modules  · M · High · partial
Generalize FloodAI's demo AoA into a real Dissimilarity Index: min weighted
distance in predictor space to training data, thresholded at the 0.95 quantile →
masks extrapolation on every map. FloodAI already returns `reliability.applicable_pct`.
- **Source:** Meyer & Pebesma (2021); Kumar et al. (2025, corpus).
- **Plugs in:** new `validation.py::area_of_applicability(train_X, pred_X, weights)`; call from each module's reliability block.
- **Data:** factor stacks; NumPy/sklearn. Live raster DI needs per-pixel feature export (partial).

### X3 — QRF uncertainty + PICP  · M · High · yes
Quantile Regression Forests for per-pixel prediction intervals; validate coverage
with PICP (fraction of obs inside the stated interval). Calibrated intervals, not
just point estimates.
- **Source:** Meinshausen (2006) QRF; Poggio et al. (2021) SoilGrids 2.0 (corpus `soilgrids2021_poggio.txt`); PICP per Kumar et al. (2025).
- **Plugs in:** `validation.py::qrf_intervals` + `picp`; surfaced in any model-backed module's `reliability`.
- **Data:** `sklearn`/`quantile-forest`; offline-capable.

### X4 — SHAP explainability  · M · Med · ✅ SHIPPED (ML flood path)
Per-feature / per-pixel attribution of risk scores so every number is auditable
("elevation drove this cell's high risk"). Offline batch over a model; not in the
request hot path.
- **Source:** Lundberg & Lee (2017); Beucher et al. (2021) SHAP for CNN soil maps (corpus `frontiers2021_cnn_acid_soil.txt`).
- **Plugs in:** `validation.py::shap_attributions`; copilot can verbalize top drivers.
- **Data:** `shap` lib; CPU for tree models.

### X5 — COG / map tiling for demo & batch outputs  · M · Med · yes
Write computed rasters as Cloud-Optimized GeoTIFFs + serve XYZ tiles (titiler /
rio-tiler) so non-GEE / batch outputs (e.g. F5 ML masks, F4 depth) tile like the
live GEE path does today.
- **Source:** COG spec; titiler (Apache-2.0), rio-tiler.
- **Plugs in:** new `tiles.py::cog_tile_url(path)` mirroring `image_tile_url`.
- **Data:** any local raster; rasterio/rioxarray.

### X6 — Report / PDF export  · M · Med · yes
One-click AOI risk brief: stitch the module stats + legends + a static map into a
PDF (WeasyPrint/ReportLab). High demo value for stakeholders.
- **Plugs in:** new `/report` route + `services/report.py` aggregating module calls.
- **Data:** existing endpoint responses; offline-capable.

### X7 — Time-series animation  · S · Med · partial
Animate a layer across time (SPI months, climate horizons, flood pre/post) — emit
an ordered list of tile-URLs / grids the UI plays as frames. Climate `timeseries`
and SPI scales already exist as the data spine.
- **Plugs in:** `climate.py`/`drought.py` add a `frames: [...]` output; `/…/animate` variants.
- **Data:** existing collections; live frames need multiple GEE renders (partial).

---

## Feasibility notes (honest)
- **Heavy-deps (GPU / large models):** F5 (Prithvi/U-Net), and the *full* learned
  variants of X2/X3/X4 when applied to deep nets. Everything else is NumPy/SciPy/
  scikit-learn/NetworkX/PuLP/OR-Tools — CPU, permissive licenses.
- **Live-only:** F1, F3, parts of F2/F4/I2 need active GEE creds; all have a demo
  path or a demo-capable equivalent so the dashboard never breaks offline.
- **Corpus reality:** the paper library is soil-DSM-centric. Its genuinely
  reusable contributions are the **reliability/uncertainty stack** (X1–X4) and
  **SAR feature engineering** (F6) — flood/CMIP6/SPI specifics come from the
  external peer-reviewed sources cited above, consistent with `research-notes.md`.
