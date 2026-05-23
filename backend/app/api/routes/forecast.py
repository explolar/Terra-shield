"""WeatherCast endpoints — short-range weather/rainfall forecast (Open-Meteo)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from terrashield_geo import aoi as aoi_mod

from ...core.cache import cached
from ...schemas.modules import ForecastRequest
from ...services import weather
from ..deps import rate_limit

router = APIRouter(prefix="/weather", tags=["WeatherCast"], dependencies=[Depends(rate_limit)])


@router.post("/forecast")
def forecast(req: ForecastRequest):
    try:
        norm = aoi_mod.normalize(req.aoi.to_engine())
    except aoi_mod.AOIError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    lon, lat = norm["centroid"]
    payload = {"lat": lat, "lon": lon, "days": req.days}
    try:
        return cached("weather.forecast", payload, lambda: weather.forecast(lat, lon, req.days))
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Weather provider unavailable: {type(exc).__name__}",
        ) from exc
