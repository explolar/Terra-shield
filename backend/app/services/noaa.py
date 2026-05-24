"""NOAA / National Weather Service (api.weather.gov) — keyless US forecast.

US-only. The /points endpoint 404s outside US coverage; we surface that cleanly
rather than erroring. NWS requires a descriptive User-Agent header.
"""
from __future__ import annotations

import logging

import httpx

log = logging.getLogger("terrashield.noaa")

POINTS_URL = "https://api.weather.gov/points/{lat},{lon}"
HEADERS = {"User-Agent": "TerraShield climate-risk platform (contact: admin@terrashield)"}


def _unavailable(msg: str) -> dict:
    return {
        "module": "weather",
        "product": "us_forecast",
        "source": "live",
        "provider": "noaa-nws",
        "available": False,
        "message": msg,
    }


def us_forecast(lat: float, lon: float) -> dict:
    """NWS multi-period forecast at (lat, lon). US-only; raises on network failure."""
    with httpx.Client(timeout=20, headers=HEADERS, follow_redirects=True) as client:
        pr = client.get(POINTS_URL.format(lat=round(float(lat), 4), lon=round(float(lon), 4)))
        if pr.status_code == 404:
            return _unavailable(
                "NOAA/NWS covers the United States only - this AOI is outside coverage."
            )
        pr.raise_for_status()
        props = pr.json()["properties"]
        fr = client.get(props["forecast"])
        fr.raise_for_status()
        periods = fr.json()["properties"]["periods"][:8]

    loc = (props.get("relativeLocation") or {}).get("properties") or {}
    daily = [
        {
            "name": p.get("name"),
            "temp": p.get("temperature"),
            "unit": p.get("temperatureUnit"),
            "wind": p.get("windSpeed"),
            "precip_prob": (p.get("probabilityOfPrecipitation") or {}).get("value"),
            "short": p.get("shortForecast"),
        }
        for p in periods
    ]
    return {
        "module": "weather",
        "product": "us_forecast",
        "source": "live",
        "provider": "noaa-nws",
        "available": True,
        "location": {"city": loc.get("city"), "state": loc.get("state")},
        "periods": daily,
    }
