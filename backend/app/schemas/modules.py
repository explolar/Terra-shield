"""Per-module request schemas (strict input validation)."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from .common import AOI


# ---- FloodAI -------------------------------------------------------------- #
class FloodWeights(BaseModel):
    """Optional per-factor weights for the 11-factor AHP model (0-1). Any omitted
    factor falls back to the AHP default; weights are renormalized to sum to 1."""

    distance_to_river: float | None = Field(default=None, ge=0, le=1)
    hand: float | None = Field(default=None, ge=0, le=1)
    rainfall: float | None = Field(default=None, ge=0, le=1)
    slope: float | None = Field(default=None, ge=0, le=1)
    elevation: float | None = Field(default=None, ge=0, le=1)
    drainage_density: float | None = Field(default=None, ge=0, le=1)
    twi: float | None = Field(default=None, ge=0, le=1)
    lulc: float | None = Field(default=None, ge=0, le=1)
    soil: float | None = Field(default=None, ge=0, le=1)
    ndvi: float | None = Field(default=None, ge=0, le=1)
    curvature: float | None = Field(default=None, ge=0, le=1)


class SusceptibilityRequest(BaseModel):
    aoi: AOI
    weights: FloodWeights | None = None
    rainfall_scenario: Literal["normal", "wet", "extreme"] = "normal"
    ahp_matrix: list[list[float]] | None = Field(
        default=None,
        description="Optional 6x6 reciprocal pairwise matrix; derives weights via AHP "
        "(order: elevation, slope, twi, drainage, rainfall, landuse).",
    )


class SarExtentRequest(BaseModel):
    aoi: AOI
    pre_start: str = "2023-05-01"
    pre_end: str = "2023-05-31"
    post_start: str = "2023-07-01"
    post_end: str = "2023-07-31"


class RoadRiskRequest(BaseModel):
    aoi: AOI
    depth_threshold: float = Field(default=0.5, ge=0, le=1)


class MultiYearRequest(BaseModel):
    aoi: AOI
    years: list[int] | None = Field(default=None, description="Defaults to 2019-2024")


class MlRiskRequest(BaseModel):
    aoi: AOI
    model: Literal["gbm", "xgboost", "random_forest"] = "gbm"


# ---- ClimateLens ---------------------------------------------------------- #
class ProjectionRequest(BaseModel):
    aoi: AOI
    scenario: Literal["ssp245", "ssp585"] = "ssp585"
    variable: Literal["pr", "tas", "tasmax"] = "pr"
    horizon: Literal["2030s", "2050s", "2080s"] = "2050s"
    model: str = "ensemble"


class ExtremesRequest(BaseModel):
    aoi: AOI
    scenario: Literal["ssp245", "ssp585"] = "ssp585"
    horizon: Literal["2030s", "2050s", "2080s"] = "2050s"
    model: str = "ensemble"


# ---- DroughtAI ------------------------------------------------------------ #
class SpiRequest(BaseModel):
    aoi: AOI
    scale_months: Literal[1, 3, 6, 12] = 3


class VegetationRequest(BaseModel):
    aoi: AOI


# ---- InfraRisk ------------------------------------------------------------ #
class ExposureRequest(BaseModel):
    aoi: AOI
    hazard: Literal["flood", "drought"] = "flood"


class CriticalityRequest(BaseModel):
    aoi: AOI


# ---- GeoCopilot ----------------------------------------------------------- #
class CopilotRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)
    aoi: AOI | None = None


# ---- ResilienceOR (optimization) ----------------------------------------- #
class AhpRequest(BaseModel):
    matrix: list[list[float]] = Field(..., description="Square reciprocal pairwise matrix")
    labels: list[str] | None = None


class TopsisRequest(BaseModel):
    alternatives: list[str]
    matrix: list[list[float]] = Field(..., description="m alternatives x k criteria")
    weights: list[float]
    benefit: list[bool] = Field(..., description="True if larger-is-better per criterion")


class ShelterRequest(BaseModel):
    aoi: AOI
    num_shelters: int = Field(default=3, ge=1, le=20)
    radius_km: float = Field(default=8.0, gt=0, le=100)


class EvacuationRequest(BaseModel):
    aoi: AOI


class InterventionModel(BaseModel):
    id: str
    cost: float = Field(..., gt=0)
    risk_reduction: float = Field(..., ge=0)


class MitigationRequest(BaseModel):
    budget: float = Field(..., gt=0)
    interventions: list[InterventionModel] | None = None
