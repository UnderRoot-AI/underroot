from pathlib import Path
import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.report_connection import get_report_db
from app.core.config import settings
from app.core.security import get_current_user
from app.models.user import User
from app.models.report import Report
from app.models.soil_test import SoilTest
from app.schemas.report import ReportGenerate, ReportOut, ReportVerify
from app.services.soil_service import calculate_health
from app.services.extraction_service import extract_parameters
from app.services.report_store_service import upsert_report_record
from app.integrations.ocr.client import extract_text
from app.services.recommendation_service import crop_recommendations, fertilizer_recommendations
from app.services.pdf_service import build_soil_report_pdf

router = APIRouter(prefix="/reports", tags=["Reports"])
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)

def out(r):
    params = json.loads(r.extracted_parameters) if r.extracted_parameters else None
    return {"id":r.id,"soil_test_id":r.soil_test_id,"file_name":r.file_name,"file_url":r.file_url,
            "status":r.status,"extracted_text":r.extracted_text,"extracted_parameters":params,"created_at":r.created_at}

@router.post("/upload", response_model=ReportOut)
async def upload(file: UploadFile = File(...), db: Session = Depends(get_db), report_db: Session = Depends(get_report_db), user: User = Depends(get_current_user)):
    safe_name = Path(file.filename or "report").name
    allowed = {".pdf", ".jpg", ".jpeg", ".png", ".webp", ".txt", ".csv"}
    if Path(safe_name).suffix.lower() not in allowed:
        raise HTTPException(400, "Unsupported file type. Use PDF, JPG, PNG, WEBP, TXT or CSV.")
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(413, "File is larger than 10 MB")
    destination = Path(settings.upload_dir) / f"{user.id}_{safe_name}"
    destination.write_bytes(content)
    report = Report(user_id=user.id, file_name=safe_name, file_url=f"/uploads/{destination.name}", status="uploaded")
    db.add(report); db.commit(); db.refresh(report)
    upsert_report_record(report_db, app_report_id=report.id, user_id=user.id, file_name=safe_name, file_path=str(destination), status="uploaded")
    return out(report)

@router.post("/generate", response_model=ReportOut)
def generate(data: ReportGenerate, db: Session = Depends(get_db), report_db: Session = Depends(get_report_db), user: User = Depends(get_current_user)):
    soil = db.query(SoilTest).filter(SoilTest.id == data.soil_test_id, SoilTest.user_id == user.id).first()
    if not soil: raise HTTPException(404, "Soil test not found")
    p = {"ph":soil.ph,"nitrogen":soil.nitrogen,"phosphorus":soil.phosphorus,"potassium":soil.potassium,
         "ec":soil.ec,"moisture":soil.moisture,"temperature":soil.temperature,"organic_carbon":soil.organic_carbon}
    existing = db.query(Report).filter(Report.user_id == user.id, Report.soil_test_id == soil.id).order_by(Report.created_at.desc()).first()
    if existing:
        upsert_report_record(report_db, app_report_id=existing.id, user_id=user.id, soil_test_id=soil.id, status=existing.status, extracted_text=existing.extracted_text, extracted_parameters=json.loads(existing.extracted_parameters) if existing.extracted_parameters else p)
        return out(existing)
    report = Report(user_id=user.id, soil_test_id=soil.id, status="generated",
                    extracted_parameters=json.dumps(p), extracted_text="Report generated from verified soil-test data.")
    db.add(report); db.commit(); db.refresh(report)
    upsert_report_record(report_db, app_report_id=report.id, user_id=user.id, soil_test_id=soil.id, status="generated", extracted_text=report.extracted_text, extracted_parameters=p)
    return out(report)

@router.post("/{report_id}/verify", response_model=ReportOut)
def verify(report_id: int, data: ReportVerify, db: Session = Depends(get_db), report_db: Session = Depends(get_report_db), user: User = Depends(get_current_user)):
    report = db.query(Report).filter(Report.id == report_id, Report.user_id == user.id).first()
    if not report: raise HTTPException(404, "Report not found")
    allowed = {"ph", "nitrogen", "phosphorus", "potassium", "ec", "moisture", "temperature", "organic_carbon"}
    params = {k: v for k, v in data.parameters.items() if k in allowed and v is not None}
    score, status = calculate_health(params)
    soil = SoilTest(user_id=user.id, location=data.location, latitude=data.latitude, longitude=data.longitude,
                    notes=data.notes, health_score=score, health_status=status, **params)
    db.add(soil); db.flush()
    report.soil_test_id = soil.id
    report.status = "verified"
    report.extracted_parameters = json.dumps(params)
    db.commit(); db.refresh(report)
    upsert_report_record(report_db, app_report_id=report.id, user_id=user.id, soil_test_id=soil.id, status="verified", extracted_text=report.extracted_text, extracted_parameters=params)
    return out(report)

@router.get("/{report_id}", response_model=ReportOut)
def get_report(report_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    r = db.query(Report).filter(Report.id == report_id, Report.user_id == user.id).first()
    if not r: raise HTTPException(404, "Report not found")
    return out(r)

@router.get("/{report_id}/pdf")
def report_pdf(report_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    r = db.query(Report).filter(Report.id == report_id, Report.user_id == user.id).first()
    if not r or not r.soil_test_id: raise HTTPException(404, "A verified soil report is required")
    soil = db.query(SoilTest).filter(SoilTest.id == r.soil_test_id, SoilTest.user_id == user.id).first()
    if not soil: raise HTTPException(404, "Soil test not found")
    p={"ph":soil.ph,"nitrogen":soil.nitrogen,"phosphorus":soil.phosphorus,"potassium":soil.potassium,"ec":soil.ec,"moisture":soil.moisture,"temperature":soil.temperature,"organic_carbon":soil.organic_carbon}
    test={"id":soil.id,"location":soil.location,"created_at":str(soil.created_at),"health_score":soil.health_score,"health_status":soil.health_status,"parameters":p}
    pdf=build_soil_report_pdf(test,crop_recommendations(p),fertilizer_recommendations(p))
    return Response(content=pdf, media_type="application/pdf", headers={"Content-Disposition":f'attachment; filename="soil-report-{soil.id}.pdf"'})
