import json
from sqlalchemy.orm import Session
from app.models.soil_report_record import SoilReportRecord

def upsert_report_record(
    db: Session, *, app_report_id: int, user_id: int, soil_test_id: int | None = None, file_name: str | None = None,
    file_path: str | None = None, status: str = "uploaded", extracted_text: str | None = None,
    extracted_parameters: dict | None = None, ocr_engine: str | None = None, rag_context: str | None = None,
):
    record = db.query(SoilReportRecord).filter(SoilReportRecord.app_report_id == app_report_id).first()
    if not record:
        record = SoilReportRecord(app_report_id=app_report_id, user_id=user_id)
        db.add(record)
    for key, value in {
        "soil_test_id": soil_test_id, "file_name": file_name, "file_path": file_path, "status": status,
        "extracted_text": extracted_text,
        "extracted_parameters": json.dumps(extracted_parameters) if extracted_parameters is not None else None,
        "ocr_engine": ocr_engine, "rag_context": rag_context,
    }.items():
        if value is not None:
            setattr(record, key, value)
    db.commit(); db.refresh(record)
    return record
