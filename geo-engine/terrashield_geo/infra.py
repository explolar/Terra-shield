"""InfraRisk compute — infrastructure & population exposure to hazards.

v1 computes exposure overlays: how much road network, built-up area and
population fall within a hazard footprint. Routing-based access loss is on the
roadmap. Live path uses ESA WorldCover + WorldPop; demo path is deterministic.
"""
from __future__ import annotations

import logging
from typing import Any

from . import aoi as aoi_mod
from . import demo, gee

log = logging.getLogger("terrashield.geo.infra")


def exposure(aoi: dict[str, Any], hazard: str = "flood") -> dict[str, Any]:
    norm = aoi_mod.normalize(aoi)
    if gee.is_live():
        try:
            return _exposure_live(norm, hazard)
        except Exception as exc:  # pragma: no cover
            log.warning("infra.exposure live failed, demo fallback: %s", exc)
    return _exposure_demo(norm, hazard)


def _exposure_demo(norm, hazard) -> dict[str, Any]:
    import numpy as np

    bbox = norm["bbox"]
    hazard_field = demo.smooth_field(bbox, 22, salt=f"infra:hazard:{hazard}", sharpness=1.6)
    builtup_field = demo.smooth_field(bbox, 22, salt="infra:builtup")
    pop_density = demo.smooth_field(bbox, 22, salt="infra:pop")

    exposed_mask = hazard_field > 0.55
    area = norm["area_km2"]
    # Synthesize totals scaled to AOI area for plausibility.
    total_pop = int(area * np.interp(float(pop_density.mean()), [0, 1], [200, 4000]))
    exposed_pop = int(total_pop * float((exposed_mask * pop_density).sum() / max(pop_density.sum(), 1e-6)))
    total_built_km2 = round(area * float(builtup_field.mean()) * 0.3, 2)
    exposed_built_km2 = round(total_built_km2 * float(exposed_mask.mean()), 2)

    grid = demo.field_to_grid(bbox, (hazard_field * builtup_field).round(3), value_key="exposure")
    return {
        "module": "infra",
        "product": "exposure",
        "source": "demo",
        "hazard": hazard,
        "tile_url": None,
        "grid": grid,
        "legend": [
            {"label": "High exposure", "color": "#67000d"},
            {"label": "Moderate", "color": "#fb6a4a"},
            {"label": "Low", "color": "#fee5d9"},
        ],
        "stats": {
            "population_total": total_pop,
            "population_exposed": exposed_pop,
            "population_exposed_pct": round(exposed_pop / max(total_pop, 1) * 100, 1),
            "builtup_km2": total_built_km2,
            "builtup_exposed_km2": exposed_built_km2,
            "area_km2": area,
        },
        "aoi": {"bbox": bbox, "centroid": norm["centroid"]},
    }


def _exposure_live(norm, hazard) -> dict[str, Any]:  # pragma: no cover
    ee = gee.get_ee()
    geom = aoi_mod.to_ee_geometry(norm)

    pop = ee.ImageCollection("WorldPop/GP/100m/pop").filter(
        ee.Filter.eq("year", 2020)
    ).mosaic().clip(geom)
    builtup = ee.Image("ESA/WorldCover/v200/2021").select("Map").eq(50).clip(geom)

    # Hazard footprint: reuse flood susceptibility as a proxy here.
    from . import flood
    sus = flood._susceptibility_live(  # noqa: SLF001 (internal reuse)
        norm, flood._normalize_weights(None), 1.0, "normal"
    )
    # The live susceptibility returns tiles, not an image; recompute a threshold mask.
    dem = ee.Image("USGS/SRTMGL1_003").clip(geom)
    hazard_mask = dem.lt(dem.reduceRegion(ee.Reducer.percentile([30]), geom, 90,
                                          maxPixels=1e9, bestEffort=True).values().get(0))

    total_pop = ee.Number(pop.reduceRegion(ee.Reducer.sum(), geom, 100,
                                           maxPixels=1e9, bestEffort=True).values().get(0))
    exposed_pop = ee.Number(
        pop.updateMask(hazard_mask).reduceRegion(ee.Reducer.sum(), geom, 100,
                                                 maxPixels=1e9, bestEffort=True).values().get(0)
    )
    return {
        "module": "infra",
        "product": "exposure",
        "source": "live",
        "hazard": hazard,
        "tile_url": None,
        "grid": None,
        "legend": [{"label": "Exposed", "color": "#67000d"}],
        "stats": {
            "population_total": int(total_pop.getInfo() or 0),
            "population_exposed": int(exposed_pop.getInfo() or 0),
            "area_km2": norm["area_km2"],
        },
        "aoi": {"bbox": norm["bbox"], "centroid": norm["centroid"]},
    }
