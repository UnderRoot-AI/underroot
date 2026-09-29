from pydantic import BaseModel, field_validator, model_validator, ConfigDict
from datetime import datetime
import math


# ── Physiologically realistic parameter bounds ──────────────────────────────
# Units: N/P/K in kg/ha (matches frontend constants/soilParameters.ts)
_BOUNDS: dict[str, tuple[float, float]] = {
    "ph":             (0.0,  14.0),
    "nitrogen":       (0.0, 1000.0),  # kg/ha
    "phosphorus":     (0.0,  500.0),  # kg/ha
    "potassium":      (0.0, 2000.0),  # kg/ha
    "ec":             (0.0,   30.0),  # dS/m
    "moisture":       (0.0,  100.0),  # %
    "temperature":    (-30.0, 80.0),  # °C
    "organic_carbon": (0.0,   20.0),  # %
}


class SoilParameters(BaseModel):
    ph: float | None = None
    nitrogen: float | None = None
    phosphorus: float | None = None
    potassium: float | None = None
    ec: float | None = None
    moisture: float | None = None
    temperature: float | None = None
    organic_carbon: float | None = None

    @model_validator(mode="after")
    def validate_all_params(self):
        errors: list[str] = []
        for field, (lo, hi) in _BOUNDS.items():
            val = getattr(self, field)
            if val is None:
                continue
            if math.isnan(val) or math.isinf(val):
                errors.append(f"{field}: must be a finite number")
                continue
            if not (lo <= val <= hi):
                errors.append(f"{field}: {val} is outside the valid range [{lo}, {hi}]")
        if errors:
            raise ValueError("; ".join(errors))
        return self

    @model_validator(mode="after")
    def at_least_one_param(self):
        """Require at least one soil parameter for a useful test."""
        values = [self.ph, self.nitrogen, self.phosphorus, self.potassium,
                  self.ec, self.moisture, self.temperature, self.organic_carbon]
        if all(v is None for v in values):
            raise ValueError("At least one soil parameter is required")
        return self


class SoilTestCreate(BaseModel):
    field_id: int | None = None
    location: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    parameters: SoilParameters
    notes: str | None = None

    @field_validator("location")
    @classmethod
    def trim_location(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            return v if v else None
        return v


class SoilTestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    field_id: int | None = None
    location: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    created_at: datetime
    parameters: SoilParameters
    health_score: float
    health_status: str
    notes: str | None = None
    source: str | None = None
    device_id: str | None = None
