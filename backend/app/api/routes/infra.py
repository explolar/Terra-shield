"""InfraRisk endpoints — exposure overlays."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from terrashield_geo import aoi as aoi_mod
from terrashield_geo import infra

from ...core.cache import cached
from ...schemas.common import LayerResponse
from ...schemas.modules import ExposureRequest
from ..deps import rate_limit

router = APIRouter(prefix="/infra", tags=["InfraRisk"], dependencies=[Depends(rate_limit)])


@router.post("/exposure", response_model=LayerResponse)
def exposure(req: ExposureRequest):
    payload = req.model_dump()
    try:
        return cached(
            "infra.exposure", payload,
            lambda: infra.exposure(req.aoi.to_engine(), req.hazard),
        )
    except aoi_mod.AOIError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
