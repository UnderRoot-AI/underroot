from sqlalchemy.orm import Session
from app.models.soil_test import SoilTest

def list_for_user(db: Session, user_id: int): return db.query(SoilTest).filter(SoilTest.user_id == user_id).order_by(SoilTest.created_at.desc()).all()
def get_for_user(db: Session, user_id: int, test_id: int): return db.query(SoilTest).filter(SoilTest.user_id == user_id, SoilTest.id == test_id).first()
