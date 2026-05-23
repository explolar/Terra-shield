"""Build TerraShield geo assets from the India shapefiles.

Reads the India state/district shapefiles, copies the raw data into the repo,
and emits:
  * simplified GeoJSON boundaries for the map (states + districts)
  * a national gazetteer (place name -> bbox) so GeoCopilot can resolve any
    Indian state/district by name
  * state presets (name, bbox, centroid) for the frontend AOI chips

Run:  python scripts/build_geo_assets.py  [SOURCE_DIR]
Idempotent; safe to re-run.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import geopandas as gpd

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SRC = Path(r"C:\Users\ankit\Downloads\India Shapefile With Kashmir (1)\India_Shape")

RAW_DST = ROOT / "data" / "india_shape"
FE_GEO = ROOT / "frontend" / "public" / "geo"
GE_DATA = ROOT / "geo-engine" / "terrashield_geo" / "data"


def _load(src: Path, rel: str) -> gpd.GeoDataFrame:
    g = gpd.read_file(src / rel)
    if g.crs is None:
        g = g.set_crs(4326)  # India shapefiles are lon/lat
    return g.to_crs(4326)


def _bbox(geom) -> list[float]:
    return [round(v, 4) for v in geom.bounds]


def main(src: Path) -> None:
    for d in (RAW_DST, FE_GEO, GE_DATA):
        d.mkdir(parents=True, exist_ok=True)

    states = _load(src, "India_state/india_st.shp")
    districts = _load(src, "india_ds/india_ds.shp")

    # 1) Copy raw shapefile components into the repo (provenance).
    for sub in ("India_state", "india_ds"):
        for f in (src / sub).glob("*"):
            if f.suffix.lower() in {".shp", ".shx", ".dbf", ".prj"}:
                shutil.copy2(f, RAW_DST / f.name)

    # 2) Simplified GeoJSON boundaries for the map.
    states_simp = states.copy()
    states_simp["geometry"] = states_simp.geometry.simplify(0.01, preserve_topology=True)
    states_simp.to_file(FE_GEO / "india_states.geojson", driver="GeoJSON")

    districts_simp = districts.copy()
    districts_simp["geometry"] = districts_simp.geometry.simplify(0.008, preserve_topology=True)
    districts_simp.to_file(FE_GEO / "india_districts.geojson", driver="GeoJSON")

    # National outline (dissolve all states) — a clean single boundary for the map.
    outline = states.dissolve()
    outline["geometry"] = outline.geometry.simplify(0.02, preserve_topology=True)
    outline[["geometry"]].to_file(FE_GEO / "india_outline.geojson", driver="GeoJSON")

    # 3) Gazetteer: name -> bbox (districts first = more specific, then states).
    gazetteer: dict[str, dict] = {}
    for _, row in districts.iterrows():
        name = str(row["DISTRICT"]).strip().lower()
        if name and name not in gazetteer:
            gazetteer[name] = {"bbox": _bbox(row.geometry), "state": str(row["STATE"]).title(),
                               "level": "district"}
    for _, row in states.iterrows():
        name = str(row["STATE"]).strip().lower()
        gazetteer.setdefault(name, {"bbox": _bbox(row.geometry), "level": "state"})

    (GE_DATA / "india_gazetteer.json").write_text(
        json.dumps(gazetteer, ensure_ascii=False), encoding="utf-8")

    # 4) State presets for frontend AOI chips.
    presets = []
    for _, row in states.iterrows():
        b = _bbox(row.geometry)
        presets.append({
            "name": str(row["STATE"]).title(),
            "bbox": b,
            "centroid": [round((b[0] + b[2]) / 2, 4), round((b[1] + b[3]) / 2, 4)],
        })
    presets.sort(key=lambda p: p["name"])
    (FE_GEO / "india_states_presets.json").write_text(
        json.dumps(presets, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"states={len(states)} districts={len(districts)} gazetteer={len(gazetteer)}")
    print(f"GeoJSON -> {FE_GEO}")
    print(f"gazetteer -> {GE_DATA / 'india_gazetteer.json'}")


if __name__ == "__main__":
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SRC
    main(src)
