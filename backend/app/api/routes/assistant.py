from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.conversation import Conversation
from app.models.soil_test import SoilTest
from app.schemas.assistant import ChatRequest, ChatResponse
from app.services.assistant_service import answer

router = APIRouter(prefix="/assistant", tags=["Assistant"])

@router.post("/chat", response_model=ChatResponse)
def chat(data: ChatRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    soil = None
    if data.soil_test_id:
        soil = db.query(SoilTest).filter(SoilTest.id == data.soil_test_id, SoilTest.user_id == user.id).first()
    if not soil:
        soil = db.query(SoilTest).filter(SoilTest.user_id == user.id).order_by(SoilTest.created_at.desc()).first()
    soil_data = None
    if soil:
        soil_data = {"ph":soil.ph,"nitrogen":soil.nitrogen,"phosphorus":soil.phosphorus,"potassium":soil.potassium,
                     "ec":soil.ec,"moisture":soil.moisture,"temperature":soil.temperature,"organic_carbon":soil.organic_carbon}
    db.add(Conversation(user_id=user.id, role="user", content=data.message))
    lang = getattr(user, "language", None) or "en"
    reply, sources = answer(data.message, soil_data, lang)
    db.add(Conversation(user_id=user.id, role="assistant", content=reply))
    db.commit()
    return {"answer": reply, "sources": sources or ["Local agriculture knowledge base"]}
