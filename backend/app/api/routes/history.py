from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.soil_test import SoilTest

router = APIRouter(prefix="/history", tags=["History"])


def _serialize(s: SoilTest) -> dict:
    return {
        "id": s.id,
        "field_id": s.field_id,
        "location": s.location,
        "latitude": s.latitude,
        "longitude": s.longitude,
        "created_at": s.created_at,
        "health_score": s.health_score,
        "health_status": s.health_status,
        "notes": s.notes,
        "source": s.source,
        "parameters": {
            "ph": s.ph,
            "nitrogen": s.nitrogen,
            "phosphorus": s.phosphorus,
            "potassium": s.potassium,
            "ec": s.ec,
            "moisture": s.moisture,
            "temperature": s.temperature,
            "organic_carbon": s.organic_carbon,
        },
    }


@router.get("")
def history(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    tests = (
        db.query(SoilTest)
        .filter(SoilTest.user_id == user.id)
        .order_by(SoilTest.created_at.desc())
        .all()
    )
    return [_serialize(s) for s in tests]
