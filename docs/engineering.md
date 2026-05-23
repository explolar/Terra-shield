# TerraShield AI — Engineering & Methods

> The tech *is* the product. This document is the scientific and algorithmic
> spine of TerraShield: every method names its source, its data structure, and
> its computational complexity. Nothing here is hand-wavy.

## 0. Design tenets

1. **Decoupled compute.** `terrashield_geo` (the EarthData Engine) is a pure
   library: no web framework, no globals beyond the GEE gateway. It is unit-testable
   and reusable from notebooks or batch jobs.
2. **Offline-deterministic.** Every analytic has a live (Earth Engine) path and a
   deterministic demo path seeded by the AOI (`hashlib.sha256` → NumPy PRNG). The
   API shape is identical; a `source: live|demo` field never lets the two be confused.
3. **Honest uncertainty.** Following the digital-soil-mapping rigor of the sister
   TerrAI project, FloodAI ships an Area-of-Applicability reliability signal and
   reports spatial-cross-validation as the headline metric, not random-CV.
4. **Decisions, not just maps.** The ResilienceOR layer turns hazard surfaces into
   constrained decisions with provable approximation bounds.

---

## 1. Geospatial analytics

### 1.1 FloodAI — multi-criteria susceptibility
A weighted linear combination of conditioning factors, each unit-scaled to [0,1]
(low elevation/slope and high TWI/drainage-proximity/rainfall raise risk):

```
S(x) = Σ_k w_k · f_k(x),     Σ_k w_k = 1
```

- **Factors & sources:** elevation/slope (SRTM, *Farr et al., 2007*); Topographic
  Wetness Index `TWI = ln(a / tanβ)` from upstream area (MERIT Hydro, *Yamazaki et
  al., 2019*; TWI: *Beven & Kirkby, 1979*); drainage proximity (JRC Global Surface
  Water, *Pekel et al., 2016*); rainfall (CHIRPS, *Funk et al., 2015*); land use
  (ESA WorldCover).
- **Weights** are derived by **AHP** (§3.1), not guessed — a defensible, auditable
  process with a consistency check.
- **Data structure:** band-stacked `ee.Image`; reductions via `reduceRegion`.

### 1.2 FloodAI — SAR inundation
Sentinel-1 GRD (VV) change detection: open water is specularly dark, so a post-event
backscatter drop flags new water. Threshold via Otsu's method (*Otsu, 1979*) /
fixed dB. Datasets/benchmarks: Sen1Floods11 (*Bonafilia et al., 2020*), STURM-Flood
(*2025*). Reported metric: IoU against Copernicus EMS footprints. Prithvi-EO-2.0
(*Szwarcman et al., 2025*) is the planned learned-segmentation backbone (Sen1Floods11
water IoU ≈ 82.6).

### 1.3 ClimateLens — CMIP6/SSP projections
NEX-GDDP-CMIP6 (*Thrasher et al., 2022*), 0.25°, daily, bias-corrected & statistically
downscaled. Δ = period-mean(SSP, horizon) − period-mean(historical, 1995–2014).
Units normalised (`pr`: kg m⁻² s⁻¹ → mm yr⁻¹; `tas`: K → °C). SSP framework: *O'Neill
et al., 2016*. Extreme indices (R95p, heatwave days) per ETCCDI are on the roadmap.

### 1.4 DroughtAI — SPI & VCI
- **SPI** (*McKee et al., 1993*): fit a gamma distribution to the k-month precipitation
  accumulation (CHIRPS), transform the CDF to the standard normal; classify D0–D4.
  Live path uses a historical z-score approximation pending full gamma fitting.
- **VCI** (*Kogan, 1995*): `VCI = (NDVI − NDVI_min)/(NDVI_max − NDVI_min)` from
  MODIS MOD13, clamped to [0,1].

### 1.5 Tile strategy
No rasters cross the backend. A styled `ee.Image` yields a `getMapId()` XYZ tile
template streamed by Leaflet from Google's edge — O(1) payload regardless of AOI.
Demo mode instead returns a GeoJSON cell grid (an n×n choropleth) rendered client-side.

---

## 2. Reliability & validation (cross-cutting GeoAI)

- **Spatial cross-validation** is mandatory: random K-fold leaks spatially
  autocorrelated samples and inflates R²; one corpus study showed R² collapse from
  0.96 (random) to 0.02–0.27 (spatial). We block by geography (KMeans on
  coordinates → GroupKFold) — *Meyer et al., 2019; Roberts et al., 2017*.
- **Area of Applicability (AOA)** (*Meyer & Pebesma, 2021*): a Dissimilarity Index
  in (weighted) feature space; `DI > 1` ⇒ outside the AOA ⇒ the prediction is an
  extrapolation and is masked/flagged. FloodAI returns `reliability.applicable_pct`.
- **Calibrated uncertainty:** Quantile Regression Forests + PICP (coverage of
  prediction intervals) — *Meinshausen, 2006*.
- **Explainability:** SHAP (*Lundberg & Lee, 2017*) for factor attribution.

---

## 3. ResilienceOR — operations research

Each method below is in `terrashield_geo/optimize.py` with the stated complexity.

### 3.1 AHP — weight derivation · O(n²)
Analytic Hierarchy Process (*Saaty, 1980*). From a positive reciprocal pairwise
matrix A, the priority vector is the principal eigenvector, approximated by the
row geometric mean (exact for consistent matrices). Consistency:

```
λmax = mean_i (A w)_i / w_i ;  CI = (λmax − n)/(n − 1) ;  CR = CI / RI(n)
```

`CR ≤ 0.10` ⇒ judgements acceptably consistent. The default flood matrix yields
CR ≈ 0.012 (consistent). **Data structure:** dense NumPy matrix.

### 3.2 TOPSIS — multi-criteria ranking · O(m·k)
Technique for Order Preference by Similarity to Ideal Solution (*Hwang & Yoon,
1981*). Vector-normalise the m×k decision matrix, weight it, find the ideal-best
and ideal-worst per criterion (benefit vs. cost), and rank alternatives by
relative closeness `C = d⁻ / (d⁺ + d⁻)`. Used to rank districts by composite risk.

### 3.3 Relief-shelter siting — MCLP · greedy O(p·S·D)
Maximal Covering Location Problem (*Church & ReVelle, 1974*): choose p facilities
to cover the most demand (exposed population) within a service radius. NP-hard, but
coverage is **monotone submodular**, so the greedy algorithm is a `(1 − 1/e) ≈
0.632` approximation (*Nemhauser, Wolsey & Fisher, 1978*). **Data structures:**
per-site coverage sets (`set[int]`); haversine distance gate. Swap in an ILP
(PuLP/OR-Tools) behind the same signature for exact optima on small instances.

### 3.4 Evacuation routing — Dijkstra · O(E log V)
Shortest path (*Dijkstra, 1959*) on an adjacency-list road graph with a binary
min-heap (`heapq`). Edge weight = physical length (km); flooded edges carry a large
additive penalty so a route through water is chosen only if no dry alternative
exists — surfacing "no safe route" honestly rather than failing silently.
**Data structures:** `RoadGraph` (adjacency list), priority queue, predecessor map.

### 3.5 Mitigation planning — 0/1 knapsack · DP O(n·B)
Bellman dynamic programming (*Bellman, 1957*): pick interventions maximising total
expected risk reduction (e.g. Expected Annual Damage avoided) under a budget B.
Costs discretised to a granularity to bound the table; choice matrix enables exact
reconstruction of the selected set.

---

## 4. Backend systems

- **Framework:** FastAPI (async), pydantic v2 strict request validation.
- **Caching:** in-process TTL cache keyed by `sha256(namespace + normalised request)`;
  GEE calls are slow and quota-limited, so memoisation is first-class. Redis-swappable.
- **Rate limiting:** per-IP token bucket (O(1) amortised) guarding compute endpoints.
- **Observability:** request-id middleware, structured (JSON in prod) logging, timing.
- **Errors:** typed `{error, detail, hint}` envelope; GEE traces never leak.

### Complexity summary

| Operation | Method | Complexity |
|-----------|--------|-----------|
| Flood susceptibility | weighted overlay | O(P) pixels |
| AHP weights | geometric-mean eigenvector | O(n²) |
| TOPSIS | normalise + distance | O(m·k) |
| Shelter siting | greedy MCLP | O(p·S·D) |
| Evacuation route | Dijkstra (heap) | O(E log V) |
| Mitigation | 0/1 knapsack DP | O(n·B) |
| Cache lookup | hash | O(1) |
| Rate limit | token bucket | O(1) |

---

## 5. Key references

Beven & Kirkby (1979) *Hydrol. Sci. Bull.* · Bellman (1957) *Dynamic Programming* ·
Bonafilia et al. (2020) Sen1Floods11, *CVPRW* · Church & ReVelle (1974) *Papers Reg.
Sci.* · Dijkstra (1959) *Numer. Math.* · Farr et al. (2007) SRTM, *Rev. Geophys.* ·
Funk et al. (2015) CHIRPS, *Sci. Data* · Hwang & Yoon (1981) *MADM* · Kogan (1995)
VCI, *Adv. Space Res.* · Lundberg & Lee (2017) SHAP, *NeurIPS* · McKee et al. (1993)
SPI, *AMS* · Meinshausen (2006) QRF, *JMLR* · Meyer & Pebesma (2021) AOA, *Methods
Ecol. Evol.* · Nemhauser, Wolsey & Fisher (1978) *Math. Prog.* · O'Neill et al.
(2016) SSP, *Geosci. Model Dev.* · Otsu (1979) *IEEE SMC* · Pekel et al. (2016) JRC
GSW, *Nature* · Saaty (1980) AHP · Szwarcman et al. (2025) Prithvi-EO-2.0 · Thrasher
et al. (2022) NEX-GDDP-CMIP6, *Sci. Data* · Yamazaki et al. (2019) MERIT Hydro, *WRR*.

A fuller, module-by-module literature brief is in [`research-notes.md`](research-notes.md).
