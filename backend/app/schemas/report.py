from pydantic import BaseModel
from datetime import datetime

class ReportGenerate(BaseModel):
    soil_test_id: int

class ReportOut(BaseModel):
    id: int
    soil_test_id: int | None = None
    file_name: str | None = None
    file_url: str | None = None
    status: str
    extracted_text: str | None = None
    extracted_parameters: dict | None = None
    created_at: datetime

class ReportVerify(BaseModel):
    parameters: dict[str, float | None]
    location: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    notes: str | None = None
