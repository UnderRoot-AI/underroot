"""
Tests for the Resend-based email service.

Covers:
  1. Verification email calls Resend with correct recipient
  2. Resend-verification calls Resend with correct recipient
  3. Forgot-password calls Resend with correct recipient
  4. Password-reset confirmation calls Resend with correct recipient
  5. Missing RESEND_API_KEY falls back to console (no crash, returns False)
  6. Resend API failure propagates the exception (no silent swallow)
  7. Recipient address is the actual target email, not a hardcoded test address
  8. API key is never exposed in logs or error messages
  9. Existing auth behaviour is unchanged (token flow, response schema)

The Resend SDK is fully mocked — no real API calls are made during pytest.
"""
from __future__ import annotations

import logging
import sys
import types
import unittest.mock as mock
from urllib.parse import urlparse, parse_qs

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

# ── Isolate settings before importing app code ────────────────────────────────
import app.core.config as _cfg  # noqa: E402

_cfg.settings.database_url = "sqlite:///./test_auth_tmp.db"
_cfg.settings.soil_report_database_url = "sqlite:///./test_soil_reports_tmp.db"
_cfg.settings.frontend_url = "http://testserver"
_cfg.settings.smtp_host = ""
_cfg.settings.password_reset_expire_minutes = 60

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from app.database import connection as _conn  # noqa: E402
from app.database.connection import Base  # noqa: E402

_test_engine = create_engine(
    "sqlite:///./test_auth_tmp.db",
    connect_args={"check_same_thread": False},
)
_TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)
_conn.engine = _test_engine
_conn.SessionLocal = _TestingSession

import app.models  # noqa: E402  register ORM models

from app.database import report_connection as _rep  # noqa: E402

_test_report_engine = create_engine(
    "sqlite:///./test_soil_reports_tmp.db",
    connect_args={"check_same_thread": False},
)
_rep.report_engine = _test_report_engine
_rep.ReportSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_test_report_engine)

from app.database.report_connection import ReportBase  # noqa: E402

Base.metadata.create_all(bind=_test_engine)
ReportBase.metadata.create_all(bind=_test_report_engine)

from app.database.migrations import ensure_user_columns  # noqa: E402
ensure_user_columns()

from app.api.routes import auth as _auth_router  # noqa: E402
from app.database.connection import get_db  # noqa: E402

_app = FastAPI()
_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
_app.include_router(_auth_router.router, prefix="/api")


def _override_get_db():
    db = _TestingSession()
    try:
        yield db
    finally:
        db.close()


_app.dependency_overrides[get_db] = _override_get_db
client = TestClient(_app, raise_server_exceptions=True)

# ── Payload helpers ───────────────────────────────────────────────────────────

_BASE = {
    "name": "Resend Tester",
    "email": "resendtest@example.com",
    "password": "Password123",
    "state": "Gujarat",
    "district": "Mehsana",
}


def _signup(overrides: dict | None = None) -> dict:
    payload = {**_BASE, **(overrides or {})}
    r = client.post("/api/auth/signup", json=payload)
    assert r.status_code == 200, r.text
    return r.json()


def _signup_and_verify(overrides: dict | None = None):
    """Signup + verify (console mode) and return access_token."""
    data = _signup(overrides)
    vurl = data.get("verification_url")
    assert vurl, "verification_url missing in console mode"
    token = parse_qs(urlparse(vurl).query)["token"][0]
    vr = client.get("/api/auth/verify-email", params={"token": token})
    assert vr.status_code == 200, vr.text
    return data["access_token"]


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=_test_engine)
    Base.metadata.create_all(bind=_test_engine)
    ensure_user_columns()
    yield
    Base.metadata.drop_all(bind=_test_engine)


# ── Context manager: activate Resend mode, patch resend.Emails.send ──────────

class _ResendActive:
    """
    Context manager that:
      - sets RESEND_API_KEY to a fake key (so _resend_configured() → True)
      - patches resend.Emails.send to a MagicMock
      - patches the ThreadPoolExecutor to call _do_send_resend synchronously
        so we can inspect calls in the same thread as the test
    """

    def __init__(self, side_effect=None):
        self._side_effect = side_effect
        self._patches = []
        self.mock_send = None

    def __enter__(self):
        import app.services.email_service as _es

        # 1. Make _resend_configured() return True
        _cfg.settings.resend_api_key = "re_fake_test_key_do_not_use"

        # 2. Create a mock for resend.Emails.send
        resend_mod = types.ModuleType("resend")
        emails_cls = mock.MagicMock()
        resend_mod.Emails = emails_cls
        resend_mod.api_key = ""

        send_mock = mock.MagicMock(return_value={"id": "test-email-id"})
        if self._side_effect is not None:
            send_mock.side_effect = self._side_effect
        resend_mod.Emails.send = send_mock
        self.mock_send = send_mock

        p_resend = mock.patch.dict(sys.modules, {"resend": resend_mod})
        p_resend.start()
        self._patches.append(p_resend)

        # 3. Patch _pool.submit to call the function synchronously
        def _sync_submit(fn, *args, **kwargs):
            fn(*args, **kwargs)

        p_pool = mock.patch.object(_es._pool, "submit", side_effect=_sync_submit)
        p_pool.start()
        self._patches.append(p_pool)

        return self

    def __exit__(self, *args):
        for p in reversed(self._patches):
            p.stop()
        _cfg.settings.resend_api_key = ""


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Verification email calls Resend with correct recipient
# ═══════════════════════════════════════════════════════════════════════════════
def test_verification_email_calls_resend():
    with _ResendActive() as ctx:
        _signup()
        ctx.mock_send.assert_called_once()
        call_params = ctx.mock_send.call_args[0][0]
        assert call_params["to"] == [_BASE["email"]]
        assert "Verify" in call_params["subject"]


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Resend-verification calls Resend with correct recipient
# ═══════════════════════════════════════════════════════════════════════════════
def test_resend_verification_calls_resend():
    # Signup in console mode first (no Resend) so we get verification_url
    data = _signup()
    access_token = data["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # Backdate the token so the cooldown does not fire
    from datetime import datetime, timedelta, timezone
    from app.models.user import User
    db = _TestingSession()
    try:
        u = db.query(User).filter(User.email == _BASE["email"].lower()).first()
        u.verification_expires_at = (
            datetime.now(timezone.utc) - timedelta(seconds=1)
        )
        db.commit()
    finally:
        db.close()

    with _ResendActive() as ctx:
        r = client.post("/api/auth/resend-verification", headers=headers)
        assert r.status_code == 200, r.text
        ctx.mock_send.assert_called_once()
        call_params = ctx.mock_send.call_args[0][0]
        assert call_params["to"] == [_BASE["email"]]


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Forgot-password calls Resend with correct recipient
# ═══════════════════════════════════════════════════════════════════════════════
def test_forgot_password_calls_resend():
    _signup_and_verify()  # console mode verify
    with _ResendActive() as ctx:
        r = client.post("/api/auth/forgot-password", json={"email": _BASE["email"]})
        assert r.status_code == 200, r.text
        ctx.mock_send.assert_called_once()
        call_params = ctx.mock_send.call_args[0][0]
        assert call_params["to"] == [_BASE["email"]]
        assert "Reset" in call_params["subject"] or "password" in call_params["subject"].lower()


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Password-reset confirmation calls Resend with correct recipient
# ═══════════════════════════════════════════════════════════════════════════════
def test_password_reset_confirmation_calls_resend():
    _signup_and_verify()  # console mode verify

    # Inject a reset token directly so we control it
    from datetime import datetime, timedelta, timezone
    from app.models.user import User
    from app.services.email_service import generate_password_reset_token

    raw_token, token_hash = generate_password_reset_token()
    db = _TestingSession()
    try:
        u = db.query(User).filter(User.email == _BASE["email"].lower()).first()
        u.password_reset_token_hash = token_hash
        u.password_reset_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        db.commit()
    finally:
        db.close()

    with _ResendActive() as ctx:
        r = client.post(
            "/api/auth/reset-password",
            json={"token": raw_token, "new_password": "NewPassword456"},
        )
        assert r.status_code == 200, r.text
        ctx.mock_send.assert_called_once()
        call_params = ctx.mock_send.call_args[0][0]
        assert call_params["to"] == [_BASE["email"]]


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Missing RESEND_API_KEY → console fallback (returns False, no exception)
# ═══════════════════════════════════════════════════════════════════════════════
def test_missing_resend_api_key_falls_back_to_console(caplog):
    # Ensure no key is set and no SMTP is configured
    _cfg.settings.resend_api_key = ""
    _cfg.settings.smtp_host = ""

    from app.services.email_service import send_email

    with caplog.at_level(logging.INFO, logger="underroot.email"):
        result = send_email(
            "user@example.com",
            "Test Subject",
            "<p>html</p>",
            "plain text",
        )

    assert result is False, "send_email must return False in console fallback mode"
    assert any("DEV EMAIL" in record.message for record in caplog.records)


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Resend API failure propagates the exception (no silent swallow)
# ═══════════════════════════════════════════════════════════════════════════════
def test_resend_failure_propagates():
    import app.services.email_service as _es

    boom = RuntimeError("Resend API error")

    with _ResendActive(side_effect=boom):
        with pytest.raises(RuntimeError):
            # Call _do_send_resend directly to verify it raises
            _es._do_send_resend(
                "user@example.com",
                "Test Subject",
                "<p>html</p>",
                "plain text",
            )


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Recipient address is the actual target email (not a hardcoded address)
# ═══════════════════════════════════════════════════════════════════════════════
def test_recipient_is_actual_user_email():
    custom_email = "myfarmer@example.org"
    with _ResendActive() as ctx:
        _signup({"email": custom_email})
        ctx.mock_send.assert_called_once()
        call_params = ctx.mock_send.call_args[0][0]
        assert call_params["to"] == [custom_email]
        # Must NOT be any hardcoded test address
        assert "gmail.com" not in call_params["to"][0]
        assert "underroot" not in call_params["to"][0].lower()


# ═══════════════════════════════════════════════════════════════════════════════
# 8. API key is never exposed in logs or error messages
# ═══════════════════════════════════════════════════════════════════════════════
def test_api_key_not_exposed_in_logs(caplog):
    fake_key = "re_fake_test_key_do_not_use"
    boom = RuntimeError("some resend failure")

    import app.services.email_service as _es

    with _ResendActive(side_effect=boom):
        with caplog.at_level(logging.ERROR, logger="underroot.email"):
            with pytest.raises(RuntimeError):
                _es._do_send_resend(
                    "user@example.com",
                    "Test Subject",
                    "<p>html</p>",
                    "plain text",
                )

    for record in caplog.records:
        assert fake_key not in record.message, (
            "RESEND_API_KEY must not appear in log output"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# 9. Existing auth behaviour is unchanged
#    (token flow, response schema, unverified-login rejection)
# ═══════════════════════════════════════════════════════════════════════════════
def test_existing_auth_behaviour_unchanged():
    """Signup → verify → login must work end-to-end regardless of email provider."""
    # In console mode (no Resend key), verification_url is returned in response
    data = _signup()
    assert data["access_token"]
    assert data["user"]["email_verified"] is False
    assert data["verification_required"] is True
    vurl = data.get("verification_url")
    assert vurl, "verification_url must be returned in console mode"

    # Unverified login must be rejected
    lr = client.post(
        "/api/auth/login",
        json={"email": _BASE["email"], "password": _BASE["password"]},
    )
    assert lr.status_code in (401, 403)

    # Verify via the URL token
    token = parse_qs(urlparse(vurl).query)["token"][0]
    vr = client.get("/api/auth/verify-email", params={"token": token})
    assert vr.status_code == 200
    assert vr.json()["email_verified"] is True

    # Now login must succeed
    lr2 = client.post(
        "/api/auth/login",
        json={"email": _BASE["email"], "password": _BASE["password"]},
    )
    assert lr2.status_code == 200
    assert lr2.json()["access_token"]
    assert lr2.json()["verification_required"] is False
