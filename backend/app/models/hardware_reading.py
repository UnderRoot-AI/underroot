"""
HardwareReading — stores a single measurement payload from any physical device.

Design goals:
- Extensible: the `measurements` JSON column can store any parameter from any device,
  not just the 8 core SoilTest parameters.  This allows SoilX and future sensors
  to contribute sulphur, boron, iron, zinc, humus indices, etc. without schema changes.
- Traceable: raw_payload preserves the original device output before any normalization.
- Linked: soil_test_id is set when a SoilTest is automatically created from this reading.
"""
from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import ForeignKey, DateTime, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.connection import Base


class HardwareReading(Base):
    __tablename__ = "hardware_readings"

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    # Wall-clock timestamp claimed by the device (may differ from created_at)
    reading_timestamp: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # Source provenance — e.g. "generic", "soilx", "modbus", "lorawan"
    source: Mapped[str] = mapped_column(String(40), nullable=False, default="generic")
    manufacturer: Mapped[str | None] = mapped_column(String(120), nullable=True)
    model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    # Extensible measurement store:
    # {
    #   "ph":  {"value": 6.8, "unit": "pH"},
    #   "nitrogen": {"value": 185, "unit": "kg/ha"},
    #   ... any additional parameters from the device ...
    # }
    measurements: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    # Raw payload as received from the device (before normalization).
    # Useful for debugging and re-processing.  Never store credentials here.
    raw_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Set once a SoilTest has been automatically created from this reading
    soil_test_id: Mapped[int | None] = mapped_column(
        ForeignKey("soil_tests.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    device = relationship("Device", back_populates="readings")
    user = relationship("User")
