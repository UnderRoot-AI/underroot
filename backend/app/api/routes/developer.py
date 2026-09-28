import csv
import io
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import verify_password, create_developer_token, get_current_developer
from app.database.connection import get_db
from app.models.user import User
from app.models.soil_test import SoilTest
from app.models.government_scheme import GovernmentScheme

router = APIRouter(prefix="/developer", tags=["Developer"])

class DeveloperLogin(BaseModel):
    email: str
    password: str

class SchemePayload(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    state: str | None = None
    description: str = Field(min_length=5)
    url: str
    active: bool = True

@router.post("/login")
def developer_login(data: DeveloperLogin):
    if data.email.strip().lower() != settings.developer_email.lower() or not verify_password(data.password, settings.developer_password_hash):
        raise HTTPException(401, "Invalid developer email or password")
    return {"access_token": create_developer_token(), "email": settings.developer_email, "role": "developer"}

@router.get("/stats")
def developer_stats(_: dict = Depends(get_current_developer), db: Session = Depends(get_db)):
    total_users = db.query(func.count(User.id)).scalar() or 0
    logged_in_users = db.query(func.count(User.id)).filter(User.last_login_at.isnot(None)).scalar() or 0
    total_logins = db.query(func.coalesce(func.sum(User.login_count), 0)).scalar() or 0
    total_tests = db.query(func.count(SoilTest.id)).scalar() or 0
    active_schemes = db.query(func.count(GovernmentScheme.id)).filter(GovernmentScheme.active.is_(True)).scalar() or 0
    return {"total_users": total_users, "logged_in_users": logged_in_users, "total_logins": int(total_logins), "total_soil_tests": total_tests, "active_schemes": active_schemes}

@router.get("/users")
def developer_users(_: dict = Depends(get_current_developer), db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.state.asc(), User.district.asc(), User.city_village.asc(), User.name.asc()).all()
    return [{"id":u.id,"name":u.name,"email":u.email,"phone":u.phone,"state":u.state,"district":u.district,"village":u.city_village,"language":u.language,"login_count":u.login_count or 0,"last_login_at":u.last_login_at,"created_at":u.created_at} for u in users]

@router.get("/users/export")
def export_users(_: dict = Depends(get_current_developer), db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.state.asc(), User.district.asc(), User.city_village.asc(), User.name.asc()).all()
    out = io.StringIO(); writer = csv.writer(out)
    writer.writerow(["Name","Email","Phone","State","District","Village","Language","Login Count","Last Login","Registered At"])
    for u in users:
        writer.writerow([u.name,u.email,u.phone or "",u.state or "",u.district or "",u.city_village or "",u.language,u.login_count or 0,u.last_login_at.isoformat() if u.last_login_at else "",u.created_at.isoformat() if u.created_at else ""])
    out.seek(0)
    return StreamingResponse(iter([out.getvalue()]), media_type="text/csv", headers={"Content-Disposition":"attachment; filename=smart-soil-users-by-location.csv"})

@router.get("/schemes")
def list_schemes(_: dict = Depends(get_current_developer), db: Session = Depends(get_db)):
    return db.query(GovernmentScheme).order_by(GovernmentScheme.active.desc(), GovernmentScheme.name.asc()).all()

@router.post("/schemes")
def create_scheme(data: SchemePayload, _: dict = Depends(get_current_developer), db: Session = Depends(get_db)):
    if db.query(GovernmentScheme).filter(func.lower(GovernmentScheme.name) == data.name.lower()).first():
        raise HTTPException(409, "A scheme with this name already exists")
    row = GovernmentScheme(**data.model_dump())
    db.add(row); db.commit(); db.refresh(row)
    return row

@router.put("/schemes/{scheme_id}")
def update_scheme(scheme_id: int, data: SchemePayload, _: dict = Depends(get_current_developer), db: Session = Depends(get_db)):
    row = db.get(GovernmentScheme, scheme_id)
    if not row: raise HTTPException(404, "Government scheme not found")
    for k,v in data.model_dump().items(): setattr(row,k,v)
    row.updated_at = datetime.now(timezone.utc)
    db.commit(); db.refresh(row)
    return row

@router.delete("/schemes/{scheme_id}")
def delete_scheme(scheme_id: int, _: dict = Depends(get_current_developer), db: Session = Depends(get_db)):
    row = db.get(GovernmentScheme, scheme_id)
    if not row: raise HTTPException(404, "Government scheme not found")
    db.delete(row); db.commit()
    return {"message":"Government scheme removed"}
