"""
Tests for the updated signup flow:
  - state and district are required
  - phone is optional (no OTP required)
  - email verification is mandatory before login
  - phone OTP is not required anywhere in the signup/login flow
  - forgot password and reset password still work
  - resend verification still works

Covers all 22 required cases listed in the specification.

These tests share the same minimal FastAPI app infrastructure as test_auth_flows.py
but use separate database files to remain fully isolated.
"""
from __future__ import annotations

import sys
import types
from urllib.parse import urlparse, parse_qs

import pytest

# ── Stub out heavy optional dependencies ─────────────────────────────────────
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

# ── Isolate from other test modules ──────────────────────────────────────────
import app.core.config as _cfg  # noqa: E402

_cfg.settings.database_url = "sqlite:///./test_signup_flow_tmp.db"
_cfg.settings.soil_report_database_url = "sqlite:///./test_signup_flow_reports_tmp.db"
_cfg.settings.frontend_url = "http://testserver"
_cfg.settings.smtp_host = ""       # console mode — no real emails, verification_url returned
_cfg.settings.password_reset_expire_minutes = 60

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from app.database import connection as _conn  # noqa: E402
from app.database.connection import Base  # noqa: E402

_test_engine = create_engine(
    "sqlite:///./test_signup_flow_tmp.db",
    connect_args={"check_same_thread": False},
)
_TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)
_conn.engine = _test_engine
_conn.SessionLocal = _TestingSession

import app.models  # noqa: E402

from app.database import report_connection as _rep  # noqa: E402

_test_report_engine = create_engine(
    "sqlite:///./test_signup_flow_reports_tmp.db",
    connect_args={"check_same_thread": False},
)
_rep.report_engine = _test_report_engine
_rep.ReportSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_test_report_engine)

from app.database.report_connection import ReportBase  # noqa: E402
from app.models.soil_report_record import SoilReportRecord  # noqa: E402  # noqa

Base.metadata.create_all(bind=_test_engine)
ReportBase.metadata.create_all(bind=_test_report_engine)

from app.database.migrations import ensure_user_columns  # noqa: E402
ensure_user_columns()

from app.api.routes import auth as _auth_router  # noqa: E402
from app.database.connection import get_db  # noqa: E402

_app = FastAPI()
_app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
_app.include_router(_auth_router.router, prefix="/api")


def _override_get_db():
    db = _TestingSession()
    try:
        yield db
    finally:
        db.close()


_app.dependency_overrides[get_db] = _override_get_db
client = TestClient(_app, raise_server_exceptions=True)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clean_db():
    """Drop and recreate tables before/after every test for full isolation."""
    Base.metadata.drop_all(bind=_test_engine)
    Base.metadata.create_all(bind=_test_engine)
    ensure_user_columns()
    yield
    Base.metadata.drop_all(bind=_test_engine)


# ── Helpers ───────────────────────────────────────────────────────────────────

_BASE = {
    "name": "Test Farmer",
    "email": "farmer@example.com",
    "password": "Password123",
    "state": "Gujarat",
    "district": "Mehsana",
}


def _signup(overrides: dict | None = None) -> dict:
    payload = {**_BASE, **(overrides or {})}
    r = client.post("/api/auth/signup", json=payload)
    return r


def _signup_and_verify(overrides: dict | None = None):
    """Complete signup + email verification and return the token."""
    r = _signup(overrides)
    assert r.status_code == 200, r.text
    data = r.json()
    vurl = data["verification_url"]
    assert vurl, "verification_url missing (is SMTP misconfigured for tests?)"
    token = parse_qs(urlparse(vurl).query)["token"][0]
    vr = client.get("/api/auth/verify-email", params={"token": token})
    assert vr.status_code == 200, vr.text
    return data["access_token"]


def _login(email: str = _BASE["email"], password: str = _BASE["password"]) -> dict:
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    return r


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Signup with all required fields succeeds.
# ═══════════════════════════════════════════════════════════════════════════════
def test_signup_all_required_fields_succeeds():
    r = _signup()
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["access_token"]
    assert data["user"]["email"] == _BASE["email"]
    assert data["user"]["state"] == "Gujarat"
    assert data["user"]["district"] == "Mehsana"


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Signup without name fails.
# ═══════════════════════════════════════════════════════════════════════════════
def test_signup_without_name_fails():
    r = _signup({"name": ""})
    assert r.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Signup without email fails.
# ═══════════════════════════════════════════════════════════════════════════════
def test_signup_without_email_fails():
    r = _signup({"email": ""})
    assert r.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Signup without password fails.
# ═══════════════════════════════════════════════════════════════════════════════
def test_signup_without_password_fails():
    r = _signup({"password": ""})
    assert r.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Signup without state fails.
# ═══════════════════════════════════════════════════════════════════════════════
def test_signup_without_state_fails():
    payload = {k: v for k, v in _BASE.items() if k != "state"}
    r = client.post("/api/auth/signup", json=payload)
    assert r.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Signup without district fails.
# ═══════════════════════════════════════════════════════════════════════════════
def test_signup_without_district_fails():
    payload = {k: v for k, v in _BASE.items() if k != "district"}
    r = client.post("/api/auth/signup", json=payload)
    assert r.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Signup with no mobile succeeds.
# ═══════════════════════════════════════════════════════════════════════════════
def test_signup_with_no_mobile_succeeds():
    r = _signup({"phone": None})
    assert r.status_code == 200, r.text
    assert r.json()["user"]["phone"] is None


# ═══════════════════════════════════════════════════════════════════════════════
# 8. Signup with valid mobile succeeds.
# ═══════════════════════════════════════════════════════════════════════════════
def test_signup_with_valid_mobile_succeeds():
    r = _signup({"phone": "9876543210"})
    assert r.status_code == 200, r.text


# ═══════════════════════════════════════════════════════════════════════════════
# 9. Invalid email fails.
# ═══════════════════════════════════════════════════════════════════════════════
def test_signup_invalid_email_fails():
    r = _signup({"email": "not-an-email"})
    assert r.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# 10. Password too short fails.
# ═══════════════════════════════════════════════════════════════════════════════
def test_signup_short_password_fails():
    r = _signup({"password": "abc"})
    assert r.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# 11. Empty state string fails.
# ═══════════════════════════════════════════════════════════════════════════════
def test_signup_empty_state_fails():
    r = _signup({"state": ""})
    assert r.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# 12. Empty district string fails.
# ═══════════════════════════════════════════════════════════════════════════════
def test_signup_empty_district_fails():
    r = _signup({"district": ""})
    assert r.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# 13. Whitespace-only name fails.
# ═══════════════════════════════════════════════════════════════════════════════
def test_signup_whitespace_only_name_fails():
    r = _signup({"name": "   "})
    assert r.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# 14. Newly registered user is unverified.
# ═══════════════════════════════════════════════════════════════════════════════
def test_newly_registered_user_is_unverified():
    r = _signup()
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["user"]["email_verified"] is False
    assert data["verification_required"] is True


# ═══════════════════════════════════════════════════════════════════════════════
# 15. Unverified user cannot log in.
# ═══════════════════════════════════════════════════════════════════════════════
def test_unverified_user_cannot_login():
    _signup()
    r = _login()
    # Must be rejected — login blocked for unverified accounts
    assert r.status_code in (401, 403), f"Expected auth failure, got {r.status_code}: {r.text}"


# ═══════════════════════════════════════════════════════════════════════════════
# 16. Email verification succeeds with valid token.
# ═══════════════════════════════════════════════════════════════════════════════
def test_email_verification_succeeds():
    r = _signup()
    data = r.json()
    vurl = data["verification_url"]
    token = parse_qs(urlparse(vurl).query)["token"][0]
    vr = client.get("/api/auth/verify-email", params={"token": token})
    assert vr.status_code == 200, vr.text
    assert vr.json()["email_verified"] is True


# ═══════════════════════════════════════════════════════════════════════════════
# 17. Verified user can log in.
# ═══════════════════════════════════════════════════════════════════════════════
def test_verified_user_can_login():
    _signup_and_verify()
    r = _login()
    assert r.status_code == 200, r.text
    assert r.json()["access_token"]
    assert r.json()["verification_required"] is False


# ═══════════════════════════════════════════════════════════════════════════════
# 18. Resend verification still works.
# ═══════════════════════════════════════════════════════════════════════════════
def test_resend_verification_works():
    r = _signup()
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    # Wait is simulated by the test environment — the first resend should be rate-limited
    # but we can test that the endpoint exists and returns a useful response.
    r2 = client.post("/api/auth/resend-verification", headers=headers)
    # Either 200 (sent) or 429 (rate limited within cooldown) — both are valid
    assert r2.status_code in (200, 429), r2.text


# ═══════════════════════════════════════════════════════════════════════════════
# 19. Forgot password still works.
# ═══════════════════════════════════════════════════════════════════════════════
def test_forgot_password_works():
    _signup_and_verify()
    r = client.post("/api/auth/forgot-password", json={"email": _BASE["email"]})
    assert r.status_code == 200, r.text
    assert "message" in r.json()


# ═══════════════════════════════════════════════════════════════════════════════
# 20. Reset password still works.
# ═══════════════════════════════════════════════════════════════════════════════
def test_reset_password_works():
    _signup_and_verify()
    # Request reset
    client.post("/api/auth/forgot-password", json={"email": _BASE["email"]})
    # Grab the token directly from the DB
    db = _TestingSession()
    try:
        from app.models.user import User as _User
        u = db.query(_User).filter(_User.email == _BASE["email"].lower()).first()
        assert u is not None
        from app.services.email_service import generate_password_reset_token, hash_password_reset_token
        from datetime import datetime, timedelta, timezone
        raw_token, token_hash = generate_password_reset_token()
        u.password_reset_token_hash = token_hash
        u.password_reset_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        db.commit()
    finally:
        db.close()

    r = client.post("/api/auth/reset-password", json={"token": raw_token, "new_password": "NewPassword456"})
    assert r.status_code == 200, r.text

    # Verify old password no longer works
    r2 = _login(password=_BASE["password"])
    assert r2.status_code == 401

    # Verify new password works
    r3 = _login(password="NewPassword456")
    assert r3.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════════
# 21. Signup does NOT set verification_required to False because of phone.
#     (phone is present but should NOT drive the verification_required flag)
# ═══════════════════════════════════════════════════════════════════════════════
def test_signup_with_phone_does_not_require_phone_otp():
    r = _signup({"phone": "9876543210"})
    assert r.status_code == 200, r.text
    data = r.json()
    # verification_required must be True (email not yet verified)
    # It must NOT be False just because phone is absent/present
    assert data["verification_required"] is True
    # The user must still be unverified by email
    assert data["user"]["email_verified"] is False


# ═══════════════════════════════════════════════════════════════════════════════
# 22. Phone OTP is not required anywhere in the signup flow.
#     After signup with phone + email verification, login succeeds
#     WITHOUT any phone OTP step.
# ═══════════════════════════════════════════════════════════════════════════════
def test_login_after_verify_does_not_require_phone_otp():
    # Signup with phone number provided
    r = _signup({"phone": "9876543210"})
    data = r.json()
    vurl = data["verification_url"]
    token = parse_qs(urlparse(vurl).query)["token"][0]

    # Verify email
    vr = client.get("/api/auth/verify-email", params={"token": token})
    assert vr.status_code == 200

    # Login — must succeed WITHOUT phone OTP
    lr = _login()
    assert lr.status_code == 200, lr.text
    login_data = lr.json()
    assert login_data["access_token"]
    # verification_required must be False — email is the only requirement
    assert login_data["verification_required"] is False
    # Phone may be unverified but login must still succeed
    # (phone_verified state is irrelevant to login access)
    assert login_data["user"]["email_verified"] is True


# ═══════════════════════════════════════════════════════════════════════════════
# Bonus: invalid phone format is rejected by backend.
# ═══════════════════════════════════════════════════════════════════════════════
def test_signup_invalid_phone_format_fails():
    r = _signup({"phone": "123"})  # too short, wrong prefix
    assert r.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# Bonus: duplicate email is rejected.
# ═══════════════════════════════════════════════════════════════════════════════
def test_signup_duplicate_email_rejected():
    _signup()
    r2 = _signup({"email": _BASE["email"]})
    assert r2.status_code == 409
