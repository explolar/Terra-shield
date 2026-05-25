"""TerraShield AI backend — FastAPI app factory."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from terrashield_geo import gee

from .core.config import get_settings
from .core.logging import RequestContextMiddleware, configure_logging
from .api.routes import (
    climate,
    copilot,
    drought,
    earthdata,
    flood,
    forecast,
    groundwater,
    health,
    infra,
    landslide,
    optimize,
)

log = logging.getLogger("terrashield")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level, json_logs=settings.is_prod)
    # force=True so the configured project always applies, even if some import-time
    # code triggered a lazy demo-init before startup.
    mode = gee.init(settings.gee_project, settings.gee_sa_key, force=True)
    log.info("TerraShield backend starting — env=%s, EarthData Engine=%s", settings.env, mode)
    yield
    log.info("TerraShield backend shutting down")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="TerraShield AI",
        description="The AI Operating System for Climate Risk & Resilience.",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        openapi_tags=[
            {"name": "FloodAI", "description": "Flood susceptibility, SAR extent, road risk."},
            {"name": "ClimateLens", "description": "CMIP6/SSP future-climate projections."},
            {"name": "DroughtAI", "description": "SPI and vegetation-stress drought analytics."},
            {"name": "InfraRisk", "description": "Infrastructure & population exposure."},
            {"name": "ResilienceOR", "description": "Operations research: AHP, TOPSIS, shelter siting, evacuation routing, mitigation."},
            {"name": "WeatherCast", "description": "Short-range weather & rainfall forecast (Open-Meteo)."},
            {"name": "GroundwaterAI", "description": "GRACE terrestrial water storage & groundwater depletion."},
            {"name": "GeoCopilot", "description": "Natural-language climate-risk assistant (Llama)."},
            {"name": "EarthData Engine", "description": "GEE status, AOI, datasets."},
            {"name": "system", "description": "Health & introspection."},
        ],
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_list,
        # Always allow TerraShield's own Cloud Run frontend, regardless of the
        # CORS_ORIGINS env var — so a deploy that blanks it can't take the app
        # "offline". Matches any terrashield-frontend-*.run.app origin.
        allow_origin_regex=r"https://terrashield-frontend-[\w.-]+\.run\.app",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestContextMiddleware)

    prefix = settings.api_prefix
    for module in (health, earthdata, flood, climate, drought, infra, optimize,
                   forecast, groundwater, landslide, copilot):
        app.include_router(module.router, prefix=prefix)

    @app.get("/", tags=["system"])
    def root() -> dict:
        return {
            "name": "TerraShield AI",
            "tagline": "The AI Operating System for Climate Risk & Resilience",
            "docs": "/docs",
            "api": prefix,
            "modules": ["flood", "climate", "drought", "infra", "optimize",
                        "weather", "groundwater", "copilot", "earthdata"],
            "earthdata_engine": gee.mode(),
        }

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        return JSONResponse(
            status_code=422,
            content={"error": "invalid_request", "detail": str(exc),
                     "hint": "Check the AOI and parameters."},
        )

    return app


app = create_app()
