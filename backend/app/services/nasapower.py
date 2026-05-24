"""NASA POWER — keyless agro-climatology for a point.

power.larc.nasa.gov: long-term monthly + annual climatology of temperature,
precipitation, humidity, wind and solar radiation (agroclimate community). No key.
"""
from __future__ import annotations

import logging

import httpx

log = logging.getLogger("terrashield.nasapower")

POWER_URL = "https://power.larc.nasa.gov/api/temporal/climatology/point"
PARAMS = ["T2M", "PRECTOTCORR", "RH2M", "WS2M", "ALLSKY_SFC_SW_DWN"]
_MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
           "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def _clean(v):
    # POWER uses -999 as the fill/missing value.
    return None if v is None or v <= -900 else round(float(v), 2)


def agroclimate(lat: float, lon: float) -> dict:
    """Long-term agro-climatology at (lat, lon). Raises on network/API failure."""
    params = {
        "parameters": ",".join(PARAMS),
        "community": "AG",
        "longitude": round(float(lon), 4),
        "latitude": round(float(lat), 4),
        "format": "JSON",
    }
    with httpx.Client(timeout=20) as client:
        resp = client.get(POWER_URL, params=params)
        resp.raise_for_status()
        p = resp.json()["properties"]["parameter"]

    def ann(key: str):
        return _clean(p.get(key, {}).get("ANN"))

    def series(key: str):
        return [{"month": m, "value": _clean(p.get(key, {}).get(m))} for m in _MONTHS]

    def to_kwh(v):  # POWER reports shortwave irradiance in MJ/m²/day
        return round(v / 3.6, 2) if v is not None else None

    precip_day = ann("PRECTOTCORR")
    solar_monthly = [{"month": m["month"], "value": to_kwh(m["value"])}
                     for m in series("ALLSKY_SFC_SW_DWN")]
    return {
        "module": "weather",
        "product": "agroclimate",
        "source": "live",
        "provider": "nasa-power",
        "latitude": params["latitude"],
        "longitude": params["longitude"],
        "summary": {
            "temp_c": ann("T2M"),
            "precip_mm_day": precip_day,
            "precip_mm_year": round(precip_day * 365.25) if precip_day is not None else None,
            "humidity_pct": ann("RH2M"),
            "wind_ms": ann("WS2M"),
            "solar_kwh_m2_day": to_kwh(ann("ALLSKY_SFC_SW_DWN")),
        },
        "monthly": {
            "temp_c": series("T2M"),
            "precip_mm_day": series("PRECTOTCORR"),
            "solar_kwh_m2_day": solar_monthly,
        },
    }
