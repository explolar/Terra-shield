"""DroughtAI endpoints — SPI and vegetation stress."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from terrashield_geo import aoi as aoi_mod
from terrashield_geo import drought

from ...core.cache import cached
from ...schemas.common import LayerResponse
from ...schemas.modules import SpiRequest, VegetationRequest
from ..deps import rate_limit

router = APIRouter(prefix="/drought", tags=["DroughtAI"], dependencies=[Depends(rate_limit)])


@router.post("/spi", response_model=LayerResponse)
def spi(req: SpiRequest):
    payload = req.model_dump()
    try:
        return cached(
            "drought.spi", payload,
            lambda: drought.spi(req.aoi.to_engine(), req.scale_months),
        )
    except aoi_mod.AOIError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/vegetation", response_model=LayerResponse)
def vegetation(req: VegetationRequest):
    payload = req.model_dump()
    try:
        return cached(
            "drought.vegetation", payload,
            lambda: drought.vegetation(req.aoi.to_engine()),
        )
    except aoi_mod.AOIError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
