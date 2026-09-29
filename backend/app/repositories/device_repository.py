"""
Repository layer for Device and HardwareReading CRUD.

All queries enforce user_id ownership — no query returns data from another user.
"""
from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.device import Device
from app.models.hardware_reading import HardwareReading


# ── Device ────────────────────────────────────────────────────────────────────

def create_device(db: Session, user_id: int, **kwargs) -> Device:
    d = Device(user_id=user_id, **kwargs)
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


def list_devices(db: Session, user_id: int) -> list[Device]:
    return (
        db.query(Device)
        .filter(Device.user_id == user_id, Device.is_active == True)
        .order_by(Device.created_at.desc())
        .all()
    )


def get_device(db: Session, user_id: int, device_pk: int) -> Device | None:
    return (
        db.query(Device)
        .filter(Device.id == device_pk, Device.user_id == user_id)
        .first()
    )


def get_device_by_device_id(db: Session, user_id: int, device_id: str) -> Device | None:
    return (
        db.query(Device)
        .filter(Device.device_id == device_id, Device.user_id == user_id)
        .first()
    )


def deactivate_device(db: Session, user_id: int, device_pk: int) -> Device | None:
    d = get_device(db, user_id, device_pk)
    if not d:
        return None
    d.is_active = False
    d.status = "offline"
    db.commit()
    db.refresh(d)
    return d


def touch_device(db: Session, device: Device) -> None:
    """Update last_seen_at and status to online."""
    device.last_seen_at = datetime.now(timezone.utc)
    device.status = "online"
    db.commit()


# ── HardwareReading ───────────────────────────────────────────────────────────

def create_reading(db: Session, **kwargs) -> HardwareReading:
    r = HardwareReading(**kwargs)
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def list_readings(db: Session, user_id: int, device_pk: int, limit: int = 50) -> list[HardwareReading]:
    return (
        db.query(HardwareReading)
        .filter(HardwareReading.device_id == device_pk, HardwareReading.user_id == user_id)
        .order_by(HardwareReading.created_at.desc())
        .limit(limit)
        .all()
    )


def get_latest_reading(db: Session, user_id: int, device_pk: int) -> HardwareReading | None:
    return (
        db.query(HardwareReading)
        .filter(HardwareReading.device_id == device_pk, HardwareReading.user_id == user_id)
        .order_by(HardwareReading.created_at.desc())
        .first()
    )
