from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

connect_args = {"check_same_thread": False} if settings.soil_report_database_url.startswith("sqlite") else {}
report_engine = create_engine(settings.soil_report_database_url, connect_args=connect_args)
ReportSessionLocal = sessionmaker(bind=report_engine, autoflush=False, autocommit=False)
ReportBase = declarative_base()

def get_report_db():
    db = ReportSessionLocal()
    try:
        yield db
    finally:
        db.close()
