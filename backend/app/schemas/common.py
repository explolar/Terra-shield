"""Shared request/response schemas."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AOI(BaseModel):
    """Area of interest — a bbox or a GeoJSON polygon."""

    type: Literal["bbox", "geojson"] = "bbox"
    bbox: list[float] | None = Field(
        default=None,
        description="[minLon, minLat, maxLon, maxLat]",
        examples=[[73.9, 17.6, 74.3, 18.0]],
    )
    geojson: dict[str, Any] | None = Field(default=None, description="GeoJSON Polygon")

    @model_validator(mode="after")
    def _check(self) -> "AOI":
        if self.type == "bbox" and not self.bbox:
            raise ValueError("bbox AOI requires a 'bbox' of 4 numbers")
        if self.type == "geojson" and not self.geojson:
            raise ValueError("geojson AOI requires a 'geojson' object")
        return self

    def to_engine(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True)


class LegendItem(BaseModel):
    model_config = ConfigDict(extra="allow")
    label: str
    color: str
    min: float | None = None
    max: float | None = None


class LayerResponse(BaseModel):
    """Generic layer response. Extra module-specific keys are preserved."""

    model_config = ConfigDict(extra="allow")

    module: str
    product: str
    source: Literal["live", "demo"]
    tile_url: str | None = None
    grid: dict[str, Any] | None = Field(default=None, description="GeoJSON FeatureCollection (demo)")
    legend: list[LegendItem] = []
    stats: dict[str, Any] = {}
    aoi: dict[str, Any] = {}


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
    hint: str | None = None
