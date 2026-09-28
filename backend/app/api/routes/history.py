from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.soil_test import SoilTest

router = APIRouter(prefix="/history", tags=["History"])

@router.get("")
def history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(SoilTest).filter(SoilTest.user_id == user.id).order_by(SoilTest.created_at.desc()).all()
