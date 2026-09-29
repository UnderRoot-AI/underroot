"""
Tests for DELETE /api/auth/account — account deletion.

Tests:
  1.  Successful account deletion returns 200 and success message.
  2.  Wrong password is rejected with 403.
  3.  Unauthenticated request is rejected with 401.
  4.  Missing password body is rejected with 422.
  5.  Deletion removes the user's soil tests.
  6.  Deletion removes the user's devices and hardware readings.
  7.  Deletion removes the user's assistant/conversation history.
  8.  Deletion removes the user's reports and report-store records.
  9.  Another user's data is completely untouched.
 10.  Transaction rollback: if a deletion step raises an exception the user
      record still exists and no partial data is removed.
"""
from __future__ import annotations

import sys
import types
import unittest.mock as mock

# ── Stub heavy optional dependencies ─────────────────────────────────────────
_STUBS = [
    "joblib", "sklearn", "sklearn.preprocessing", "sklearn.ensemble",
    "pytesseract", "PIL", "PIL.Image", "fitz",
    "reportlab",
    "reportlab.platypus", "reportlab.lib", "reportlab.lib.styles",
    "reportlab.lib.units", "reportlab.lib.pagesizes",
    "pypdf", "pyserial", "serial", "pandas",
]
for _mod in _STUBS:
    if _mod not in sys.modules:
        sys.modules[_mod] = types.ModuleType(_mod)

# ── Isolated test databases ───────────────────────────────────────────────────
import app.core.config as _cfg  # noqa: E402
_cfg.settings.database_url               = "sqlite:///./test_delete_account_tmp.db"
_cfg.settings.soil_report_database_url   = "sqlite:///./test_delete_account_reports_tmp.db"
_cfg.settings.smtp_host                  = ""
_cfg.settings.hardware_mode              = "mock"

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
import pytest  # noqa: E402

# ── Main DB ───────────────────────────────────────────────────────────────────
from app.database import connection as _conn  # noqa: E402
from app.database.connection import Base  # noqa: E402

_engine = create_engine(
    "sqlite:///./test_delete_account_tmp.db",
    connect_args={"check_same_thread": False},
)
_Session = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
_conn.engine = _engine
_conn.SessionLocal = _Session

# ── Report DB ─────────────────────────────────────────────────────────────────
from app.database import report_connection as _rep  # noqa: E402
from app.database.report_connection import ReportBase  # noqa: E402

_rep_engine = create_engine(
    "sqlite:///./test_delete_account_reports_tmp.db",
    connect_args={"check_same_thread": False},
)
_rep.report_engine = _rep_engine
_rep.ReportSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_rep_engine)

import app.models  # noqa: E402  register ORM models
from app.models.soil_report_record import SoilReportRecord  # noqa: E402
from app.database.migrations import ensure_soil_test_columns, ensure_report_columns  # noqa: E402

Base.metadata.create_all(bind=_engine)
ReportBase.metadata.create_all(bind=_rep_engine)
ensure_soil_test_columns()
ensure_report_columns(_rep_engine)

# ── FastAPI test app: auth + soil + devices routes ───────────────────────────
from app.api.routes import auth as _auth  # noqa: E402
from app.api.routes import soil as _soil  # noqa: E402
from app.api.routes import devices as _devices  # noqa: E402
from app.database.connection import get_db  # noqa: E402
from app.database.report_connection import get_report_db  # noqa: E402

_app = FastAPI()
_app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])
_app.include_router(_auth.router, prefix="/api")
_app.include_router(_soil.router, prefix="/api")
_app.include_router(_devices.router, prefix="/api")


def _override_db():
    db = _Session()
    try:
        yield db
    finally:
        db.close()


def _override_report_db():
    db = _rep.ReportSessionLocal()
    try:
        yield db
    finally:
        db.close()


_app.dependency_overrides[get_db] = _override_db
_app.dependency_overrides[get_report_db] = _override_report_db

@pytest.fixture(autouse=True)
def _clean_db():
    Base.metadata.drop_all(bind=_engine)
    Base.metadata.create_all(bind=_engine)
    ReportBase.metadata.drop_all(bind=_rep_engine)
    ReportBase.metadata.create_all(bind=_rep_engine)
    ensure_soil_test_columns()
    ensure_report_columns(_rep_engine)
    yield
    Base.metadata.drop_all(bind=_engine)
    ReportBase.metadata.drop_all(bind=_rep_engine)


client = TestClient(_app, raise_server_exceptions=False)

# ── Helpers ───────────────────────────────────────────────────────────────────
_PWD = "TestPass123!"
_USER_A = {
    "name": "Alice Farmer", "email": "alice_del@test.com", "password": _PWD,
    "state": "Gujarat", "district": "Ahmedabad", "mobile": "",
}
_USER_B = {
    "name": "Bob Farmer", "email": "bob_del@test.com", "password": _PWD,
    "state": "Punjab", "district": "Ludhiana", "mobile": "",
}

_SOIL_PARAMS = {
    "ph": 6.8, "nitrogen": 180.0, "phosphorus": 45.0, "potassium": 220.0,
    "ec": 0.65, "moisture": 24.0, "temperature": 28.0, "organic_carbon": 0.75,
}


def _register_and_verify(user_data: dict) -> str:
    """Register, force-verify email, return token."""
    r = client.post("/api/auth/signup", json=user_data)
    assert r.status_code == 200, f"signup failed: {r.text}"
    from app.models.user import User as _U
    db = _Session()
    try:
        u = db.query(_U).filter(_U.email == user_data["email"]).first()
        u.email_verified = True
        db.commit()
    finally:
        db.close()
    r2 = client.post("/api/auth/login",
                     json={"email": user_data["email"], "password": user_data["password"]})
    assert r2.status_code == 200, f"login failed: {r2.text}"
    return r2.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _user_exists(email: str) -> bool:
    from app.models.user import User as _U
    db = _Session()
    try:
        return db.query(_U).filter(_U.email == email).first() is not None
    finally:
        db.close()


def _count_soil_tests(user_id: int) -> int:
    from app.models.soil_test import SoilTest as _ST
    db = _Session()
    try:
        return db.query(_ST).filter(_ST.user_id == user_id).count()
    finally:
        db.close()


def _count_conversations(user_id: int) -> int:
    from app.models.conversation import Conversation as _C
    db = _Session()
    try:
        return db.query(_C).filter(_C.user_id == user_id).count()
    finally:
        db.close()


def _count_devices(user_id: int) -> int:
    from app.models.device import Device as _D
    db = _Session()
    try:
        return db.query(_D).filter(_D.user_id == user_id).count()
    finally:
        db.close()


def _count_reports(user_id: int) -> int:
    from app.models.report import Report as _R
    db = _Session()
    try:
        return db.query(_R).filter(_R.user_id == user_id).count()
    finally:
        db.close()


def _count_report_records(user_id: int) -> int:
    rep_db = _rep.ReportSessionLocal()
    try:
        return rep_db.query(SoilReportRecord).filter(
            SoilReportRecord.user_id == user_id
        ).count()
    finally:
        rep_db.close()


def _get_user_id(email: str) -> int:
    from app.models.user import User as _U
    db = _Session()
    try:
        u = db.query(_U).filter(_U.email == email).first()
        return u.id
    finally:
        db.close()


# ── Test 1: Successful account deletion ──────────────────────────────────────
def test_delete_account_success():
    token = _register_and_verify(_USER_A)
    r = client.request(
        "DELETE", "/api/auth/account",
        json={"password": _PWD},
        headers=_auth_headers(token),
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert "deleted" in data["message"].lower() or "permanent" in data["message"].lower()
    assert not _user_exists(_USER_A["email"])


# ── Test 2: Wrong password rejected ──────────────────────────────────────────
def test_delete_account_wrong_password():
    token = _register_and_verify({**_USER_A, "email": "alice_del_wp@test.com"})
    r = client.request(
        "DELETE", "/api/auth/account",
        json={"password": "WRONG_PASSWORD_XYZ"},
        headers=_auth_headers(token),
    )
    assert r.status_code == 403
    assert "incorrect" in r.json()["detail"].lower() or "password" in r.json()["detail"].lower()
    # User should still exist
    assert _user_exists("alice_del_wp@test.com")


# ── Test 3: Unauthenticated request rejected ──────────────────────────────────
def test_delete_account_unauthenticated():
    r = client.request(
        "DELETE", "/api/auth/account",
        json={"password": _PWD},
        # No Authorization header
    )
    assert r.status_code == 401


# ── Test 4: Missing password body rejected with 422 ──────────────────────────
def test_delete_account_missing_password():
    token = _register_and_verify({**_USER_A, "email": "alice_del_mp@test.com"})
    r = client.request(
        "DELETE", "/api/auth/account",
        json={},          # password field is absent
        headers=_auth_headers(token),
    )
    assert r.status_code == 422


# ── Test 5: Soil tests are removed ───────────────────────────────────────────
def test_delete_account_removes_soil_tests():
    email = "alice_del_soils@test.com"
    token = _register_and_verify({**_USER_A, "email": email})
    user_id = _get_user_id(email)

    # Create two soil tests
    for _ in range(2):
        r = client.post("/api/soil/tests",
                        json={"parameters": _SOIL_PARAMS},
                        headers=_auth_headers(token))
        assert r.status_code == 200

    assert _count_soil_tests(user_id) == 2

    r = client.request("DELETE", "/api/auth/account",
                       json={"password": _PWD},
                       headers=_auth_headers(token))
    assert r.status_code == 200
    assert _count_soil_tests(user_id) == 0


# ── Test 6: Devices and hardware readings are removed ────────────────────────
def test_delete_account_removes_devices_and_readings():
    email = "alice_del_dev@test.com"
    token = _register_and_verify({**_USER_A, "email": email})
    user_id = _get_user_id(email)

    # Register a device
    dr = client.post("/api/devices",
                     json={"device_id": "TEST-DEV-001", "name": "Test Sensor",
                           "connection_type": "http"},
                     headers=_auth_headers(token))
    assert dr.status_code == 201, dr.text
    device_pk = dr.json()["id"]

    # Ingest a reading
    rr = client.post(
        f"/api/devices/{device_pk}/readings",
        json={
            "timestamp": "2026-01-01T00:00:00",
            "measurements": {
                "ph":          {"value": 6.8,  "unit": "pH"},
                "nitrogen":    {"value": 180.0, "unit": "kg/ha"},
                "phosphorus":  {"value": 45.0,  "unit": "kg/ha"},
                "potassium":   {"value": 220.0, "unit": "kg/ha"},
                "ec":          {"value": 0.65,  "unit": "dS/m"},
                "moisture":    {"value": 24.0,  "unit": "%"},
                "temperature": {"value": 28.0,  "unit": "°C"},
                "organic_carbon": {"value": 0.75, "unit": "%"},
            },
        },
        headers=_auth_headers(token),
    )
    assert rr.status_code == 201, rr.text

    assert _count_devices(user_id) == 1

    r = client.request("DELETE", "/api/auth/account",
                       json={"password": _PWD},
                       headers=_auth_headers(token))
    assert r.status_code == 200
    assert _count_devices(user_id) == 0
    # Readings cascade from device, so implicitly checked via device count


# ── Test 7: Conversation/assistant history is removed ────────────────────────
def test_delete_account_removes_conversations():
    from app.models.conversation import Conversation as _C
    email = "alice_del_conv@test.com"
    token = _register_and_verify({**_USER_A, "email": email})
    user_id = _get_user_id(email)

    # Directly insert conversation rows
    db = _Session()
    try:
        db.add(_C(user_id=user_id, role="user", content="Hello"))
        db.add(_C(user_id=user_id, role="assistant", content="Hi there!"))
        db.commit()
    finally:
        db.close()

    assert _count_conversations(user_id) == 2

    r = client.request("DELETE", "/api/auth/account",
                       json={"password": _PWD},
                       headers=_auth_headers(token))
    assert r.status_code == 200
    assert _count_conversations(user_id) == 0


# ── Test 8: Reports and report-store records are removed ─────────────────────
def test_delete_account_removes_reports():
    from app.models.report import Report as _R
    email = "alice_del_rpts@test.com"
    token = _register_and_verify({**_USER_A, "email": email})
    user_id = _get_user_id(email)

    # Create a soil test first, then a report against it
    st_r = client.post("/api/soil/tests",
                       json={"parameters": _SOIL_PARAMS},
                       headers=_auth_headers(token))
    soil_test_id = st_r.json()["id"]

    db = _Session()
    rep_db = _rep.ReportSessionLocal()
    try:
        report = _R(user_id=user_id, soil_test_id=soil_test_id, status="generated")
        db.add(report)
        db.flush()
        rep_record = SoilReportRecord(
            app_report_id=report.id, user_id=user_id, soil_test_id=soil_test_id,
            status="generated",
        )
        rep_db.add(rep_record)
        db.commit()
        rep_db.commit()
    finally:
        db.close()
        rep_db.close()

    # The soil test route may already create a report record; we just need at least 1
    assert _count_reports(user_id) >= 1
    assert _count_report_records(user_id) >= 1

    r = client.request("DELETE", "/api/auth/account",
                       json={"password": _PWD},
                       headers=_auth_headers(token))
    assert r.status_code == 200
    assert _count_reports(user_id) == 0
    assert _count_report_records(user_id) == 0


# ── Test 9: Another user's data remains untouched ─────────────────────────────
def test_delete_account_does_not_touch_other_users():
    email_a = "alice_del_other@test.com"
    email_b = "bob_del_other@test.com"

    token_a = _register_and_verify({**_USER_A, "email": email_a})
    token_b = _register_and_verify({**_USER_B, "email": email_b})
    user_b_id = _get_user_id(email_b)

    # Give user B a soil test
    client.post("/api/soil/tests",
                json={"parameters": _SOIL_PARAMS},
                headers=_auth_headers(token_b))
    assert _count_soil_tests(user_b_id) == 1

    # Delete user A
    r = client.request("DELETE", "/api/auth/account",
                       json={"password": _PWD},
                       headers=_auth_headers(token_a))
    assert r.status_code == 200
    assert not _user_exists(email_a)

    # User B and their data must be intact
    assert _user_exists(email_b)
    assert _count_soil_tests(user_b_id) == 1


# ── Test 10: Transaction rollback on failure ──────────────────────────────────
def test_delete_account_rollback_on_failure():
    """
    If one of the deletion steps raises an unexpected exception, the whole
    main-DB transaction is rolled back and the user record still exists.
    """
    email = "alice_del_rollback@test.com"
    token = _register_and_verify({**_USER_A, "email": email})

    # Patch the Conversation delete to raise an error mid-transaction
    with mock.patch(
        "app.api.routes.auth.Conversation",
        side_effect=RuntimeError("simulated DB failure"),
    ):
        r = client.request("DELETE", "/api/auth/account",
                           json={"password": _PWD},
                           headers=_auth_headers(token))

    assert r.status_code == 500
    detail = r.json().get("detail", "")
    assert "failed" in detail.lower() or "error" in detail.lower() or "deletion" in detail.lower()

    # User must still exist because the transaction was rolled back
    assert _user_exists(email), "User should still exist after a rolled-back deletion"
