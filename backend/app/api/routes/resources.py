from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.government_scheme import GovernmentScheme

router = APIRouter(prefix="/resources", tags=["Government Resources"])

@router.get("/government")
def government_resources(db: Session = Depends(get_db)):
    rows = db.query(GovernmentScheme).filter(GovernmentScheme.active.is_(True)).order_by(GovernmentScheme.name.asc()).all()
    return {
        "title": "Official agriculture resources",
        "items": [{"id":r.id,"name":r.name,"state":r.state,"url":r.url,"description":r.description,"updated_at":r.updated_at} for r in rows],
        "note": "Government information is maintained by the developer account. Open the official portal for current eligibility, dates, application status and scheme rules."
    }
