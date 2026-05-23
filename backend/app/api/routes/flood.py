"""FloodAI endpoints — susceptibility, SAR extent, road risk."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from terrashield_geo import aoi as aoi_mod
from terrashield_geo import flood, ml_flood

from ...core.cache import cached
from ...schemas.common import LayerResponse
from ...schemas.modules import (
    MlRiskRequest,
    MultiYearRequest,
    RoadRiskRequest,
    SarExtentRequest,
    SusceptibilityRequest,
)
from ..deps import rate_limit

router = APIRouter(prefix="/flood", tags=["FloodAI"], dependencies=[Depends(rate_limit)])


@router.post("/susceptibility", response_model=LayerResponse)
def susceptibility(req: SusceptibilityRequest):
    weights = req.weights.model_dump(exclude_none=True) if req.weights else None
    payload = {"aoi": req.aoi.to_engine(), "weights": weights,
               "rain": req.rainfall_scenario, "ahp": req.ahp_matrix}
    try:
        return cached(
            "flood.susceptibility", payload,
            lambda: flood.susceptibility(req.aoi.to_engine(), weights,
                                         req.rainfall_scenario, req.ahp_matrix),
        )
    except aoi_mod.AOIError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/sar-extent", response_model=LayerResponse)
def sar_extent(req: SarExtentRequest):
    payload = req.model_dump()
    try:
        return cached(
            "flood.sar", payload,
            lambda: flood.sar_extent(req.aoi.to_engine(), req.pre_start, req.pre_end,
                                     req.post_start, req.post_end),
        )
    except aoi_mod.AOIError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/ml-risk")
def ml_risk(req: MlRiskRequest):
    payload = req.model_dump()
    try:
        return cached(
            "flood.ml_risk", payload,
            lambda: ml_flood.flood_risk_ml(req.aoi.to_engine(), req.model),
        )
    except aoi_mod.AOIError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/multiyear")
def multiyear(req: MultiYearRequest):
    payload = req.model_dump()
    try:
        return cached(
            "flood.multiyear", payload,
            lambda: flood.multiyear(req.aoi.to_engine(), req.years),
        )
    except aoi_mod.AOIError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/road-risk", response_model=LayerResponse)
def road_risk(req: RoadRiskRequest):
    payload = {"aoi": req.aoi.to_engine(), "thr": req.depth_threshold}
    try:
        return cached(
            "flood.road", payload,
            lambda: flood.road_risk(req.aoi.to_engine(), req.depth_threshold),
        )
    except aoi_mod.AOIError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
