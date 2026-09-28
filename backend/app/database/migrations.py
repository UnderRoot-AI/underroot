from sqlalchemy import inspect, text
from app.database.connection import engine

# Lightweight compatibility migration for the SQLite development database.
def ensure_soil_test_columns():
    """Add hardware provenance columns to soil_tests if they do not exist."""
    if not engine.url.get_backend_name().startswith("sqlite"):
        return
    inspector = inspect(engine)
    if "soil_tests" not in inspector.get_table_names():
        return
    existing = {c["name"] for c in inspector.get_columns("soil_tests")}
    additions = {
        "source": "VARCHAR(40) DEFAULT 'manual'",
        "device_id": "VARCHAR(120)",
    }
    with engine.begin() as conn:
        for name, typ in additions.items():
            if name not in existing:
                conn.execute(text(f"ALTER TABLE soil_tests ADD COLUMN {name} {typ}"))

def ensure_user_columns():
    if not engine.url.get_backend_name().startswith("sqlite"):
        return
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return
    existing = {c["name"] for c in inspector.get_columns("users")}
    additions = {
        "state": "VARCHAR(120)",
        "district": "VARCHAR(120)",
        "city_village": "VARCHAR(120)",
        "email_verified": "BOOLEAN DEFAULT 0",
        "phone_verified": "BOOLEAN DEFAULT 0",
        "phone_otp_hash": "VARCHAR(128)",
        "phone_otp_expires_at": "DATETIME",
        "phone_otp_attempts": "INTEGER DEFAULT 0",
        "verification_token_hash": "VARCHAR(128)",
        "verification_expires_at": "DATETIME",
        "password_reset_token_hash": "VARCHAR(128)",
        "password_reset_expires_at": "DATETIME",
        "last_login_at": "DATETIME",
        "login_count": "INTEGER DEFAULT 0",
    }
    with engine.begin() as conn:
        for name, typ in additions.items():
            if name not in existing:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {name} {typ}"))

def ensure_report_columns(report_engine):
    if not report_engine.url.get_backend_name().startswith("sqlite"):
        return
    inspector = inspect(report_engine)
    if "soil_report_records" not in inspector.get_table_names():
        return
    existing = {c["name"] for c in inspector.get_columns("soil_report_records")}
    with report_engine.begin() as conn:
        if "soil_test_id" not in existing:
            conn.execute(text("ALTER TABLE soil_report_records ADD COLUMN soil_test_id INTEGER"))
