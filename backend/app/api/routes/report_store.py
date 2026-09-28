import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.report_connection import get_report_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.soil_report_record import SoilReportRecord

router = APIRouter(prefix="/soil-reports", tags=["Soil Report Database"])

def serialize(r: SoilReportRecord):
    return {
        "id": r.id, "app_report_id": r.app_report_id, "soil_test_id": r.soil_test_id, "file_name": r.file_name,
        "status": r.status, "extracted_text": r.extracted_text,
        "extracted_parameters": json.loads(r.extracted_parameters) if r.extracted_parameters else None,
        "ocr_engine": r.ocr_engine, "rag_context": r.rag_context,
        "created_at": r.created_at, "updated_at": r.updated_at,
    }

@router.get("")
def list_soil_reports(db: Session = Depends(get_report_db), user: User = Depends(get_current_user)):
    rows = db.query(SoilReportRecord).filter(SoilReportRecord.user_id == user.id).order_by(SoilReportRecord.created_at.desc()).all()
    return [serialize(r) for r in rows]

@router.get("/{record_id}")
def get_soil_report(record_id: int, db: Session = Depends(get_report_db), user: User = Depends(get_current_user)):
    row = db.query(SoilReportRecord).filter(SoilReportRecord.id == record_id, SoilReportRecord.user_id == user.id).first()
    if not row:
        raise HTTPException(404, "Stored soil report not found")
    return serialize(row)
