"""ClimateLens endpoints — CMIP6/SSP projections."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from terrashield_geo import aoi as aoi_mod
from terrashield_geo import climate

from ...core.cache import cached
from ...schemas.common import LayerResponse
from ...schemas.modules import ExtremesRequest, ProjectionRequest
from ..deps import rate_limit

router = APIRouter(prefix="/climate", tags=["ClimateLens"], dependencies=[Depends(rate_limit)])


@router.get("/scenarios")
def scenarios() -> dict:
    return climate.scenarios()


@router.post("/extremes")
def extremes(req: ExtremesRequest):
    payload = req.model_dump()
    try:
        return cached(
            "climate.extremes", payload,
            lambda: climate.extremes(req.aoi.to_engine(), req.scenario, req.horizon, req.model),
        )
    except aoi_mod.AOIError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/projection", response_model=LayerResponse)
def projection(req: ProjectionRequest):
    payload = req.model_dump()
    try:
        return cached(
            "climate.projection", payload,
            lambda: climate.projection(req.aoi.to_engine(), req.scenario, req.variable,
                                       req.horizon, req.model),
        )
    except aoi_mod.AOIError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/anomaly", response_model=LayerResponse)
def anomaly(req: ProjectionRequest):
    payload = {**req.model_dump(), "kind": "anomaly"}
    try:
        return cached(
            "climate.anomaly", payload,
            lambda: climate.anomaly(req.aoi.to_engine(), req.scenario, req.variable, req.horizon),
        )
    except aoi_mod.AOIError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
