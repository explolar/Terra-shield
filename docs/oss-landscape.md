# TerraShield AI — Open-Source Landscape

A practical scan of open-source projects TerraShield could **adopt, integrate, or
learn from**, grouped by module. Format: **name** — what it does — why it's
relevant to TerraShield — license. Licenses are noted where verified from the
project; treat unverified ones as "confirm before adopting."

> Build-vs-buy guidance is inline. Default stance: reuse permissively-licensed
> (Apache-2.0 / MIT / BSD) libraries for plumbing; reserve custom code for the
> risk-scoring/OR logic that is TerraShield's differentiator.

---

## FloodAI — flood mapping (SAR / optical / susceptibility)

- **Sen1Floods11** (cloudtostreet) — Benchmark dataset + reference FCNN training
  code for Sentinel-1 flood segmentation (446 hand-labeled chips, 11 events). —
  Primary training/eval data and baseline for FloodAI's water-segmentation model.
  — License: data/code on GitHub (verify; commonly cited as research-permissive).
- **FLOMPY** (kleok/FLOMPY) — Automatic floodwater mapping from Sentinel-1
  intensity time series using Otsu thresholding + statistical change. — Drop-in
  unsupervised SAR flood baseline / fallback when no labels exist. — License:
  open source (GPL-style; confirm).
- **Global Flood Mapper** (PratyushTripathy) — GEE app for rapid Sentinel-1 SAR
  flood mapping via z-score anomaly vs pre-flood baseline. — Pattern + GEE code
  for fast operational flood extents in EarthData Engine. — License: open (GEE).
- **UNOSAT AI-Based Rapid Mapping** (UNITAR-UNOSAT) — Pretrained FCNN models for
  rapid flood segmentation in Sentinel-1 SAR (humanitarian-grade). — Battle-tested
  models + dataset for an operational FloodAI rapid-mapping mode. — License: check
  repo (UN/UNITAR terms).
- **STURM-Flood** (STURM-WEO) — Curated S-1/S-2 flood dataset (60 events) with
  U-Net benchmarks + code on Zenodo/GitHub. — Larger, recent training set to
  augment Sen1Floods11; ready-made U-Net baselines. — License: open (Zenodo;
  confirm CC variant).
- **nfie-floodmap / CFIM** (cybergis) — HAND-based continental inundation mapping
  framework. — Reuse HAND terrain conditioning to suppress SAR false positives
  and for hydrologic flood extent. — License: open source (confirm).
- **geemap** (gee-community) — Python/Jupyter interface to Google Earth Engine
  with interactive maps. — The glue for prototyping FloodAI/EarthData GEE
  workflows (incl. Otsu segmentation recipes). — License: MIT.

## ClimateLens — CMIP6 / climate tooling

- **xarray** (pydata) — Labeled N-D arrays for NetCDF/Zarr; the lingua franca of
  climate data. — Core data model for all ClimateLens gridded climate handling. —
  License: Apache-2.0.
- **xclim** (Ouranosinc) — 150+ climate indicators (incl. **ETCCDI** extremes:
  R95p, TXx, WSDI/heatwave days), plus bias-adjustment (quantile mapping/QDM) and
  ensemble tools, all on xarray+dask. — Implement ClimateLens extreme indices and
  bias correction here rather than rolling your own. — License: Apache-2.0.
- **intake-esm** (intake) — Catalog + loader for CMIP5/6 (and NEX-GDDP) into
  xarray datasets. — Discover and ingest CMIP6/SSP archives (incl. cloud Zarr) for
  ClimateLens. — License: Apache-2.0.
- **cf-xarray / cftime / netCDF4** (xarray ecosystem) — CF-convention awareness,
  non-standard calendars, NetCDF I/O. — Needed plumbing for correct CMIP6 time
  axes and metadata. — License: Apache-2.0 / MIT / BSD-style.
- **xESMF** (pangeo) — Fast, conservative regridding (ESMF) for xarray. —
  Regrid GCM/RCM grids to TerraShield's analysis grid before bias correction. —
  License: MIT/BSD (confirm).
- **xclim.sdba / scikit-downscale** — Statistical downscaling & bias adjustment
  (quantile mapping, BCSD-style, analog methods). — Statistical-downscaling track
  for ClimateLens when NEX-GDDP resolution is insufficient. — License: Apache-2.0
  (xclim) / Apache-2.0 (scikit-downscale; confirm).

## DroughtAI — drought indices

- **climate_indices** (monocongo) — Reference Python implementations of **SPI,
  SPEI, PET (Thornthwaite/Hargreaves), PNP, PDSI**; used by NOAA/drought.gov. —
  Adopt directly for DroughtAI's gamma-fit SPI and log-logistic SPEI; avoids
  reimplementing statistically tricky distribution fits. — License: BSD-3-Clause.
- **SPEI** (martinvonk/SPEI, JOSS-published) — Pandas-friendly SPI/SPEI/SGI with
  visualization. — Lightweight alternative/cross-check for station-level drought
  indices. — License: MIT (confirm).
- **xclim (drought/standardized indices)** — Has standardized precipitation
  indices on xarray grids. — Compute SPI/SPEI gridded at scale within the same
  stack as ClimateLens extremes. — License: Apache-2.0.

## Geospatial ML / deep learning

- **TorchGeo** (microsoft) — PyTorch domain library: geospatial datasets,
  samplers, transforms, and 40+ pretrained backbones (ResNet/ViT/Swin/**Prithvi**
  /ScaleMAE). — The backbone of TerraShield's EO model training/inference (flood,
  drought, land cover). — License: MIT.
- **Raster Vision** (azavea / Element 84) — Low-code framework for chip
  classification, semantic segmentation, object detection on satellite/aerial
  imagery. — Fast path to production segmentation pipelines without deep DL
  expertise. — License: Apache-2.0.
- **TerraTorch** (IBM) — Fine-tuning toolkit for geospatial foundation models
  (Prithvi, TerraMind, Clay) on PyTorch Lightning + TorchGeo. — Standardized way
  to fine-tune/serve Prithvi as named tasks — pairs with GeoCopilot's tool
  registry. — License: Apache-2.0 (confirm).
- **segmentation-models-pytorch** (qubvel) — U-Net/UPerNet/DeepLab decoders with
  many encoders. — Quick, well-tested segmentation heads for FloodAI water masks.
  — License: MIT.
- **rasterio / rioxarray / GDAL** — Raster I/O, reprojection, windowed reads. —
  Foundational raster plumbing across every module. — License: BSD/MIT/MIT-style.
- **leafmap / geopandas / shapely** — Vector analysis + interactive mapping. —
  InfraRisk exposure overlays, AOI handling, road-network geometry. — License:
  MIT / BSD.

## Foundation models (EO backbones)

- **Prithvi-EO-2.0** (NASA-IMPACT / IBM) — Multi-temporal EO foundation model
  (300M/600M) on Hugging Face; strong on flood (water IoU ~82.6 on Sen1Floods11)
  and land cover. — Recommended primary EO backbone; already the corpus's pick. —
  License: Apache-2.0 (model + code; confirm weights terms).
- **Clay** (Clay Foundation) — 632M ViT MAE on multi-sensor imagery + spatio-
  temporal metadata; produces general-purpose embeddings. — Alternative/compl.
  backbone for similarity search and few-label tasks. — License: Apache-2.0
  (code + weights); docs CC-BY-4.0.
- **SatlasPretrain** (Allen AI) — Foundation models + 302M-label pretraining set;
  +18% over ImageNet on 7 downstream EO tasks. — Strong pretrained weights for
  high/medium-res EO tasks. — License: models ODC-BY (dataset terms vary).
- **TerraMind** (IBM/ESA) — Recent multimodal generative EO foundation model
  (served via TerraTorch). — Watch-list backbone for multimodal (SAR+optical)
  fusion. — License: confirm.

## GIS copilots / LLM agents

- **LLM-Geo** (gladcolor) — Reference autonomous-GIS prototype: LLM generates +
  executes geoprocessing workflows to answer spatial questions. — Direct
  architectural blueprint for GeoCopilot's plan→code→execute loop. — License:
  open (confirm; research code).
- **GIS Copilot** (PSU GIScience) — LLM embedded in QGIS that auto-generates
  spatial-analysis workflows for non-experts. — Closest published analog to
  GeoCopilot; shows tool-grounding and UX patterns. — License: open-source
  (QGIS-based; confirm).
- **LangChain** — Agent/RAG framework: chains, tools, agents, retrievers. —
  Orchestrate GeoCopilot's ReAct-style tool-calling over EO/OR tools. — License:
  MIT.
- **LlamaIndex** — Data framework for RAG: connectors, indices, retrievers,
  agents. — Build the retrieval layer over TerraShield docs/method cards/metadata.
  — License: MIT.
- **Note on RAG infra:** pair LangChain/LlamaIndex with a vector store
  (**pgvector**, PostgreSQL-licensed; **Qdrant**/**Weaviate**, Apache-2.0/BSD) so
  GeoCopilot retrieval is grounded and self-hostable.

## Operations research (ResilienceOR)

- **PuLP** (coin-or) — Python LP/MILP modeling, ships with CBC solver. — Model
  MCLP shelter siting and knapsack allocation as MILPs. — License: BSD/MIT-style.
- **Google OR-Tools** (google) — CP-SAT, routing (VRP), and MILP solvers. —
  Production-grade evacuation routing + facility location at scale. — License:
  Apache-2.0.
- **NetworkX** — Graph algorithms incl. Dijkstra and betweenness centrality. —
  Road-network criticality (InfraRisk) and routing prototypes. — License:
  BSD-3-Clause.
- **scikit-criteria / pymcdm** — TOPSIS, AHP and other MCDM methods. — Off-the-
  shelf TOPSIS/AHP so ResilienceOR doesn't reimplement normalization/weighting
  edge cases. — License: BSD/MIT (confirm).

---

## Recommended adoption shortlist

1. **xclim + xarray + intake-esm** — adopt as the entire ClimateLens climate
   backbone (indices, bias correction, CMIP6 ingestion). Apache-2.0, mature.
2. **climate_indices** — adopt for DroughtAI SPI/SPEI (BSD, NOAA-used) instead of
   hand-rolling distribution fits.
3. **TorchGeo + TerraTorch + Prithvi-EO-2.0** — adopt as the EO ML stack; fine-
   tune Prithvi for FloodAI water segmentation via TerraTorch tasks.
4. **OR-Tools / PuLP + NetworkX** — adopt for ResilienceOR (MCLP, routing,
   knapsack, betweenness); permissive licenses.
5. **LangChain/LlamaIndex + a self-hostable vector store** — adopt for
   GeoCopilot's RAG + ReAct agent, exposing EO/OR functions as tools.
