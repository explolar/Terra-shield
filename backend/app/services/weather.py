"""WeatherCast — short-range weather & rainfall forecast via Open-Meteo.

Open-Meteo (https://open-meteo.com) is a free, key-less weather API. We use it for
a 1-16 day forecast at the AOI centroid: daily precipitation, rain probability,
temperature and wind — plus a flood-relevant heavy-rain watch. Complements the
CMIP6 long-range projections in ClimateLens with an actionable nowcast.
"""
from __future__ import annotations

import logging

import httpx

log = logging.getLogger("terrashield.weather")

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
HEAVY_RAIN_MM = 50.0   # IMD "heavy rainfall" daily threshold
VERY_HEAVY_MM = 115.0  # IMD "very heavy rainfall"


def forecast(lat: float, lon: float, days: int = 7) -> dict:
    """Daily forecast at (lat, lon). Raises on network/API failure (no demo data)."""
    days = max(1, min(16, int(days)))
    params = {
        "latitude": round(float(lat), 4),
        "longitude": round(float(lon), 4),
        "daily": ",".join([
            "precipitation_sum", "precipitation_probability_max",
            "temperature_2m_max", "temperature_2m_min", "wind_speed_10m_max",
        ]),
        "forecast_days": days,
        "timezone": "auto",
    }
    with httpx.Client(timeout=15) as client:
        resp = client.get(OPEN_METEO_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    d = data.get("daily", {})
    dates = d.get("time", [])
    precip = d.get("precipitation_sum", [])
    prob = d.get("precipitation_probability_max", [])
    tmax = d.get("temperature_2m_max", [])
    tmin = d.get("temperature_2m_min", [])
    wind = d.get("wind_speed_10m_max", [])

    daily = []
    for i, day in enumerate(dates):
        daily.append({
            "date": day,
            "precip_mm": _g(precip, i),
            "precip_prob": _g(prob, i),
            "tmax_c": _g(tmax, i),
            "tmin_c": _g(tmin, i),
            "wind_kmh": _g(wind, i),
        })

    total_precip = round(sum(p for p in precip if p is not None), 1)
    heavy_days = sum(1 for p in precip if p and p >= HEAVY_RAIN_MM)
    peak = max(daily, key=lambda x: x["precip_mm"] or 0) if daily else None
    watch = "very heavy rain" if any((p or 0) >= VERY_HEAVY_MM for p in precip) \
        else "heavy rain" if heavy_days else "no heavy rain"

    return {
        "module": "weather",
        "product": "forecast",
        "source": "live",
        "provider": "open-meteo",
        "latitude": params["latitude"],
        "longitude": params["longitude"],
        "days": days,
        "daily": daily,
        "summary": {
            "total_precip_mm": total_precip,
            "heavy_rain_days": heavy_days,
            "peak_precip_mm": (peak["precip_mm"] if peak else 0),
            "peak_date": (peak["date"] if peak else None),
            "flood_watch": watch,
        },
    }


def _g(arr, i):
    return arr[i] if i < len(arr) and arr[i] is not None else None
