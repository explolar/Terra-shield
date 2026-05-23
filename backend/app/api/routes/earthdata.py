"""EarthData Engine endpoints — GEE status, AOI validation, dataset catalog."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from terrashield_geo import aoi as aoi_mod
from terrashield_geo import datasets, gee

from ...schemas.common import AOI

router = APIRouter(prefix="/earthdata", tags=["EarthData Engine"])


@router.get("/status")
def status() -> dict:
    """Earth Engine init status: live vs demo, project, availability."""
    return gee.status()


@router.post("/aoi/validate")
def validate_aoi(aoi: AOI) -> dict:
    try:
        return aoi_mod.normalize(aoi.to_engine())
    except aoi_mod.AOIError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/datasets")
def dataset_catalog() -> dict:
    return {"datasets": datasets.catalog()}


@router.get("/basemaps")
def basemaps() -> dict:
    return {
        "basemaps": [
            {"id": "osm", "name": "OpenStreetMap",
             "url": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
             "attribution": "© OpenStreetMap contributors"},
            {"id": "carto-dark", "name": "Carto Dark",
             "url": "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
             "attribution": "© OpenStreetMap, © CARTO"},
            {"id": "esri-imagery", "name": "Esri Satellite",
             "url": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
             "attribution": "© Esri"},
        ]
    }
