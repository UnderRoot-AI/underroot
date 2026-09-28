from sqlalchemy.orm import Session
from app.models.conversation import Conversation

def add(db: Session, user_id: int, role: str, content: str):
    row=Conversation(user_id=user_id, role=role, content=content); db.add(row); return row

def latest(db: Session, user_id: int, limit: int = 20):
    return db.query(Conversation).filter(Conversation.user_id == user_id).order_by(Conversation.created_at.desc()).limit(limit).all()
