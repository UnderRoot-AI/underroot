from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.soil_test import SoilTest
from app.services.recommendation_service import crop_recommendations, fertilizer_recommendations

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

def get_soil(soil_test_id, db, user):
    q = db.query(SoilTest).filter(SoilTest.user_id == user.id)
    s = q.filter(SoilTest.id == soil_test_id).first() if soil_test_id else q.order_by(SoilTest.created_at.desc()).first()
    if not s: raise HTTPException(404, "No soil test available")
    return vars(s)

@router.get("/crops")
def crops(soil_test_id: int | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return crop_recommendations(get_soil(soil_test_id, db, user))

@router.get("/fertilizer")
def fertilizer(soil_test_id: int | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return fertilizer_recommendations(get_soil(soil_test_id, db, user))
