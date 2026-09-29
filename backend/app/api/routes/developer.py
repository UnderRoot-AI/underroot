import csv
import io
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from app.core.config import settings
from app.core.security import verify_password, create_developer_token, get_current_developer
from app.database.connection import get_db
from app.models.user import User
from app.models.soil_test import SoilTest
from app.models.device import Device
from app.models.hardware_reading import HardwareReading
from app.models.report import Report
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


# ── Authentication ────────────────────────────────────────────────────────────

@router.post("/login")
def developer_login(data: DeveloperLogin):
    if (
        data.email.strip().lower() != settings.developer_email.lower()
        or not verify_password(data.password, settings.developer_password_hash)
    ):
        raise HTTPException(401, "Invalid developer email or password")
    return {
        "access_token": create_developer_token(),
        "email": settings.developer_email,
        "role": "developer",
    }


# ── Stats ─────────────────────────────────────────────────────────────────────

@router.get("/stats")
def developer_stats(
    _: dict = Depends(get_current_developer),
    db: Session = Depends(get_db),
):
    total_users = db.query(func.count(User.id)).scalar() or 0
    verified_users = db.query(func.count(User.id)).filter(User.email_verified.is_(True)).scalar() or 0
    unverified_users = total_users - verified_users
    logged_in_users = (
        db.query(func.count(User.id)).filter(User.last_login_at.isnot(None)).scalar() or 0
    )
    total_logins = db.query(func.coalesce(func.sum(User.login_count), 0)).scalar() or 0
    total_tests = db.query(func.count(SoilTest.id)).scalar() or 0
    total_devices = db.query(func.count(Device.id)).filter(Device.is_active.is_(True)).scalar() or 0
    total_reports = db.query(func.count(Report.id)).scalar() or 0
    active_schemes = (
        db.query(func.count(GovernmentScheme.id))
        .filter(GovernmentScheme.active.is_(True))
        .scalar() or 0
    )
    return {
        "total_users": total_users,
        "verified_users": verified_users,
        "unverified_users": unverified_users,
        "logged_in_users": logged_in_users,
        "total_logins": int(total_logins),
        "total_soil_tests": total_tests,
        "total_devices": total_devices,
        "total_reports": total_reports,
        "active_schemes": active_schemes,
    }


# ── Users ─────────────────────────────────────────────────────────────────────

@router.get("/users")
def developer_users(
    _: dict = Depends(get_current_developer),
    db: Session = Depends(get_db),
):
    users = (
        db.query(User)
        .order_by(
            User.state.asc(),
            User.district.asc(),
            User.city_village.asc(),
            User.name.asc(),
        )
        .all()
    )
    return [
        {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "phone": u.phone,
            "state": u.state,
            "district": u.district,
            "village": u.city_village,
            "language": u.language,
            "login_count": u.login_count or 0,
            "email_verified": u.email_verified,
            "last_login_at": u.last_login_at,
            "created_at": u.created_at,
        }
        for u in users
    ]


@router.get("/users/export")
def export_users(
    _: dict = Depends(get_current_developer),
    db: Session = Depends(get_db),
):
    users = (
        db.query(User)
        .order_by(
            User.state.asc(),
            User.district.asc(),
            User.city_village.asc(),
            User.name.asc(),
        )
        .all()
    )
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow([
        "Name", "Email", "Phone", "State", "District", "Village",
        "Language", "Email Verified", "Login Count", "Last Login", "Registered At",
    ])
    for u in users:
        writer.writerow([
            u.name, u.email, u.phone or "",
            u.state or "", u.district or "", u.city_village or "",
            u.language,
            "Yes" if u.email_verified else "No",
            u.login_count or 0,
            u.last_login_at.isoformat() if u.last_login_at else "",
            u.created_at.isoformat() if u.created_at else "",
        ])
    out.seek(0)
    return StreamingResponse(
        iter([out.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=smart-soil-users-by-location.csv"},
    )


# ── Soil Tests ────────────────────────────────────────────────────────────────

@router.get("/soil-tests")
def developer_soil_tests(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    _: dict = Depends(get_current_developer),
    db: Session = Depends(get_db),
):
    """Return recent soil tests across all users (admin view)."""
    rows = (
        db.query(SoilTest)
        .order_by(SoilTest.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    total = db.query(func.count(SoilTest.id)).scalar() or 0

    # Build a user name lookup from the IDs we need
    user_ids = list({r.user_id for r in rows})
    users_map: dict[int, str] = {}
    if user_ids:
        for u in db.query(User.id, User.name, User.email).filter(User.id.in_(user_ids)).all():
            users_map[u.id] = u.name

    return {
        "total": total,
        "items": [
            {
                "id": s.id,
                "user_id": s.user_id,
                "user_name": users_map.get(s.user_id, "—"),
                "location": s.location,
                "source": s.source,
                "health_score": s.health_score,
                "health_status": s.health_status,
                "ph": s.ph,
                "nitrogen": s.nitrogen,
                "phosphorus": s.phosphorus,
                "potassium": s.potassium,
                "created_at": s.created_at,
            }
            for s in rows
        ],
    }


# ── Devices ───────────────────────────────────────────────────────────────────

@router.get("/devices")
def developer_devices(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    _: dict = Depends(get_current_developer),
    db: Session = Depends(get_db),
):
    """Return all registered devices across all users (admin view)."""
    rows = (
        db.query(Device)
        .filter(Device.is_active.is_(True))
        .order_by(Device.last_seen_at.desc().nullslast(), Device.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    total = (
        db.query(func.count(Device.id)).filter(Device.is_active.is_(True)).scalar() or 0
    )

    user_ids = list({r.user_id for r in rows})
    users_map: dict[int, str] = {}
    if user_ids:
        for u in db.query(User.id, User.name).filter(User.id.in_(user_ids)).all():
            users_map[u.id] = u.name

    # Latest reading count per device
    reading_counts: dict[int, int] = {}
    if rows:
        dev_ids = [r.id for r in rows]
        counts = (
            db.query(HardwareReading.device_id, func.count(HardwareReading.id))
            .filter(HardwareReading.device_id.in_(dev_ids))
            .group_by(HardwareReading.device_id)
            .all()
        )
        reading_counts = {did: cnt for did, cnt in counts}

    return {
        "total": total,
        "items": [
            {
                "id": d.id,
                "device_id": d.device_id,
                "name": d.name,
                "manufacturer": d.manufacturer,
                "model": d.model,
                "connection_type": d.connection_type,
                "status": d.status,
                "user_id": d.user_id,
                "owner_name": users_map.get(d.user_id, "—"),
                "last_seen_at": d.last_seen_at,
                "reading_count": reading_counts.get(d.id, 0),
                "created_at": d.created_at,
            }
            for d in rows
        ],
    }


# ── Reports ───────────────────────────────────────────────────────────────────

@router.get("/reports")
def developer_reports(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    _: dict = Depends(get_current_developer),
    db: Session = Depends(get_db),
):
    """Return all reports across all users (admin view)."""
    rows = (
        db.query(Report)
        .order_by(Report.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    total = db.query(func.count(Report.id)).scalar() or 0

    user_ids = list({r.user_id for r in rows})
    users_map: dict[int, str] = {}
    if user_ids:
        for u in db.query(User.id, User.name).filter(User.id.in_(user_ids)).all():
            users_map[u.id] = u.name

    return {
        "total": total,
        "items": [
            {
                "id": r.id,
                "user_id": r.user_id,
                "owner_name": users_map.get(r.user_id, "—"),
                "soil_test_id": r.soil_test_id,
                "file_name": r.file_name,
                "status": r.status,
                "created_at": r.created_at,
            }
            for r in rows
        ],
    }


# ── Government Schemes ────────────────────────────────────────────────────────

@router.get("/schemes")
def list_schemes(
    _: dict = Depends(get_current_developer),
    db: Session = Depends(get_db),
):
    return (
        db.query(GovernmentScheme)
        .order_by(GovernmentScheme.active.desc(), GovernmentScheme.name.asc())
        .all()
    )


@router.post("/schemes")
def create_scheme(
    data: SchemePayload,
    _: dict = Depends(get_current_developer),
    db: Session = Depends(get_db),
):
    if db.query(GovernmentScheme).filter(
        func.lower(GovernmentScheme.name) == data.name.lower()
    ).first():
        raise HTTPException(409, "A scheme with this name already exists")
    row = GovernmentScheme(**data.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.put("/schemes/{scheme_id}")
def update_scheme(
    scheme_id: int,
    data: SchemePayload,
    _: dict = Depends(get_current_developer),
    db: Session = Depends(get_db),
):
    row = db.get(GovernmentScheme, scheme_id)
    if not row:
        raise HTTPException(404, "Government scheme not found")
    for k, v in data.model_dump().items():
        setattr(row, k, v)
    row.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/schemes/{scheme_id}")
def delete_scheme(
    scheme_id: int,
    _: dict = Depends(get_current_developer),
    db: Session = Depends(get_db),
):
    row = db.get(GovernmentScheme, scheme_id)
    if not row:
        raise HTTPException(404, "Government scheme not found")
    db.delete(row)
    db.commit()
    return {"message": "Government scheme removed"}
