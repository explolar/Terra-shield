# TerraShield AI — Research Methods Brief

A practical, citable methods brief for engineers building TerraShield's modules
(FloodAI, ClimateLens, DroughtAI, InfraRisk, GeoCopilot, EarthData Engine).

**Source corpus.** Derived from the research PDF library at `f:\Soil_term\paper`
(read via the pre-extracted text in `extracted/`). The library is heavily
soil-science / digital-soil-mapping (DSM) focused. Only a handful of papers are
directly about TerraShield modules (Prithvi geospatial foundation model, SAR
flood mapping, foundation-model fine-tuning). For the rest, this brief extracts
**transferable** geospatial-ML techniques (spatial cross-validation, Area of
Applicability, kriging, SHAP, ensemble uncertainty) and flags them as such.

> Honest gap note: the corpus has **no dedicated flood-susceptibility, CMIP6/WRF
> downscaling, SPI/VCI drought-index, or agentic-LLM/RAG papers**. Those sections
> below combine what the corpus *does* support (SAR water mapping via Prithvi,
> soil-moisture/vegetation indices, geostatistics) with explicit "not covered —
> bring external source" callouts so nobody over-claims a citation.

> Module-coverage note (2026-05-24): this brief predates two later modules —
> **WeatherCast** (short-range forecasts via the key-less Open-Meteo API) and
> **GroundwaterAI** (NASA GRACE/GRACE-FO terrestrial water storage; key references
> Tapley et al. 2004, Rodell et al. 2009/2018, Famiglietti 2014). Their methods and
> sources are documented in [`engineering.md`](engineering.md) §1.5–1.6 and
> [`modules.md`](modules.md); they are not part of the soil-science source corpus
> covered below.

---

## External references (web-sourced, 2026-05-23)

These references **fill the gaps** flagged in the original corpus brief (flood
susceptibility, CMIP6/SSP/WRF downscaling, SPI/VCI drought indices, exposure
frameworks, OR methods, agentic-LLM/RAG). Each is a peer-reviewed paper, official
dataset doc, or recognized standard. Authors (Year), Title, Venue, then a
one-line actionable takeaway. Reported metrics are quoted only where the source
states them; where a number could not be verified from the source page it is
described qualitatively rather than fabricated. Source URLs follow each module.

### FloodAI — flood susceptibility (AHP) + SAR/optical water segmentation

- **Saaty, T.L. (1980).** *The Analytic Hierarchy Process: Planning, Priority
  Setting, Resource Allocation.* McGraw-Hill. — Foundational MCDM method:
  derive criterion weights from pairwise comparisons on the 1–9 Saaty scale,
  with a consistency ratio (CR < 0.10) check. This is the weighting engine for a
  GIS weighted-overlay flood-susceptibility map.
- **Beven, K.J., & Kirkby, M.J. (1979).** *A physically based, variable
  contributing area model of basin hydrology (TOPMODEL).* Hydrological Sciences
  Bulletin 24(1):43–69. — Origin of the **Topographic Wetness Index**
  TWI = ln(a / tanβ) (upslope contributing area a over local slope tanβ). Use
  TWI as a core flood-conditioning factor; high TWI = water-accumulating terrain.
- **Recent AHP flood-susceptibility application (peer-reviewed, GIS-based).**
  E.g., GIS-based AHP + frequency-ratio flood susceptibility (ScienceDirect,
  2025) and tropical-basin AHP studies (Kerala, India). Typical conditioning
  stack: elevation, slope, distance-to-river, rainfall, drainage density, LULC,
  **TWI**, HAND, NDVI, soil/curvature; outputs classed into 5 zones (very low →
  very high). Takeaway: this factor stack + Saaty weights is the standard,
  citable FloodAI susceptibility recipe.
- **Bonafilia, D., Tellman, B., Anderson, T., & Issenberg, E. (2020).**
  *Sen1Floods11: A Georeferenced Dataset to Train and Test Deep Learning Flood
  Algorithms for Sentinel-1.* CVPR Workshops (IEEE/CVF), pp. 835–845. — 446
  hand-labeled 512×512 chips, 11 global flood events; the de-facto SAR flood
  benchmark. Key finding: **FCNNs trained on flood-water labels beat
  backscatter-thresholding**, and labeling *flood* water (not just permanent
  water) matters. Use as primary training/eval set.
- **Otsu thresholding for SAR water extraction.** Otsu (1979) histogram
  bi-level thresholding is the standard *unsupervised* SAR-water baseline (low
  VV/VH backscatter = smooth water); operationalized in UN-SPIDER's GEE
  Recommended Practice and tools like GEE4FLOOD/FLOMPY. Takeaway: ship Otsu as a
  fast, label-free fallback and DL baseline, ideally on a HAND-masked AOI to cut
  false positives.
- **Notarangelo, N.M., Wirion, C., & van Winsen, F. (2025).** *STURM-Flood: a
  curated dataset for deep learning-based flood extent mapping leveraging
  Sentinel-1 and Sentinel-2 imagery.* Big Earth Data (Taylor & Francis). —
  21,602 S-1 + 2,675 S-2 tiles (128×128, 10 m), 60 flood events, with Copernicus
  EMS ground truth. U-Net baselines: **S-1 ~83.6% acc / 0.833 weighted F1; S-2
  ~92.8% acc / 0.924 weighted F1** — optical wins when cloud-free; SAR is the
  all-weather workhorse.
- **Ronneberger, O., Fischer, P., & Brox, T. (2015).** *U-Net: Convolutional
  Networks for Biomedical Image Segmentation.* MICCAI, LNCS 9351:234–241. —
  Encoder–decoder with skip connections; the default segmentation backbone for
  flood water masks (used as the STURM-Flood and many SAR-flood baselines).
  Takeaway: U-Net is the sensible from-scratch baseline before reaching for a
  geospatial foundation model (cf. Prithvi water IoU 82.6 in the corpus brief).

Sources: https://link.springer.com/article/10.1007/BF01386390 ·
https://openaccess.thecvf.com/content_CVPRW_2020/html/w11/Bonafilia_Sen1Floods11_A_Georeferenced_Dataset_to_Train_and_Test_Deep_Learning_CVPRW_2020_paper.html ·
https://github.com/cloudtostreet/Sen1Floods11 ·
https://www.tandfonline.com/doi/full/10.1080/20964471.2025.2458714 ·
https://arxiv.org/abs/1505.04597 ·
https://www.sciencedirect.com/science/article/pii/S0921818125001407 ·
https://www.un-spider.org/advisory-support/recommended-practices/recommended-practice-google-earth-engine-flood-mapping/step-by-step ·
https://archive.org/details/analytichierarch0000saat

### ClimateLens — CMIP6/SSP, downscaling, bias correction, extreme indices

- **Thrasher, B., Wang, W., Michaelis, A., Melton, F., Lee, T., & Nemani, R.
  (2022).** *NASA Global Daily Downscaled Projections, CMIP6 (NEX-GDDP-CMIP6).*
  Scientific Data 9:262. — Daily, 1/4° (~25 km) statistically downscaled
  projections (1950–2100) via BCSD over CMIP6 GCMs and all Tier-1 SSPs; CC0
  license, on AWS/GEE. Takeaway: ClimateLens's fastest path to analysis-ready,
  bias-corrected SSP projections without running a dynamical model.
- **O'Neill, B.C., Tebaldi, C., van Vuuren, D.P., et al. (2016).** *The Scenario
  Model Intercomparison Project (ScenarioMIP) for CMIP6.* Geosci. Model Dev.
  9:3461–3482. — Defines the SSP×RCP scenario matrix (SSP1-2.6 … SSP5-8.5) used
  across CMIP6. Takeaway: present scenarios as SSP-RCP pairs and cite this for
  the framework; pair with Riahi et al. (2017) for the SSP narratives.
- **Giorgi, F., & Gutowski, W.J. (2015).** *Regional Dynamical Downscaling and
  the CORDEX Initiative.* Annual Review of Environment and Resources 40:467–490.
  — Review of nesting RCMs (e.g., **WRF**) inside GCMs under a coordinated
  protocol for high-resolution regional projections. Takeaway: cite for the
  CORDEX/WRF dynamical-downscaling track when statistical downscaling is
  insufficient (complex terrain, convective extremes).
- **Cannon, A.J., Sobie, S.R., & Murdock, T.Q. (2015).** *Bias Correction of GCM
  Precipitation by Quantile Mapping: How Well Do Methods Preserve Changes in
  Quantiles and Extremes?* Journal of Climate 28(17):6938–6959. — Introduces
  **Quantile Delta Mapping (QDM)**, which preserves the model's projected
  relative changes in quantiles (unlike naive QM, which can corrupt trends).
  Takeaway: use QDM (not plain quantile mapping) for ClimateLens precip/extreme
  bias correction.
- **Zhang, X., Alexander, L., Hegerl, G.C., et al. (2011).** *Indices for
  monitoring changes in extremes based on daily temperature and precipitation
  data.* WIREs Climate Change 2(6):851–870 (ETCCDI 27-index set). — Standard,
  reproducible definitions: **R95p** (annual precip from days > 1961–90 95th
  wet-day percentile), TXx, TN90p, WSDI/heatwave days (≥ N consecutive days >
  90th pct). Takeaway: implement ClimateLens extremes against ETCCDI/ETCCDI-style
  specs (computable via xclim) so numbers are comparable to the IPCC literature.

Sources: https://www.nature.com/articles/s41597-022-01393-4 ·
https://gmd.copernicus.org/articles/9/3461/2016/gmd-9-3461-2016.pdf ·
https://www.annualreviews.org/doi/10.1146/annurev-environ-102014-021217 ·
https://journals.ametsoc.org/view/journals/clim/28/17/jcli-d-14-00754.1.xml ·
https://etccdi.pacificclimate.org/list_27_indices.shtml ·
https://www.researchgate.net/publication/229537662

### DroughtAI — drought indices

- **McKee, T.B., Doesken, N.J., & Kleist, J. (1993).** *The relationship of
  drought frequency and duration to time scales.* 8th Conf. on Applied
  Climatology (AMS), Anaheim, pp. 179–184. — Defines the **SPI**: fit a
  **two-parameter gamma distribution** to accumulated precipitation at a chosen
  time scale (1–36 months), then transform the CDF to the standard normal (z).
  Drought when SPI < −1; multi-scale (SPI-3 meteorological → SPI-12 hydrological).
- **Vicente-Serrano, S.M., Beguería, S., & López-Moreno, J.I. (2010).** *A
  Multiscalar Drought Index Sensitive to Global Warming: The Standardized
  Precipitation Evapotranspiration Index (SPEI).* Journal of Climate
  23(7):1696–1718. — Like SPI but on the **climatic water balance (P − PET)**,
  fit to a log-logistic distribution; captures temperature-driven drying. Use
  SPEI alongside SPI so warming-amplified droughts are not missed.
- **Kogan, F.N. (1995).** *Application of vegetation index and brightness
  temperature for drought detection.* Advances in Space Research / Int. J.
  Remote Sensing (Monitoring regional drought using the VCI, IJRS 17(14)). —
  **VCI = 100 × (NDVI − NDVI_min)/(NDVI_max − NDVI_min)** per pixel over the
  historical record; VCI < 35% = extreme vegetation drought. Companion **TCI**
  uses brightness temperature. Takeaway: VCI/TCI give the EO vegetation-stress
  layer that complements precip-based SPI/SPEI.
- **Svoboda, M., LeComte, D., Hayes, M., et al. (2002).** *The Drought Monitor.*
  Bulletin of the American Meteorological Society 83(8):1181–1190. — The **US
  Drought Monitor** D0–D4 scheme (Abnormally Dry → Exceptional), a
  percentile-based blend of indicators (D0 ≈ 20–30th pct, D4 < 2nd pct).
  Takeaway: adopt the D0–D4 categories + percentile thresholds so DroughtAI
  outputs map to a recognized severity classification.

Sources: https://climatedataguide.ucar.edu/climate-data/standardized-precipitation-index-spi ·
https://journals.ametsoc.org/view/journals/clim/23/7/2009jcli2909.1.xml ·
https://www.tandfonline.com/doi/abs/10.1080/01431169608949106 ·
https://droughtmonitor.unl.edu/About/AbouttheData/DroughtClassification.aspx ·
https://www.droughtmanagement.info/literature/AMS_Drought_Monitor_2002.pdf

### InfraRisk — exposure, vulnerability, network criticality

- **Stevens, F.R., Gaughan, A.E., Linard, C., & Tatem, A.J. (2015).**
  *Disaggregating Census Data for Population Mapping Using Random Forests with
  Remotely-Sensed and Ancillary Data.* PLOS ONE 10(2):e0107042. — The
  Random-Forest **dasymetric** method behind **WorldPop** ~100 m gridded
  population. Takeaway: use WorldPop as the population-exposure layer; the RF
  weighting approach is reusable if you need a bespoke higher-res surface.
- **UNDRR — Global Assessment Report on Disaster Risk Reduction (GAR).** UN
  Office for Disaster Risk Reduction (biennial). — Operationalizes **Risk =
  Hazard × Exposure × Vulnerability** via a Global Risk Model (earthquake,
  flood, cyclone, storm surge). Takeaway: frame InfraRisk on the GAR
  hazard/exposure/vulnerability triad, consistent with the Sendai Framework, so
  outputs align with international DRR reporting.
- **Road-network criticality via betweenness centrality.** Multiple
  peer-reviewed studies (e.g., Gauthier et al. 2018, *Transportation Research
  Record*; AIP *Chaos* 2024) use (edge) **betweenness centrality** and
  connected-component / largest-component loss under link removal to rank
  critical road segments for disaster access. Takeaway: compute link betweenness
  on the routable graph to flag segments whose failure most degrades emergency
  access; pairs naturally with Dijkstra-based routing (ResilienceOR).

Sources: https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0107042 ·
https://www.worldpop.org/methods/ ·
https://www.undrr.org/gar ·
https://journals.sagepub.com/doi/10.1177/0361198118792115 ·
https://pubs.aip.org/aip/cha/article/34/1/013124/3037471

### ResilienceOR — multi-criteria, location, routing, knapsack

- **Saaty, T.L. (1980).** *The Analytic Hierarchy Process.* McGraw-Hill. —
  (See FloodAI.) AHP for deriving criterion weights with a consistency check;
  TerraShield's general multi-criteria weighting engine.
- **Hwang, C.L., & Yoon, K. (1981).** *Multiple Attribute Decision Making:
  Methods and Applications — A State-of-the-Art Survey.* Springer. — **TOPSIS**:
  rank alternatives by closeness to the positive-ideal and distance from the
  negative-ideal solution (normalize → weight → distances → closeness ratio).
  Takeaway: AHP for weights + TOPSIS for ranking sites/options is the canonical
  pairing.
- **Church, R., & ReVelle, C. (1974).** *The Maximal Covering Location Problem.*
  Papers in Regional Science 32(1):101–118. — **MCLP**: site p facilities to
  maximize demand covered within a service radius. Takeaway: the exact model for
  shelter/relief-depot siting; an integer program in TerraShield's optimizer.
- **Nemhauser, G.L., Wolsey, L.A., & Fisher, M.L. (1978).** *An analysis of
  approximations for maximizing submodular set functions—I.* Mathematical
  Programming 14:265–294. — Greedy maximization of a monotone submodular
  function (coverage is submodular) gives a **(1 − 1/e) ≈ 0.632 optimality
  guarantee**. Takeaway: cite this when using greedy facility selection — it's a
  provably near-optimal, scalable alternative to solving MCLP to optimality.
- **Dijkstra, E.W. (1959).** *A note on two problems in connexion with graphs.*
  Numerische Mathematik 1:269–271. — Single-source shortest paths on
  non-negative-weighted graphs; the basis for evacuation/relief routing and the
  betweenness computations above.
- **Bellman, R. (1957).** *Dynamic Programming.* Princeton University Press. —
  The DP principle underpinning the **0/1 knapsack** resource-allocation solver
  (O(nW) table) for budget-constrained relief-asset selection. Takeaway: cite
  Bellman for the DP/knapsack module rather than an ad-hoc reference.
- **OR for disaster relief (recent).** Survey/modeling work on shelter
  location-allocation and evacuation routing (e.g., multi-objective
  location-allocation, *J. of Safety Science & Resilience* 2021; two-stage
  stochastic facility-location/inventory/evacuation models, EJOR/Comp. & OR
  2024–2026) shows the field favors **multi-objective, stochastic/robust**
  formulations integrating facility location + pre-positioning + evacuation.
  Takeaway: position ResilienceOR's MCLP/Dijkstra/knapsack stack within this
  integrated framing, adding uncertainty where decisions are high-stakes.

Sources: https://link.springer.com/article/10.1007/BF01942293 ·
https://link.springer.com/book/10.1007/978-3-642-48318-9 ·
https://link.springer.com/article/10.1007/BF01588971 ·
https://link.springer.com/article/10.1007/BF01386390 ·
https://www.sciencedirect.com/science/article/pii/S2092521221000031 ·
https://arxiv.org/html/2505.03979v1

### GeoCopilot / GenAI for geospatial — RAG, agents, GIS copilots

- **Lewis, P., Perez, E., Piktus, A., et al. (2020).** *Retrieval-Augmented
  Generation for Knowledge-Intensive NLP Tasks.* NeurIPS 2020. — Combine a dense
  retriever over a document index (non-parametric memory) with a seq2seq
  generator to ground answers and cut hallucination. Takeaway: GeoCopilot should
  RAG over TerraShield docs/metadata/method cards so answers cite real sources.
- **Yao, S., Zhao, J., Yu, D., et al. (2023).** *ReAct: Synergizing Reasoning and
  Acting in Language Models.* ICLR 2023. — Interleave reasoning traces with
  tool-call actions so the agent plans, calls tools, and incorporates results.
  Takeaway: the reference pattern for GeoCopilot's agent loop over named
  EO/analysis tools (TerraTorch tasks, GEE ops, the OR solvers).
- **Li, Z., & Ning, H. (2023).** *Autonomous GIS: the next-generation AI-powered
  GIS (LLM-Geo).* International Journal of Digital Earth 16(2):4668–4686. —
  Prototype where an LLM autonomously generates and executes geoprocessing
  workflows (self-generating/organizing/verifying/executing/growing). Takeaway:
  the seminal "autonomous GIS" reference that directly motivates GeoCopilot.
- **Akinboyewa, T., Li, Z., Ning, H., & Lessani, M.N. (2025).** *GIS Copilot:
  towards an autonomous GIS agent for spatial analysis.* International Journal of
  Digital Earth 18:2497489. — Embeds an LLM into QGIS to auto-generate spatial
  workflows for non-experts (open-source). Takeaway: concrete, recent blueprint
  (and benchmark expectations) for a production GIS copilot.
- **GeoBenchX (2025, arXiv 2503.18129)** and **LLM-Find (Ning et al., 2024,
  arXiv 2407.21024).** — Benchmarking multi-step geospatial agents, and an
  autonomous agent for geospatial *data retrieval*. Takeaway: use GeoBenchX-style
  multi-step task suites to evaluate GeoCopilot; reuse the LLM-Find pattern for
  the data-acquisition sub-agent.

Sources: https://arxiv.org/abs/2005.11401 ·
https://arxiv.org/abs/2210.03629 ·
https://doi.org/10.1080/17538947.2023.2278895 ·
https://www.tandfonline.com/doi/full/10.1080/17538947.2025.2497489 ·
https://arxiv.org/html/2503.18129v2 ·
https://arxiv.org/pdf/2407.21024

---

## FloodAI — SAR flood mapping & water segmentation

- **Use Sen1Floods11 as the primary benchmark/training set.** It is 446 chips of
  512×512, paired Sentinel-1 (SAR) + Sentinel-2 (optical) imagery, covering 14
  biomes, 357 ecoregions, 6 continents, across 11 flood events (2018–2020). Labels
  are binary: 0 = land, 1 = water (Szwarcman et al., 2025; Prithvi-EO-2.0). This is
  the de-facto reference dataset for the FloodAI water/no-water task. (Note:
  STURM-Flood was requested but does not appear in this corpus — source it
  externally.)
- **Fine-tune the Prithvi-EO-2.0 geospatial foundation model for water
  segmentation rather than training a U-Net from scratch.** On Sen1Floods11,
  Prithvi-EO-2.0-300M with temporal+location embeddings reaches mIoU 90.0, mF1
  97.7, and **water-class IoU 82.6** — a +3.0–3.5 IoU gain on the minority water
  class vs. Prithvi-EO-1.0-100M (water IoU 79.6) (Szwarcman et al., 2025). The
  model is on Hugging Face (`ibm-nasa-geospatial/Prithvi-EO-2.0`) and IBM
  TerraTorch.
- **Concrete training recipe (directly reusable).** UPerNet decoder head on the
  frozen-or-fine-tuned ViT encoder; cross-entropy loss; 50 epochs with
  early-stopping patience 20; random H/V flips for augmentation; tune only weight
  decay + learning rate (10 trials), then repeat best config over 10 seeds for
  variance reporting. Because the 600M model uses a 14×14 patch, **resize 512×512
  chips to 448×448** (divisible by 14) instead of padding/cropping (Szwarcman et
  al., 2025).
- **The water class is heavily imbalanced — average metrics hide it.** Report and
  optimize the **per-class water IoU**, not just mIoU; "land" is trivially easy and
  inflates the mean (Szwarcman et al., 2025). Pair this with the imbalance handling
  from the fine-tuning study below (Focal/Dice loss).
- **SAR feature engineering beyond raw backscatter (transferable from soil DSM).**
  A Sentinel-1 study found that **GLCM texture features and interferometric
  coherence each outperform backscatter intensity alone**, and fusing
  backscatter + coherence + texture gives the best result; texture/GLCM also
  **reduces speckle-related noise** (Dai et al., 2026, soil total-N mapping — method
  transfers to flood feature stacks). Practical takeaway for FloodAI: stack VV/VH
  backscatter **plus** GLCM texture **plus** 6/12-day interferometric coherence
  (coherence drops sharply over newly inundated surfaces) rather than thresholding
  backscatter alone. Sentinel-1's 6-day (two-satellite) / 12-day revisit defines
  the temporal resolution ceiling for change-based flood detection (Dai et al.,
  2026).
- **Optical water indices for the Sentinel-2 fusion branch (transferable).** NDWI
  and SWCI (Surface Water Capacity Index) were the strongest water-sensitive
  spectral indices for surface moisture in a Sentinel-2 study (Sedaghat et al.,
  2022) — useful as auxiliary bands or for the cloud-free optical confirmation
  layer in a SAR+optical flood product.

---

## ClimateLens — CMIP6 / SSP, downscaling, bias correction, extreme indices

> Gap note: **no CMIP6/SSP/WRF/statistical-downscaling paper exists in this
> corpus.** Do not cite these papers for GCM bias-correction or SSP-scenario
> handling; bring an external source (e.g., ISIMIP/CMIP6 bias-adjustment
> literature). The corpus only supports *gridded climate covariate handling*,
> which is the transferable piece below.

- **Use analysis-ready, pre-interpolated gridded climate layers as model
  covariates.** WorldClim (mean annual temperature MAT, mean annual precipitation
  MAP) is pulled directly from Google Earth Engine as long-term climatic summaries
  interpolated from station observations and used as model inputs (Dai et al.,
  2026). For higher-resolution downscaled climatology, **CHELSA V.2.1** (Karger et
  al., 2017) is used as a covariate source in global mapping (OpenLandMap, Hengl et
  al., 2026). Takeaway: ClimateLens can stand up a covariate layer quickly on
  WorldClim/CHELSA before investing in dynamical downscaling.
- **Validate any temporal climate model with leave-one-year-out (LOYO)
  cross-validation.** OpenLandMap reports **LOYO CV alongside spatial-blocking CV**
  specifically to avoid over-optimistic skill when years are correlated (Hengl et
  al., 2026). This is the correct evaluation protocol for ClimateLens time-series
  projections / hindcasts.
- **Extreme indices:** not covered by any paper here — implement standard ETCCDI
  indices from an external spec.

---

## DroughtAI — drought indices, soil moisture, vegetation condition

> Gap note: **no paper computes SPI, VCI, or TCI.** The SPI/VCI computation
> details requested are not derivable from this corpus and must come from an
> external reference (e.g., McKee et al. 1993 for SPI; Kogan for VCI). What the
> corpus supports is the **remote-sensing soil-moisture and vegetation-index**
> inputs that feed a drought engine.

- **Estimate surface soil moisture from Sentinel-2 with Random Forest + water
  indices (transferable input for DroughtAI).** Combining basic soil properties
  with NDWI and SWCI, an RF pedotransfer model reached R² ≈ 0.79 and RMSE ≈ 0.028
  cm³/cm³, clearly beating multiple linear regression; spectral indices **alone**
  were insufficient — pairing them with physical priors mattered (Sedaghat et al.,
  2022). Takeaway: a soil-moisture-deficit drought layer can be built from
  Sentinel-2 NDWI/SWCI + RF without microwave SM products.
- **NDVI / SAVI / EVI are the workhorse vegetation-stress predictors.** Across
  multiple corpus papers NDVI is the single most-used remote-sensing index (e.g.,
  80% of soil-texture studies; Mgohele et al., 2024), and NDVI/EVI/SAVI were key
  predictors of carbon/vegetation state (Beisekenov et al., 2025). For DroughtAI's
  VCI, the operational building block is a long NDVI time series normalized to its
  historical min/max per pixel — compute VCI = (NDVI − NDVI_min)/(NDVI_max −
  NDVI_min) (method standard; corpus supplies the NDVI pipeline, not the VCI
  formula itself).
- **CNN-LSTM spatio-temporal stacks capture stress phenology (transferable
  architecture).** A spatio-temporal pipeline merging a CNN (spatial features) with
  an LSTM (temporal dependencies) over time-series imagery hit 98% accuracy
  classifying multi-factor plant stress (incl. drought), vastly beating a
  spatial-only CNN (80%) (Patra & Sahoo, 2025). Takeaway for DroughtAI: model
  drought as a **temporal-sequence** problem (CNN-LSTM or temporal transformer over
  NDVI/soil-moisture stacks), not a single-date classification.

---

## InfraRisk — exposure & vulnerability modeling

> Gap note: **no infrastructure-exposure or hazard-vulnerability paper exists in
> this corpus.** Treat this section as transferable-methods only.

- **Map exposure/vulnerability as a regression-on-covariates problem with
  quantified per-pixel uncertainty.** The DSM stack (RF/XGBoost over
  SCORPAN-style covariates with quantile-based uncertainty — see Cross-cutting
  GeoAI) is directly reusable for spatializing a vulnerability index over an AOI
  when only point/admin samples exist.
- **Use the Area of Applicability to mask where the exposure model is
  untrustworthy.** When extrapolating a vulnerability model to new regions, the
  DI/AOA method (Meyer & Pebesma, applied by Kumar et al., 2025) flags
  out-of-distribution areas — critical for InfraRisk so the platform doesn't render
  confident risk scores where it has no analog training data.

---

## GeoCopilot / GenAI for geospatial — RAG, agentic tool-calling

> Gap note: **the corpus contains no LLM/RAG/agentic-GeoAI paper.** Do not
> fabricate citations for GeoCopilot. The only adjacent, citable idea is below.

- **Tooling/distribution pattern for serving geospatial models to non-experts.**
  Prithvi-EO-2.0 was deliberately onboarded onto **IBM TerraTorch** and shipped on
  Hugging Face precisely to close the "model creator ↔ end-user" gap, with subject-
  matter experts kept in the loop on model/dataset design (Szwarcman et al., 2025).
  Takeaway for GeoCopilot: expose underlying EO models as **named, parameterized
  tools** (a TerraTorch-style task registry) that an agent can call, and keep an
  SME-feedback loop in the product. RAG/agent-orchestration specifics must be
  sourced externally.

---

## Cross-cutting GeoAI — spatial CV, Area of Applicability, uncertainty, foundation models, explainability

This is the richest, most transferable part of the corpus. Apply across **every**
TerraShield module.

### Spatial cross-validation (avoid inflated accuracy)
- **Random k-fold CV massively over-states geospatial accuracy; always also report
  spatial CV.** A nutrient-mapping study saw R² collapse from **0.96 (random CV) to
  0.02–0.27 (spatial CV)** — the random split leaked spatial autocorrelation (Kumar
  et al., 2025). Make spatial CV the headline metric in TerraShield model cards.
- **Use spatial blocking CV with explicit block sizes.** OpenLandMap uses **5-fold
  spatial blocking with 100×100 km blocks** plus **leave-one-year-out** CV to
  prevent over-optimistic results from clustered/dense samples (Hengl et al., 2026;
  also SoilGrids 2.0, Poggio et al., 2021).

### Area of Applicability (AOA) & Dissimilarity Index (DI)
- **Compute the AOA to delineate where predictions are reliable.** Procedure:
  (a) compute the **Dissimilarity Index** = minimum (weighted) distance of each
  prediction pixel from the training data in multivariate predictor space; (b)
  threshold DI at the **0.95 quantile** of training-data DI values; pixels above
  the threshold are **outside** the AOA and should be masked or flagged (Kumar et
  al., 2025). Ship this as a "confidence mask" layer on every TerraShield map.

### Uncertainty quantification
- **Quantile Regression Forests (QRF) give per-pixel prediction intervals at
  scale.** SoilGrids 2.0 produces global maps **with quantified spatial
  uncertainty** using QRF over 240,000 sample locations and 400+ covariates,
  including cross-validation and hyper-parameter selection (Poggio et al., 2021).
  Reuse QRF (or gradient-boosting quantile loss) wherever TerraShield needs
  calibrated intervals, not just point predictions.
- **Validate interval calibration with PICP.** Use **Prediction Interval Coverage
  Probability** — the fraction of observations falling inside the stated interval —
  to check that a "90% interval" actually covers ~90% (Kumar et al., 2025). Report
  PICP per module.
- **Geostatistics still earns its place.** Variogram analysis + kriging/co-kriging
  provide spatial-autocorrelation-aware interpolation and native uncertainty;
  hybrid **geostatistics + ML** (e.g., RF/XGBoost residual kriging, "regression
  kriging") consistently outperforms either alone (Caires De et al., 2025, DSM
  synoptic review; SCORPAN framework). Use for sparse-sample AOIs where pure ML
  lacks support.

### Foundation models (Prithvi / geospatial)
- **Prithvi-EO-2.0 is the recommended EO backbone.** A multi-temporal geospatial
  foundation model (300M & 600M params) pretrained via masked-autoencoding on 4.2M
  global HLS (Harmonized Landsat–Sentinel-2) time-series samples at 30 m, with
  transformer attention in **both space and time** and explicit **temporal +
  location embeddings** from image metadata. It beats Prithvi-EO-1.0 by 8% on
  GEO-Bench and outperforms 6 other GFMs across 0.1–15 m resolutions (Szwarcman et
  al., 2025). It generalizes to disaster response (flood), land-cover/crop mapping,
  and ecosystem monitoring — i.e., reusable across FloodAI, DroughtAI, EarthData.
- **The temporal + location embeddings are worth the complexity.** Adding them
  (the `-TL` variants) gave the best Sen1Floods11 water IoU, confirming metadata
  conditioning helps even on a single-date-ish task (Szwarcman et al., 2025).
- **Fine-tuning strategy: full fine-tune > frozen encoder > train-from-scratch.**
  An ablation fine-tuning Prithvi-EO-2.0 for crop type/health found **full
  fine-tuning consistently best** (F1 0.79 crop-type), with the frozen-encoder
  feature-extractor and from-scratch baselines worse (Tomotaki-Dawoud et al.,
  2025). Recipe: AdamW, lr 1e-4, ~100 epochs, 3 temporal HLS slices (early/mid/late
  season), and **Dice or Focal loss** to fight class imbalance. Budget for class
  imbalance and small-field spatial-resolution limits in smallholder/heterogeneous
  AOIs.
- **Foundation-model lineage to know:** SatMAE (MAE on satellite imagery, spectral
  grouping) and Scale-MAE (band-pass MAE for multi-scale) are the cited precursors
  (Szwarcman et al., 2025) — useful if benchmarking alternative backbones.
  (Aurora and SkySense were requested but are not in this corpus — source
  externally.)

### Explainability (SHAP / XAI)
- **Use SHAP to interpret black-box geospatial models, including CNNs, in both
  feature and geographic space.** SHapley Additive exPlanations (Lundberg & Lee,
  2017) attribute each prediction to covariate contributions; a CNN soil-mapping
  study used SHAP to spatially explain predictions and clarify which covariates
  drove which regions (Beucher et al., 2021). Pair with **RF-based recursive
  feature elimination** for principled covariate selection (Beucher et al., 2021).
  Takeaway: every TerraShield risk score should be explainable via SHAP per-pixel /
  per-feature attributions.

### Modeling defaults that recur across the corpus
- **Random Forest and XGBoost are the strongest, most-used tabular geospatial
  learners**; QRF for uncertainty; SVM/ANN as comparators (Caires De et al., 2025;
  Mgohele et al., 2024; Poggio et al., 2021). Start there before deep nets for
  tabular covariate problems.
- **Covariate design: SCORPAN.** Organize predictors as Soil/State, Climate,
  Organisms/vegetation (NDVI/SAVI), Relief (DEM derivatives — slope, TRI, valley
  depth), Parent material, Age, plus spatial position (Caires De et al., 2025;
  nature2025 SOC study). Directly maps to TerraShield's covariate stack for any
  hazard model.

---

## Key citations

Papers actually used in this brief (filename in the source library noted for
traceability).

1. **Szwarcman, D., Roy, S., Fraccaro, P., et al. (2025).** *Prithvi-EO-2.0: A
   Versatile Multi-Temporal Foundation Model for Earth Observation Applications.*
   IBM Research / NASA technical report & IEEE preprint.
   (`RSE Prithvi Global.txt`, `2412.02732v3.txt`)
2. **Tomotaki-Dawoud, K., Chaliganti, R., Chauhan, S.C., et al. (2025).**
   *Fine-Tuning the Prithvi Foundation Model for Crop-Type and Health Mapping in
   Smallholder Farms.* Procedia Computer Science 270 (KES 2025), 5055–5064.
   (`1-s2.0-S1877050925033058-main.txt`)
3. **Dai, D., Zhang, H., Geng, Y., et al. (2026).** *Integrated Exploitation of
   Sentinel-1 Backscatter, Interferometric Coherence, and Texture Features for
   Digital Mapping of Soil Total Nitrogen Across the Iberian Peninsula.* Agronomy
   16(4):750. (SAR feature-engineering methods, transferable to FloodAI.)
   (`agronomy-16-00750-v2.txt`)
4. **Kumar, A., Moharana, P.C., Jena, R.K., et al. (2025).** *Prediction of soil
   available nitrogen using machine learning and digital mapping techniques in
   Northeast India.* (Spatial CV, AOA/DI, PICP uncertainty — transferable.)
   (`1-s2.0-S266701002500294X-main.txt`)
5. **Poggio, L., de Sousa, L.M., Batjes, N.H., et al. (2021).** *SoilGrids 2.0:
   producing soil information for the globe with quantified spatial uncertainty.*
   SOIL 7. (QRF uncertainty, cross-validation, covariate selection — transferable.)
   (`soilgrids2021_poggio.txt`)
6. **Hengl, T., et al. (2026).** *OpenLandMap soil database / global mapping
   framework.* (Spatial-blocking CV with 100×100 km blocks, LOYO CV, CHELSA
   climate covariates — transferable.) (`openlandmap2026_soildb.txt`)
7. **Sedaghat, A., Shabanpour Shahrestani, M., Noroozi, A.A., et al. (2022).**
   *Developing pedotransfer functions using Sentinel-2 satellite spectral indices
   and Machine learning for estimating the surface soil moisture.* Journal of
   Hydrology 606:127423. (NDWI/SWCI + RF soil moisture — DroughtAI input.)
   (`1-s2.0-S0022169421014736-main.txt`)
8. **Patra, A.K., & Sahoo, L. (2025).** *Improved Classification of Nitrogen
   Stress Severity in Plants Under Combined Stress Conditions Using a
   Spatio-Temporal Deep Learning Framework.* arXiv 2509.06625. (CNN-LSTM
   spatio-temporal architecture — transferable to DroughtAI.)
   (`2509.06625v2.txt`)
9. **Beucher, A., et al. (2021).** *Interpretation of convolutional neural
   networks for acid sulfate soil classification (SHAP/XAI).* Frontiers in
   Environmental Science. (SHAP explainability + RF-RFE feature selection.)
   (`frontiers2021_cnn_acid_soil.txt`)
10. **Caires De, S., et al. (2025).** *Synoptic review of digital soil mapping:
    geostatistics, kriging, and ML hybrids.* Discover Soil 2:53. (Kriging /
    variogram / RF-XGBoost hybrid methods, SCORPAN — transferable.)
    (`springer2025_dsm_synoptic_review.txt`)
11. **Beisekenov, N., Banakinaou, W., Ajayi, A.D., et al. (2025).**
    *Remote sensing-based soil organic carbon monitoring using advanced ML under
    conservation agriculture.* (Sentinel-1 SAR + Sentinel-2 fusion; XGBoost;
    NDVI/EVI/SAVI predictors — transferable to FloodAI/DroughtAI feature stacks.)
    (`1-s2.0-S2772375525002692-main.txt`)
12. **Mgohele, R.N., Massawe, B.H.J., Shitindi, M.J., et al. (2024).**
    *Prediction of soil texture using remote sensing data: a systematic review.*
    Frontiers in Remote Sensing 5:1461537. (NDVI/SAVI covariate prevalence; RF/QRF
    dominance — transferable covariate guidance.) (`frsen-5-1461537.txt`)

*Reference notes:* Lundberg & Lee (2017, SHAP), Karger et al. (2017, CHELSA),
Rußwurm & Körner (ConvLSTM crop classification), Meyer & Pebesma (AOA) are cited
*within* the above papers and noted inline where their method is used; they were
not read directly.
