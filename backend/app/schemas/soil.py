from pydantic import BaseModel, ConfigDict
from datetime import datetime

class SoilParameters(BaseModel):
    ph: float | None = None
    nitrogen: float | None = None
    phosphorus: float | None = None
    potassium: float | None = None
    ec: float | None = None
    moisture: float | None = None
    temperature: float | None = None
    organic_carbon: float | None = None

class SoilTestCreate(BaseModel):
    field_id: int | None = None
    location: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    parameters: SoilParameters
    notes: str | None = None

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
