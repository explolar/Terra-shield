"""LandslideAI endpoints — ML landslide-susceptibility (F1/AUC, not AHP)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from terrashield_geo import aoi as aoi_mod
from terrashield_geo import landslide

from ...core.cache import cached
from ...schemas.modules import LandslideRequest
from ..deps import rate_limit

router = APIRouter(prefix="/landslide", tags=["LandslideAI"], dependencies=[Depends(rate_limit)])


@router.post("/susceptibility")
def landslide_susceptibility(req: LandslideRequest):
    try:
        aoi = req.aoi.to_engine()
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    payload = {"aoi": aoi, "model": req.model, "inventory": req.inventory_asset}
    return cached(
        "landslide.susceptibility", payload,
        lambda: landslide.susceptibility(aoi, req.model, req.inventory_asset),
    )
