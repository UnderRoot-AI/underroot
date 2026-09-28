from datetime import datetime, timezone
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database.report_connection import ReportBase

class SoilReportRecord(ReportBase):
    """Separate persistence store for uploaded/processed soil reports."""
    __tablename__ = "soil_report_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    app_report_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    soil_test_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="uploaded")
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_parameters: Mapped[str | None] = mapped_column(Text, nullable=True)
    ocr_engine: Mapped[str | None] = mapped_column(String(80), nullable=True)
    rag_context: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
