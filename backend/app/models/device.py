"""
Device model — represents a physical (or virtual) soil-sensing device owned by a user.

Connection types are intentionally open-ended to support future hardware adapters:
  http, mqtt, ble, modbus, lorawan, manual, generic
"""
from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import ForeignKey, DateTime, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.connection import Base


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    # Unique identifier reported by the hardware (serial number, MAC, BLE address, etc.)
    # Unique within a user's account; globally unique is not enforced here.
    device_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    manufacturer: Mapped[str | None] = mapped_column(String(120), nullable=True)
    model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    # Human-readable name chosen by the user
    name: Mapped[str] = mapped_column(String(200), nullable=False, default="My Soil Device")
    # Connection type: http | mqtt | ble | modbus | lorawan | manual | generic
    connection_type: Mapped[str] = mapped_column(String(40), nullable=False, default="generic")
    # Status: online | offline | unknown
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="unknown")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = relationship("User", back_populates="devices")
    readings = relationship("HardwareReading", back_populates="device", cascade="all, delete-orphan")
