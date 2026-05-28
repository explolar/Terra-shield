"""ResilienceOR endpoints — operations-research decision support.

These turn hazard layers into decisions: defensible weights (AHP), district
ranking (TOPSIS), relief-shelter siting (MCLP), evacuation routing (Dijkstra),
and budget-constrained mitigation (knapsack).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from terrashield_geo import aoi as aoi_mod
from terrashield_geo import optimize

from ...core.cache import cached
from ...schemas.modules import (
    AhpRequest,
    EvacuationRequest,
    MitigationRequest,
    ShelterRequest,
    TopsisRequest,
)
from ..deps import rate_limit

router = APIRouter(prefix="/optimize", tags=["ResilienceOR"], dependencies=[Depends(rate_limit)])


@router.get("/ahp/default")
def ahp_default() -> dict:
    """Default flood-factor weights derived via AHP (with consistency ratio)."""
    return optimize.default_flood_ahp()


@router.post("/ahp")
def ahp(req: AhpRequest) -> dict:
    try:
        return optimize.ahp_weights(req.matrix, req.labels)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/topsis")
def topsis(req: TopsisRequest) -> dict:
    try:
        return optimize.topsis(req.alternatives, req.matrix, req.weights, req.benefit)
    except (ValueError, IndexError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/shelters")
def shelters(req: ShelterRequest) -> dict:
    payload = {"aoi": req.aoi.to_engine(), "p": req.num_shelters, "r": req.radius_km}
    try:
        return cached(
            "optimize.shelters", payload,
            lambda: optimize.shelters_for_aoi(req.aoi.to_engine(), req.num_shelters, req.radius_km),
        )
    except aoi_mod.AOIError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/evacuation")
def evacuation(req: EvacuationRequest) -> dict:
    payload = {"aoi": req.aoi.to_engine()}
    try:
        return cached(
            "optimize.evacuation", payload,
            lambda: optimize.evacuation_for_aoi(req.aoi.to_engine()),
        )
    except aoi_mod.AOIError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/mitigation")
def mitigation(req: MitigationRequest) -> dict:
    if req.interventions:
        items = [optimize.Intervention(i.id, i.cost, i.risk_reduction, i.effectiveness)
                 for i in req.interventions]
    else:
        items = optimize.DEFAULT_INTERVENTIONS
    # With an AOI, ground risk-reduction in the real flood-exposed population;
    # otherwise solve the abstract budget-constrained knapsack.
    if req.aoi is not None:
        payload = {"aoi": req.aoi.to_engine(), "budget": req.budget, "n": len(items)}
        return cached(
            "optimize.mitigation", payload,
            lambda: optimize.mitigation_for_aoi(req.aoi.to_engine(), req.budget, items),
        )
    return optimize.mitigation_plan(items, req.budget)
