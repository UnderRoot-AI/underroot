from fastapi import APIRouter, Depends, HTTPException
import json
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.report_connection import get_report_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.soil_test import SoilTest
from app.models.report import Report
from app.services.report_store_service import upsert_report_record
from app.schemas.soil import SoilTestCreate, SoilTestOut
from app.services.soil_service import calculate_health
from app.services.soil_analyzer import analyze_soil

router = APIRouter(prefix="/soil", tags=["Soil"])

def params_of(s: SoilTest):
    return {"ph":s.ph,"nitrogen":s.nitrogen,"phosphorus":s.phosphorus,"potassium":s.potassium,"ec":s.ec,"moisture":s.moisture,"temperature":s.temperature,"organic_carbon":s.organic_carbon}

def serialize(s: SoilTest):
    return {"id":s.id,"field_id":s.field_id,"location":s.location,"latitude":s.latitude,"longitude":s.longitude,"created_at":s.created_at,"parameters":params_of(s),"health_score":s.health_score,"health_status":s.health_status,"notes":s.notes}

@router.post("/tests", response_model=SoilTestOut)
def create_test(data: SoilTestCreate, db: Session = Depends(get_db), report_db: Session = Depends(get_report_db), user: User = Depends(get_current_user)):
    p=data.parameters.model_dump(); score,status=calculate_health(p)
    s=SoilTest(user_id=user.id,field_id=data.field_id,location=data.location,latitude=data.latitude,longitude=data.longitude,health_score=score,health_status=status,notes=data.notes,**p)
    db.add(s); db.commit(); db.refresh(s)
    report=Report(user_id=user.id,soil_test_id=s.id,status="generated",extracted_parameters=json.dumps(p),extracted_text="Report generated from soil-probe/manual verified soil-test data.")
    db.add(report); db.commit(); db.refresh(report)
    upsert_report_record(report_db,app_report_id=report.id,user_id=user.id,soil_test_id=s.id,status="generated",extracted_text=report.extracted_text,extracted_parameters=p)
    return serialize(s)

@router.get("/tests", response_model=list[SoilTestOut])
def list_tests(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return [serialize(s) for s in db.query(SoilTest).filter(SoilTest.user_id==user.id).order_by(SoilTest.created_at.desc()).all()]

@router.get("/tests/{test_id}", response_model=SoilTestOut)
def get_test(test_id:int, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    s=db.query(SoilTest).filter(SoilTest.id==test_id,SoilTest.user_id==user.id).first()
    if not s: raise HTTPException(404,"Soil test not found")
    return serialize(s)

@router.get("/tests/{test_id}/analysis")
def analyze_test(test_id:int, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    s=db.query(SoilTest).filter(SoilTest.id==test_id,SoilTest.user_id==user.id).first()
    if not s: raise HTTPException(404,"Soil test not found")
    return {"soil_test":serialize(s),"analysis":analyze_soil(params_of(s))}
