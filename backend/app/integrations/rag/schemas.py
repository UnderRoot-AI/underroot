from pydantic import BaseModel

class RetrievedSource(BaseModel):
    source: str
    text: str
