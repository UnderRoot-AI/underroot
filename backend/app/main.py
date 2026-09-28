from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.core.config import settings
from app.database.connection import Base, engine
from app.database.report_connection import ReportBase, report_engine
from app.database.migrations import ensure_user_columns, ensure_report_columns, ensure_soil_test_columns
from app import models  # register SQLAlchemy models
from app.models.soil_report_record import SoilReportRecord  # register report-store model
from app.database.connection import SessionLocal
from app.services.scheme_seed import seed_schemes
from app.api.routes import auth, reports, ocr, soil, recommendations, history, assistant, report_store, hardware, resources, developer

Base.metadata.create_all(bind=engine)
ensure_user_columns()
ensure_soil_test_columns()
ReportBase.metadata.create_all(bind=report_engine)
ensure_report_columns(report_engine)
with SessionLocal() as _seed_db:
    seed_schemes(_seed_db)

app = FastAPI(title="Smart Soil Health API", version="2.0.0", description="Smart Soil Health Detection and Decision Support System")
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
Path(settings.model_dir).mkdir(parents=True, exist_ok=True)
Path(settings.rag_dir).mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

for router in (auth.router, reports.router, ocr.router, soil.router, recommendations.router, history.router, assistant.router, report_store.router, hardware.router, resources.router, developer.router):
    app.include_router(router, prefix="/api")

@app.get("/")
def root():
    return {"message":"Smart Soil Health API is running","docs":"/docs","features":["OCR","RAG","ML crop recommendation","ML fertilizer recommendation","separate soil-report database","serial soil probe integration"]}

@app.get("/health")
def health():
    return {"status":"ok"}
