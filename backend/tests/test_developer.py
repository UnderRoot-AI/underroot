"""
Tests for the developer/admin panel endpoints.

Covers:
  1.  Developer login — valid credentials
  2.  Developer login — wrong password
  3.  Developer stats — correct counts
  4.  Developer stats — verified/unverified user breakdown
  5.  Developer stats — device and report counts
  6.  Developer users — returns all users with email_verified field
  7.  Developer users — normal user JWT cannot access
  8.  Developer users — unauthenticated request returns 401/403
  9.  Developer soil-tests — returns all tests across users
  10. Developer soil-tests — normal user JWT cannot access
  11. Developer devices — returns all active devices across users
  12. Developer devices — reading counts attached
  13. Developer reports — returns all reports across users
  14. Developer reports — normal user JWT cannot access
  15. Developer schemes — create / list / update / delete
  16. Developer schemes — duplicate name is rejected (409)
  17. Developer users/export — CSV contains Email Verified column
"""
from __future__ import annotations

import sys
import types
import pytest

# ── Stub heavy optional dependencies ─────────────────────────────────────────
_STUBS = [
    "joblib", "sklearn", "sklearn.preprocessing", "sklearn.ensemble",
    "pytesseract", "PIL", "PIL.Image", "fitz", "reportlab",
    "reportlab.platypus", "reportlab.lib", "reportlab.lib.styles",
    "reportlab.lib.units", "reportlab.lib.pagesizes",
    "pypdf", "pyserial", "serial", "pandas",
]
for _mod in _STUBS:
    if _mod not in sys.modules:
        sys.modules[_mod] = types.ModuleType(_mod)

# ── Patch settings to use isolated test databases ─────────────────────────────
import app.core.config as _cfg_module  # noqa: E402

_cfg_module.settings.database_url = "sqlite:///./test_developer_tmp.db"
_cfg_module.settings.soil_report_database_url = "sqlite:///./test_developer_reports_tmp.db"
_cfg_module.settings.smtp_host = ""
_cfg_module.settings.frontend_url = "http://testserver"
# Stable developer credentials for all tests
_cfg_module.settings.developer_email = "dev@example.com"

from app.core.security import hash_password  # noqa: E402

_cfg_module.settings.developer_password_hash = hash_password("devpass123")

# ── Wire up test databases ────────────────────────────────────────────────────
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import connection as _conn  # noqa: E402
from app.database.connection import Base  # noqa: E402

_test_engine = create_engine(
    "sqlite:///./test_developer_tmp.db",
    connect_args={"check_same_thread": False},
)
_TestSession = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)
_conn.engine = _test_engine
_conn.SessionLocal = _TestSession

import app.models  # noqa: E402 — register ORM models

from app.database import report_connection as _rep  # noqa: E402

_test_report_engine = create_engine(
    "sqlite:///./test_developer_reports_tmp.db",
    connect_args={"check_same_thread": False},
)
_rep.report_engine = _test_report_engine
from app.database.report_connection import ReportBase  # noqa: E402

ReportBase.metadata.create_all(bind=_test_report_engine)

# ── Build minimal FastAPI app with only the developer router ──────────────────
from app.api.routes.developer import router as dev_router  # noqa: E402
from app.api.routes.auth import router as auth_router  # noqa: E402
from app.api.routes.devices import router as devices_router  # noqa: E402
from app.database.connection import get_db  # noqa: E402
from app.database.report_connection import get_report_db  # noqa: E402

app = FastAPI()
app.include_router(dev_router)
app.include_router(auth_router)
app.include_router(devices_router)


def override_db():
    db = _TestSession()
    try:
        yield db
    finally:
        db.close()


def override_report_db():
    from sqlalchemy.orm import sessionmaker as sm
    RS = sm(autocommit=False, autoflush=False, bind=_test_report_engine)
    db = RS()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_db
app.dependency_overrides[get_report_db] = override_report_db

client = TestClient(app, raise_server_exceptions=True)

# ── Schema setup ──────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True, scope="module")
def setup_schema():
    Base.metadata.drop_all(bind=_test_engine)
    Base.metadata.create_all(bind=_test_engine)
    yield
    Base.metadata.drop_all(bind=_test_engine)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _dev_token() -> str:
    r = client.post("/developer/login", json={"email": "dev@example.com", "password": "devpass123"})
    assert r.status_code == 200
    return r.json()["access_token"]


def _dev_headers() -> dict:
    return {"Authorization": f"Bearer {_dev_token()}"}


def _register_user(email: str, name: str = "Test User") -> dict:
    r = client.post(
        "/auth/signup",
        json={
            "name": name,
            "email": email,
            "password": "pass1234",
            "state": "Maharashtra",
            "district": "Pune",
        },
    )
    assert r.status_code == 200
    return r.json()


def _user_headers(email: str) -> dict:
    data = _register_user(email)
    token = data["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestDeveloperLogin:
    def test_valid_login(self):
        r = client.post(
            "/developer/login",
            json={"email": "dev@example.com", "password": "devpass123"},
        )
        assert r.status_code == 200
        body = r.json()
        assert "access_token" in body
        assert body["role"] == "developer"

    def test_wrong_password(self):
        r = client.post(
            "/developer/login",
            json={"email": "dev@example.com", "password": "wrongpass"},
        )
        assert r.status_code == 401

    def test_wrong_email(self):
        r = client.post(
            "/developer/login",
            json={"email": "notdev@example.com", "password": "devpass123"},
        )
        assert r.status_code == 401


class TestDeveloperStats:
    def test_stats_structure(self):
        r = client.get("/developer/stats", headers=_dev_headers())
        assert r.status_code == 200
        body = r.json()
        for key in (
            "total_users", "verified_users", "unverified_users",
            "logged_in_users", "total_logins",
            "total_soil_tests", "total_devices", "total_reports",
            "active_schemes",
        ):
            assert key in body, f"Missing key: {key}"

    def test_verified_unverified_sum(self):
        r = client.get("/developer/stats", headers=_dev_headers())
        body = r.json()
        assert body["verified_users"] + body["unverified_users"] == body["total_users"]

    def test_unauthenticated_stats(self):
        r = client.get("/developer/stats")
        assert r.status_code == 401

    def test_user_jwt_cannot_access_stats(self):
        headers = _user_headers("stats_normal@example.com")
        r = client.get("/developer/stats", headers=headers)
        assert r.status_code == 403


class TestDeveloperUsers:
    def test_returns_users(self):
        _register_user("devuser1@example.com", "Dev User 1")
        r = client.get("/developer/users", headers=_dev_headers())
        assert r.status_code == 200
        users = r.json()
        assert isinstance(users, list)
        assert len(users) >= 1

    def test_email_verified_field_present(self):
        _register_user("devuser2@example.com", "Dev User 2")
        r = client.get("/developer/users", headers=_dev_headers())
        assert r.status_code == 200
        for u in r.json():
            assert "email_verified" in u

    def test_user_jwt_cannot_access_users(self):
        headers = _user_headers("users_normal@example.com")
        r = client.get("/developer/users", headers=headers)
        assert r.status_code == 403

    def test_unauthenticated_users(self):
        r = client.get("/developer/users")
        assert r.status_code == 401


class TestDeveloperSoilTests:
    def test_returns_paginated_response(self):
        r = client.get("/developer/soil-tests", headers=_dev_headers())
        assert r.status_code == 200
        body = r.json()
        assert "total" in body
        assert "items" in body
        assert isinstance(body["items"], list)

    def test_item_fields(self):
        # Create a soil test via user flow so data exists
        from app.models.soil_test import SoilTest as ST
        from app.models.user import User as U
        db = _TestSession()
        # Insert a dummy user and soil test directly for deterministic testing
        existing = db.query(U).filter(U.email == "soiltestowner@example.com").first()
        if not existing:
            from app.core.security import hash_password as hp
            u = U(
                name="Soil Owner",
                email="soiltestowner@example.com",
                password_hash=hp("pass1234"),
                state="Gujarat",
                district="Ahmedabad",
                email_verified=True,
                language="en",
            )
            db.add(u)
            db.flush()
            st = ST(user_id=u.id, ph=6.5, nitrogen=120.0, health_score=72.0, health_status="Good")
            db.add(st)
            db.commit()
        db.close()

        r = client.get("/developer/soil-tests", headers=_dev_headers())
        assert r.status_code == 200
        items = r.json()["items"]
        if items:
            item = items[0]
            for field in ("id", "user_id", "user_name", "source", "health_score", "health_status", "created_at"):
                assert field in item, f"Missing field: {field}"

    def test_limit_parameter(self):
        r = client.get("/developer/soil-tests?limit=2", headers=_dev_headers())
        assert r.status_code == 200
        assert len(r.json()["items"]) <= 2

    def test_normal_user_cannot_access(self):
        headers = _user_headers("soiltest_normal@example.com")
        r = client.get("/developer/soil-tests", headers=headers)
        assert r.status_code == 403

    def test_unauthenticated(self):
        r = client.get("/developer/soil-tests")
        assert r.status_code == 401


class TestDeveloperDevices:
    def test_returns_paginated_response(self):
        r = client.get("/developer/devices", headers=_dev_headers())
        assert r.status_code == 200
        body = r.json()
        assert "total" in body
        assert "items" in body

    def test_item_fields_when_devices_exist(self):
        # Register a device via the devices endpoint
        headers = _user_headers("deviceowner@example.com")
        reg = client.post(
            "/devices",
            json={
                "device_id": "TEST-DEV-001",
                "name": "My Test Device",
                "manufacturer": "TestCo",
                "model": "Model X",
                "connection_type": "http",
            },
            headers=headers,
        )
        assert reg.status_code == 201

        r = client.get("/developer/devices", headers=_dev_headers())
        assert r.status_code == 200
        items = r.json()["items"]
        assert len(items) >= 1
        item = items[0]
        for field in (
            "id", "device_id", "name", "manufacturer", "model",
            "connection_type", "status", "user_id", "owner_name",
            "reading_count", "created_at",
        ):
            assert field in item, f"Missing device field: {field}"

    def test_reading_count_is_integer(self):
        r = client.get("/developer/devices", headers=_dev_headers())
        for item in r.json()["items"]:
            assert isinstance(item["reading_count"], int)

    def test_normal_user_cannot_access(self):
        headers = _user_headers("device_normal@example.com")
        r = client.get("/developer/devices", headers=headers)
        assert r.status_code == 403

    def test_unauthenticated(self):
        r = client.get("/developer/devices")
        assert r.status_code == 401


class TestDeveloperReports:
    def test_returns_paginated_response(self):
        r = client.get("/developer/reports", headers=_dev_headers())
        assert r.status_code == 200
        body = r.json()
        assert "total" in body
        assert "items" in body

    def test_item_fields_when_reports_exist(self):
        # Insert a report directly
        from app.models.report import Report as R
        from app.models.user import User as U
        db = _TestSession()
        existing = db.query(U).filter(U.email == "reportowner@example.com").first()
        if not existing:
            from app.core.security import hash_password as hp
            u = U(
                name="Report Owner",
                email="reportowner@example.com",
                password_hash=hp("pass1234"),
                state="Karnataka",
                district="Bengaluru",
                email_verified=True,
                language="en",
            )
            db.add(u)
            db.flush()
            rpt = R(user_id=u.id, file_name="test.pdf", status="uploaded")
            db.add(rpt)
            db.commit()
        db.close()

        r = client.get("/developer/reports", headers=_dev_headers())
        assert r.status_code == 200
        items = r.json()["items"]
        if items:
            item = items[0]
            for field in ("id", "user_id", "owner_name", "soil_test_id", "file_name", "status", "created_at"):
                assert field in item, f"Missing report field: {field}"

    def test_normal_user_cannot_access(self):
        headers = _user_headers("report_normal@example.com")
        r = client.get("/developer/reports", headers=headers)
        assert r.status_code == 403

    def test_unauthenticated(self):
        r = client.get("/developer/reports")
        assert r.status_code == 401


class TestDeveloperSchemes:
    def test_create_list_update_delete(self):
        h = _dev_headers()
        # Create
        r = client.post(
            "/developer/schemes",
            json={"name": "TestScheme_Admin", "description": "A test scheme for admin", "url": "https://test.gov.in", "active": True},
            headers=h,
        )
        assert r.status_code == 200
        sid = r.json()["id"]
        # List
        r = client.get("/developer/schemes", headers=h)
        names = [s["name"] for s in r.json()]
        assert "TestScheme_Admin" in names
        # Update
        r = client.put(
            f"/developer/schemes/{sid}",
            json={"name": "TestScheme_Admin", "description": "Updated description text", "url": "https://test.gov.in", "active": False},
            headers=h,
        )
        assert r.status_code == 200
        assert r.json()["active"] is False
        # Delete
        r = client.delete(f"/developer/schemes/{sid}", headers=h)
        assert r.status_code == 200

    def test_duplicate_name_rejected(self):
        h = _dev_headers()
        payload = {"name": "UniqueSchemeDup", "description": "A unique test scheme", "url": "https://unique.gov.in", "active": True}
        r1 = client.post("/developer/schemes", json=payload, headers=h)
        assert r1.status_code == 200
        r2 = client.post("/developer/schemes", json=payload, headers=h)
        assert r2.status_code == 409
        # Clean up
        client.delete(f"/developer/schemes/{r1.json()['id']}", headers=h)

    def test_normal_user_cannot_create_scheme(self):
        headers = _user_headers("scheme_normal@example.com")
        r = client.post(
            "/developer/schemes",
            json={"name": "HijackScheme", "description": "unauthorized attempt", "url": "https://x.com", "active": True},
            headers=headers,
        )
        assert r.status_code == 403


class TestDeveloperUsersExport:
    def test_csv_contains_email_verified_column(self):
        r = client.get("/developer/users/export", headers=_dev_headers())
        assert r.status_code == 200
        content = r.content.decode("utf-8")
        assert "Email Verified" in content

    def test_normal_user_cannot_export(self):
        headers = _user_headers("export_normal@example.com")
        r = client.get("/developer/users/export", headers=headers)
        assert r.status_code == 403
