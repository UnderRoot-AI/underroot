from datetime import datetime, timezone
from sqlalchemy import ForeignKey, DateTime, Float, Text, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.connection import Base

class SoilTest(Base):
    __tablename__ = "soil_tests"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    field_id: Mapped[int | None] = mapped_column(ForeignKey("fields.id"), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    ph: Mapped[float | None] = mapped_column(Float, nullable=True)
    nitrogen: Mapped[float | None] = mapped_column(Float, nullable=True)
    phosphorus: Mapped[float | None] = mapped_column(Float, nullable=True)
    potassium: Mapped[float | None] = mapped_column(Float, nullable=True)
    ec: Mapped[float | None] = mapped_column(Float, nullable=True)
    moisture: Mapped[float | None] = mapped_column(Float, nullable=True)
    temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    organic_carbon: Mapped[float | None] = mapped_column(Float, nullable=True)
    health_score: Mapped[float] = mapped_column(Float, default=0)
    health_status: Mapped[str] = mapped_column(String(40), default="Unknown")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    # Hardware provenance — set when a test originates from a physical probe
    # source: "manual" | "ocr" | "mock" | "soilx"
    source: Mapped[str] = mapped_column(String(40), default="manual")
    # Identifier reported by the hardware device (BLE address, serial number, etc.)
    device_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    user = relationship("User", back_populates="soil_tests")
