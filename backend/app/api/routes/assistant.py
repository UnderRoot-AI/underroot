from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.soil_test import SoilTest
from app.repositories.conversation_repository import add as conv_add, latest as conv_latest
from app.schemas.assistant import ChatRequest, ChatResponse
from app.services.assistant_service import answer

router = APIRouter(prefix="/assistant", tags=["Assistant"])


@router.post("/chat", response_model=ChatResponse)
def chat(
    data: ChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Validate non-empty message
    if not data.message or not data.message.strip():
        raise HTTPException(status_code=422, detail="Message cannot be empty")

    # Retrieve most relevant soil test (explicit ID or latest)
    soil = None
    if data.soil_test_id:
        soil = (
            db.query(SoilTest)
            .filter(SoilTest.id == data.soil_test_id, SoilTest.user_id == user.id)
            .first()
        )
    if not soil:
        soil = (
            db.query(SoilTest)
            .filter(SoilTest.user_id == user.id)
            .order_by(SoilTest.created_at.desc())
            .first()
        )

    # Build soil parameter dict (raw measurements only — no secrets)
    soil_data = None
    health_score = None
    health_status = None
    if soil:
        soil_data = {
            "ph": soil.ph,
            "nitrogen": soil.nitrogen,
            "phosphorus": soil.phosphorus,
            "potassium": soil.potassium,
            "ec": soil.ec,
            "moisture": soil.moisture,
            "temperature": soil.temperature,
            "organic_carbon": soil.organic_carbon,
        }
        health_score = soil.health_score
        health_status = soil.health_status

    # Retrieve recent conversation history (max 10 pairs = 20 rows)
    recent_rows = conv_latest(db, user.id, limit=20)
    # conv_latest returns newest-first; reverse to chronological order
    history = [
        {"role": r.role, "content": r.content}
        for r in reversed(recent_rows)
    ]

    # Persist user turn
    conv_add(db, user.id, "user", data.message)

    # User language preference
    lang = getattr(user, "language", None) or "en"
    user_name = getattr(user, "name", None)

    # Generate grounded response
    try:
        reply, sources = answer(
            message=data.message,
            soil=soil_data,
            language=lang,
            health_score=health_score,
            health_status=health_status,
            history=history,
            user_name=user_name,
        )
    except Exception:
        reply = (
            "I'm having trouble reaching the agricultural knowledge service right now. "
            "Your stored soil data is still available from the Soil Analysis page."
        )
        sources = []

    # Persist assistant turn
    conv_add(db, user.id, "assistant", reply)
    db.commit()

    return {"answer": reply, "sources": sources}


@router.get("/history")
def get_history(
    limit: int = 40,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Return recent conversation history for the authenticated user."""
    rows = conv_latest(db, user.id, limit=limit)
    return [
        {"role": r.role, "content": r.content, "created_at": r.created_at}
        for r in reversed(rows)
    ]
