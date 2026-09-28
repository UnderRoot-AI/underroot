from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    soil_test_id: int | None = None

class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = []
