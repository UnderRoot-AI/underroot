import json
import logging
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.report_connection import get_report_db
from app.core.config import settings
from app.core.security import get_current_user
from app.models.user import User
from app.models.report import Report
from app.services.extraction_service import extract_parameters
from app.integrations.ocr.client import extract_text
from app.services.report_store_service import upsert_report_record
from app.integrations.rag.client import get_rag

logger = logging.getLogger("underroot.ocr")

router = APIRouter(prefix="/ocr", tags=["OCR"])

@router.post("/{report_id}/process")
def process(
    report_id: int,
    db: Session = Depends(get_db),
    report_db: Session = Depends(get_report_db),
    user: User = Depends(get_current_user),
):
    r = db.query(Report).filter(Report.id == report_id, Report.user_id == user.id).first()
    if not r:
        raise HTTPException(404, "Report not found")

    path = Path(settings.upload_dir) / Path(r.file_url or "").name
    if not path.exists():
        raise HTTPException(404, "Uploaded file is missing")

    try:
        text, engine = extract_text(path)

        params = extract_parameters(text)

        r.status = "processed"
        r.extracted_text = text or "No readable text was found. Please verify the values manually."
        r.extracted_parameters = json.dumps(params)
        db.commit()

        rag_chunks = get_rag().retrieve(text or "soil report", top_k=3)
        rag_context = "\n\n".join(f"[{x.source}] {x.text}" for x in rag_chunks)

        upsert_report_record(
            report_db,
            app_report_id=r.id,
            user_id=user.id,
            file_name=r.file_name,
            file_path=str(path),
            status=r.status,
            extracted_text=r.extracted_text,
            extracted_parameters=params,
            ocr_engine=engine,
            rag_context=rag_context,
        )

        return {
            "report_id": r.id,
            "status": r.status,
            "ocr_engine": engine,
            "extracted_text": r.extracted_text,
            "extracted_parameters": params,
        }

    except HTTPException:
        # Re-raise FastAPI HTTP exceptions (404, 422, etc.) unchanged.
        raise

    except Exception as exc:
        logger.exception("OCR process failed for report %s", report_id)
        raise HTTPException(
            status_code=500,
            detail=f"OCR processing failed: {exc}",
        )
