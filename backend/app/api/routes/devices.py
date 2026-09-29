"""
Device management and hardware reading ingestion API.

Endpoints
─────────
GET  /api/devices                          — list authenticated user's devices
POST /api/devices                          — register a new device
GET  /api/devices/{device_pk}              — get device by primary key
DELETE /api/devices/{device_pk}            — deactivate device (soft delete)
POST /api/devices/{device_pk}/readings     — ingest a hardware measurement
GET  /api/devices/{device_pk}/readings     — list readings for a device
GET  /api/devices/{device_pk}/readings/latest — latest reading

All endpoints enforce ownership: a user can only see/modify their own devices.
"""
from __future__ import annotations
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.report_connection import get_report_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.hardware import DeviceCreate, DeviceOut, ReadingIngest, ReadingOut, CONNECTION_TYPES
from app.repositories.device_repository import (
    create_device,
    list_devices,
    get_device,
    get_device_by_device_id,
    deactivate_device,
    list_readings,
    get_latest_reading,
)
from app.services.device_service import ingest_reading

router = APIRouter(prefix="/devices", tags=["Devices"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _device_or_404(db: Session, user: User, device_pk: int):
    d = get_device(db, user.id, device_pk)
    if not d:
        raise HTTPException(status_code=404, detail="Device not found")
    return d


def _serialize_device(d) -> dict:
    return {
        "id": d.id,
        "device_id": d.device_id,
        "manufacturer": d.manufacturer,
        "model": d.model,
        "name": d.name,
        "connection_type": d.connection_type,
        "status": d.status,
        "is_active": d.is_active,
        "last_seen_at": d.last_seen_at,
        "created_at": d.created_at,
    }


def _serialize_reading(r) -> dict:
    return {
        "id": r.id,
        "device_id": r.device_id,
        "user_id": r.user_id,
        "reading_timestamp": r.reading_timestamp,
        "source": r.source,
        "manufacturer": r.manufacturer,
        "model": r.model,
        "measurements": r.measurements,
        "soil_test_id": r.soil_test_id,
        "created_at": r.created_at,
    }


# ── Device CRUD ───────────────────────────────────────────────────────────────

@router.get("")
def list_user_devices(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Return all active devices belonging to the authenticated user."""
    devices = list_devices(db, user.id)
    return [_serialize_device(d) for d in devices]


@router.post("", status_code=201)
def register_device(
    data: DeviceCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Register a new device under the authenticated user's account."""
    # Prevent duplicate device_id per user
    existing = get_device_by_device_id(db, user.id, data.device_id)
    if existing and existing.is_active:
        raise HTTPException(
            status_code=409,
            detail=f"A device with device_id '{data.device_id}' already exists in your account",
        )
    device = create_device(
        db,
        user_id=user.id,
        device_id=data.device_id,
        manufacturer=data.manufacturer,
        model=data.model,
        name=data.name,
        connection_type=data.connection_type,
    )
    return _serialize_device(device)


@router.get("/{device_pk}")
def get_device_detail(
    device_pk: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return _serialize_device(_device_or_404(db, user, device_pk))


@router.delete("/{device_pk}")
def delete_device(
    device_pk: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Soft-delete (deactivate) a device.  Hard delete is intentionally avoided."""
    d = deactivate_device(db, user.id, device_pk)
    if not d:
        raise HTTPException(status_code=404, detail="Device not found")
    return {"message": "Device deactivated", "device_id": d.device_id}


# ── Ingestion ─────────────────────────────────────────────────────────────────

@router.post("/{device_pk}/readings", status_code=201)
def ingest_device_reading(
    device_pk: int,
    data: ReadingIngest,
    db: Session = Depends(get_db),
    report_db: Session = Depends(get_report_db),
    user: User = Depends(get_current_user),
):
    """
    Ingest a hardware measurement for a registered device.

    - Authenticates the user
    - Verifies device ownership
    - Validates the measurement payload (NaN/Inf rejected; core bounds checked)
    - Stores the reading (including extended parameters beyond the 8 core ones)
    - Automatically creates a SoilTest from core parameters
    - Runs the existing soil health analyzer
    - Updates device last_seen_at and status

    Returns the stored reading and the created SoilTest summary.
    """
    device = _device_or_404(db, user, device_pk)

    # Convert pydantic MeasurementValue objects to plain dicts for storage
    measurements_dict = {k: {"value": mv.value, "unit": mv.unit} for k, mv in data.measurements.items()}

    reading, soil_test = ingest_reading(
        db=db,
        device=device,
        measurements=measurements_dict,
        reading_timestamp=data.timestamp,
        raw_payload=json.dumps({"timestamp": str(data.timestamp), "measurements": measurements_dict}),
        report_db=report_db,
    )

    return {
        "reading": _serialize_reading(reading),
        "soil_test": {
            "id": soil_test.id,
            "health_score": soil_test.health_score,
            "health_status": soil_test.health_status,
            "source": soil_test.source,
            "device_id": soil_test.device_id,
            "created_at": soil_test.created_at,
        },
        "message": "Reading ingested and soil test created successfully",
    }


# ── Reading queries ───────────────────────────────────────────────────────────

@router.get("/{device_pk}/readings")
def list_device_readings(
    device_pk: int,
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Return up to `limit` readings for the device, newest first."""
    _device_or_404(db, user, device_pk)
    readings = list_readings(db, user.id, device_pk, limit=min(limit, 200))
    return [_serialize_reading(r) for r in readings]


@router.get("/{device_pk}/readings/latest")
def latest_device_reading(
    device_pk: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Return the most recent reading for the device."""
    _device_or_404(db, user, device_pk)
    r = get_latest_reading(db, user.id, device_pk)
    if not r:
        raise HTTPException(status_code=404, detail="No readings found for this device")
    return _serialize_reading(r)


# ── Supported profiles ────────────────────────────────────────────────────────

@router.get("/meta/connection-types")
def supported_connection_types():
    """Return the list of supported connection types for UI dropdowns."""
    return {"connection_types": sorted(CONNECTION_TYPES)}


@router.get("/meta/profiles")
def device_profiles():
    """
    Return known device profiles for UI auto-fill.

    SoilX is listed as a supported profile even though direct BLE connectivity
    is not yet implemented.  Users can register a SoilX device and send
    readings through the HTTP ingestion endpoint.
    """
    return {
        "profiles": [
            {
                "manufacturer": "REVE Nano-Science",
                "model": "SoilX",
                "connection_type": "generic",
                "integration_status": "integration_ready",
                "notes": "Register device and POST readings via HTTP ingestion endpoint",
            },
            {
                "manufacturer": "Generic / DIY",
                "model": "HTTP Sensor",
                "connection_type": "http",
                "integration_status": "supported",
                "notes": "Any device that can POST JSON measurements",
            },
        ]
    }
