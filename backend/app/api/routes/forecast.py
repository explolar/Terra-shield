"""WeatherCast endpoints — short-range weather/rainfall forecast (Open-Meteo)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from terrashield_geo import aoi as aoi_mod

from ...core.cache import cached
from ...schemas.modules import AgroclimateRequest, ForecastRequest, UsForecastRequest
from ...services import nasapower, noaa, weather
from ..deps import rate_limit

router = APIRouter(prefix="/weather", tags=["WeatherCast"], dependencies=[Depends(rate_limit)])


def _centroid(aoi):
    try:
        norm = aoi_mod.normalize(aoi.to_engine())
    except aoi_mod.AOIError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    lon, lat = norm["centroid"]
    return lat, lon


@router.post("/forecast")
def forecast(req: ForecastRequest):
    lat, lon = _centroid(req.aoi)
    payload = {"lat": lat, "lon": lon, "days": req.days}
    try:
        return cached("weather.forecast", payload, lambda: weather.forecast(lat, lon, req.days))
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Weather provider unavailable: {type(exc).__name__}",
        ) from exc


@router.post("/agroclimate")
def agroclimate(req: AgroclimateRequest):
    """NASA POWER long-term agro-climatology (temp/precip/humidity/wind/solar)."""
    lat, lon = _centroid(req.aoi)
    try:
        return cached("weather.agroclimate", {"lat": lat, "lon": lon},
                      lambda: nasapower.agroclimate(lat, lon))
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"NASA POWER unavailable: {type(exc).__name__}",
        ) from exc


@router.post("/us-forecast")
def us_forecast(req: UsForecastRequest):
    """NOAA / NWS forecast (United States only; clean message elsewhere)."""
    lat, lon = _centroid(req.aoi)
    try:
        return cached("weather.us_forecast", {"lat": lat, "lon": lon},
                      lambda: noaa.us_forecast(lat, lon))
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"NOAA/NWS unavailable: {type(exc).__name__}",
        ) from exc
