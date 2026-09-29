"""
Pydantic schemas for device registration and hardware measurement ingestion.

MeasurementValue supports an extensible {value, unit} format, allowing any
parameter (pH, N, P, K, EC, sulphur, boron, etc.) to be ingested without
a fixed enum of allowed fields.
"""
from __future__ import annotations
import math
from datetime import datetime
from typing import Any
from pydantic import BaseModel, field_validator, model_validator, ConfigDict

# ── Allowed connection types ──────────────────────────────────────────────────
CONNECTION_TYPES = {"http", "mqtt", "ble", "modbus", "lorawan", "manual", "generic"}

# ── Core parameters that can be validated against known bounds ────────────────
# Keys must match SoilTest column names.  Only these will be mapped to SoilTest.
_CORE_BOUNDS: dict[str, tuple[float, float]] = {
    "ph":             (0.0,   14.0),
    "nitrogen":       (0.0, 1000.0),
    "phosphorus":     (0.0,  500.0),
    "potassium":      (0.0, 2000.0),
    "ec":             (0.0,   30.0),
    "moisture":       (0.0,  100.0),
    "temperature":   (-30.0,  80.0),
    "organic_carbon": (0.0,   20.0),
}

CORE_PARAMS = set(_CORE_BOUNDS.keys())


# ── Per-measurement value ─────────────────────────────────────────────────────
class MeasurementValue(BaseModel):
    value: float
    unit: str = ""

    @field_validator("value")
    @classmethod
    def no_nan_inf(cls, v: float) -> float:
        if math.isnan(v) or math.isinf(v):
            raise ValueError("value must be a finite number (NaN and Infinity not allowed)")
        return v


# ── Ingestion payload ─────────────────────────────────────────────────────────
class ReadingIngest(BaseModel):
    """Payload sent to POST /api/devices/{device_id}/readings."""
    timestamp: datetime | None = None
    measurements: dict[str, MeasurementValue]

    @model_validator(mode="after")
    def at_least_one(self) -> "ReadingIngest":
        if not self.measurements:
            raise ValueError("measurements must contain at least one parameter")
        return self

    @model_validator(mode="after")
    def validate_core_bounds(self) -> "ReadingIngest":
        errors: list[str] = []
        for key, mv in self.measurements.items():
            if key in _CORE_BOUNDS:
                lo, hi = _CORE_BOUNDS[key]
                if not (lo <= mv.value <= hi):
                    errors.append(f"{key}: {mv.value} is outside the valid range [{lo}, {hi}]")
        if errors:
            raise ValueError("; ".join(errors))
        return self


# ── Device schemas ────────────────────────────────────────────────────────────
class DeviceCreate(BaseModel):
    device_id: str
    manufacturer: str | None = None
    model: str | None = None
    name: str = "My Soil Device"
    connection_type: str = "generic"

    @field_validator("connection_type")
    @classmethod
    def valid_connection_type(cls, v: str) -> str:
        if v not in CONNECTION_TYPES:
            raise ValueError(f"connection_type must be one of: {', '.join(sorted(CONNECTION_TYPES))}")
        return v

    @field_validator("device_id")
    @classmethod
    def non_empty_device_id(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("device_id must not be empty")
        return v


class DeviceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    device_id: str
    manufacturer: str | None = None
    model: str | None = None
    name: str
    connection_type: str
    status: str
    is_active: bool
    last_seen_at: datetime | None = None
    created_at: datetime


class ReadingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    device_id: int
    user_id: int
    reading_timestamp: datetime | None = None
    source: str
    manufacturer: str | None = None
    model: str | None = None
    measurements: dict
    soil_test_id: int | None = None
    created_at: datetime
