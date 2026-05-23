# terrashield-geo — EarthData Engine

The geospatial compute library behind TerraShield AI. It is deliberately
decoupled from the web layer: import it from FastAPI, a notebook, or a batch job.

## Design rules

1. **Runs offline.** Every compute function works without Earth Engine by
   returning a deterministic *demo* result (seeded by the AOI). The backend and
   frontend can be developed end-to-end with zero credentials.
2. **One GEE gateway.** All Earth Engine access goes through `gee.init()` /
   `gee.is_live()`. Earth Engine is imported lazily so the package installs and
   imports without `earthengine-api`.
3. **Typed I/O.** Functions return plain dicts matching the API contract in
   `docs/modules.md` (`tile_url`/`grid`, `legend`, `stats`, `source`).

## Layout

| Module | Responsibility |
|--------|----------------|
| `gee.py` | Auth/init, `is_live()`, status, lazy `ee` import |
| `aoi.py` | Parse/validate AOI, area, centroid, → `ee.Geometry` |
| `indices.py` | Spectral indices (NDVI, etc.) |
| `demo.py` | Deterministic synthetic layers/grids for offline mode |
| `tiles.py` | `ee.Image` → tile URL, legend builders |
| `flood.py` | Susceptibility, SAR extent, road risk |
| `climate.py` | NEX-GDDP-CMIP6 projections & anomalies |
| `drought.py` | SPI, NDVI/VCI anomaly |
| `infra.py` | Exposure overlays |
| `datasets.py` | Dataset catalog + licenses |

## Quick use

```python
from terrashield_geo import gee, flood
gee.init()                       # demo mode unless TERRASHIELD_GEE_PROJECT set
res = flood.susceptibility({"type": "bbox", "bbox": [73.9, 17.6, 74.3, 18.0]})
print(res["source"], res["stats"])
```
