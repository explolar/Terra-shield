"""GroundwaterAI endpoints — GRACE terrestrial water storage & depletion."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from terrashield_geo import aoi as aoi_mod
from terrashield_geo import groundwater

from ...core.cache import cached
from ...schemas.modules import GroundwaterRequest
from ..deps import rate_limit

router = APIRouter(prefix="/groundwater", tags=["GroundwaterAI"], dependencies=[Depends(rate_limit)])


@router.post("/storage")
def storage(req: GroundwaterRequest):
    payload = req.model_dump()
    try:
        return cached(
            "groundwater.storage", payload,
            lambda: groundwater.groundwater(req.aoi.to_engine()),
        )
    except aoi_mod.AOIError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
