"""Catalog of Earth-observation datasets used across TerraShield modules."""
from __future__ import annotations

CATALOG = [
    {
        "id": "USGS/SRTMGL1_003", "name": "SRTM DEM", "module": ["flood", "infra"],
        "var": "elevation, slope", "resolution": "30 m", "license": "Public domain",
    },
    {
        "id": "MERIT/Hydro/v1_0_1", "name": "MERIT Hydro", "module": ["flood"],
        "var": "upstream area, TWI, drainage", "resolution": "90 m", "license": "Open",
    },
    {
        "id": "COPERNICUS/S1_GRD", "name": "Sentinel-1 SAR", "module": ["flood"],
        "var": "VV/VH backscatter (inundation)", "resolution": "10 m", "license": "Copernicus open",
    },
    {
        "id": "COPERNICUS/S2_SR_HARMONIZED", "name": "Sentinel-2 SR", "module": ["drought", "flood"],
        "var": "NDVI, NDWI", "resolution": "10 m", "license": "Copernicus open",
    },
    {
        "id": "UCSB-CHG/CHIRPS/DAILY", "name": "CHIRPS rainfall", "module": ["flood", "drought"],
        "var": "precipitation, SPI", "resolution": "~5 km", "license": "Open (UCSB/USGS)",
    },
    {
        "id": "NASA/GDDP-CMIP6", "name": "NEX-GDDP-CMIP6", "module": ["climate"],
        "var": "pr, tas, tasmax (SSP245/585)", "resolution": "0.25°", "license": "CC-BY-SA 4.0",
    },
    {
        "id": "MODIS/061/MOD13A2", "name": "MODIS NDVI", "module": ["drought"],
        "var": "NDVI / VCI", "resolution": "1 km", "license": "Open (NASA)",
    },
    {
        "id": "ESA/WorldCover/v200/2021", "name": "ESA WorldCover", "module": ["flood", "infra"],
        "var": "land use / land cover", "resolution": "10 m", "license": "CC-BY 4.0",
    },
    {
        "id": "WorldPop/GP/100m/pop", "name": "WorldPop", "module": ["infra"],
        "var": "population count", "resolution": "100 m", "license": "CC-BY 4.0",
    },
    {
        "id": "JRC/GSW1_4/GlobalSurfaceWater", "name": "JRC Global Surface Water",
        "module": ["flood"], "var": "water occurrence", "resolution": "30 m", "license": "Open (EC JRC)",
    },
]


def catalog() -> list[dict]:
    return CATALOG
