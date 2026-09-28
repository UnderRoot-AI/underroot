from sqlalchemy.orm import Session
from app.models.report import Report

def get_for_user(db: Session, user_id: int, report_id: int): return db.query(Report).filter(Report.user_id == user_id, Report.id == report_id).first()
def latest_for_test(db: Session, user_id: int, soil_test_id: int): return db.query(Report).filter(Report.user_id == user_id, Report.soil_test_id == soil_test_id).order_by(Report.created_at.desc()).first()
