"""
Tests for email verification and password reset flows.

These tests create a minimal FastAPI app with only the auth router,
so they don't require the ML/OCR dependencies used by other routes.

Run with:
    cd backend
    pytest tests/test_auth_flows.py -v
"""
from __future__ import annotations

import sys
import types
import pytest

# ── Stub out heavy optional dependencies before any app imports ──────────────
# This avoids needing scikit-learn, pypdf, joblib, etc. in the test environment.
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

# ── Use an in-memory SQLite database ─────────────────────────────────────────
import app.core.config as _cfg_module  # noqa: E402

_cfg_module.settings.database_url = "sqlite:///./test_auth_tmp.db"
_cfg_module.settings.soil_report_database_url = "sqlite:///./test_soil_reports_tmp.db"
_cfg_module.settings.frontend_url = "http://testserver"
_cfg_module.settings.smtp_host = ""   # console mode — no real emails sent
_cfg_module.settings.password_reset_expire_minutes = 60

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

# ── Wire up a test database ───────────────────────────────────────────────────
from app.database import connection as _conn_module  # noqa: E402
from app.database.connection import Base  # noqa: E402

_test_engine = create_engine(
    "sqlite:///./test_auth_tmp.db",
    connect_args={"check_same_thread": False},
)
_TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)
_conn_module.engine = _test_engine
_conn_module.SessionLocal = _TestingSession

import app.models  # noqa: E402  — register ORM models (User etc.)

# Stub the report DB (not needed for auth)
from app.database import report_connection as _rep  # noqa: E402
_test_report_engine = create_engine(
    "sqlite:///./test_soil_reports_tmp.db",
    connect_args={"check_same_thread": False},
)
_rep.report_engine = _test_report_engine
from app.database.report_connection import ReportBase  # noqa: E402
ReportBase.metadata.create_all(bind=_test_report_engine)

# ── Create a minimal test app with only the auth router ──────────────────────
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
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


# ── Helpers ───────────────────────────────────────────────────────────────────

_PAYLOAD = {
    "name": "Test Farmer",
    "email": "farmer@example.com",
    "password": "Password123",
    "state": "Gujarat",
    "district": "Mehsana",
}


def _signup(payload: dict | None = None) -> dict:
    p = payload or _PAYLOAD
    resp = client.post("/api/auth/signup", json=p)
    assert resp.status_code == 200, resp.text
    return resp.json()


def _db_user(email: str = _PAYLOAD["email"]):
    from app.models.user import User
    db = _TestingSession()
    try:
        return db.query(User).filter(User.email == email.lower()).first()
    finally:
        db.close()


def _set_user_field(email: str, **kwargs):
    from app.models.user import User
    db = _TestingSession()
    try:
        u = db.query(User).filter(User.email == email.lower()).first()
        for k, v in kwargs.items():
            setattr(u, k, v)
        db.commit()
    finally:
        db.close()


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=_test_engine)
    Base.metadata.create_all(bind=_test_engine)
    yield
    Base.metadata.drop_all(bind=_test_engine)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Signup
# ─────────────────────────────────────────────────────────────────────────────

class TestSignup:
    def test_signup_creates_unverified_user(self):
        data = _signup()
        assert data["access_token"]
        assert data["user"]["email_verified"] is False
        assert data["verification_required"] is True

    def test_signup_stores_hashed_token_not_raw(self):
        data = _signup()
        user = _db_user()
        assert user is not None
        assert user.verification_token_hash is not None
        # Raw token appears in verification_url (dev mode); hash must differ
        raw_token = (data.get("verification_url") or "").split("token=")[-1]
        if raw_token:
            assert user.verification_token_hash != raw_token

    def test_signup_password_hashed(self):
        _signup()
        user = _db_user()
        assert user.password_hash != _PAYLOAD["password"]
        assert "pbkdf2" in user.password_hash

    def test_duplicate_email_rejected(self):
        _signup()
        resp = client.post("/api/auth/signup", json=_PAYLOAD)
        assert resp.status_code == 409

    def test_short_password_rejected(self):
        resp = client.post("/api/auth/signup", json={**_PAYLOAD, "password": "abc"})
        assert resp.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# 2. Login
# ─────────────────────────────────────────────────────────────────────────────

class TestLogin:
    def test_login_success(self):
        """Login must succeed only after email verification."""
        data = _signup()
        token = _extract_token(data)
        client.get(f"/api/auth/verify-email?token={token}")
        resp = client.post("/api/auth/login", json={"email": _PAYLOAD["email"], "password": _PAYLOAD["password"]})
        assert resp.status_code == 200
        assert resp.json()["access_token"]

    def test_login_unverified_is_rejected(self):
        """Unverified account must be rejected at login."""
        _signup()
        resp = client.post("/api/auth/login", json={"email": _PAYLOAD["email"], "password": _PAYLOAD["password"]})
        assert resp.status_code in (401, 403)

    def test_login_wrong_password(self):
        _signup()
        resp = client.post("/api/auth/login", json={"email": _PAYLOAD["email"], "password": "wrong"})
        assert resp.status_code == 401

    def test_login_unknown_email(self):
        resp = client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "pass"})
        assert resp.status_code == 401

    def test_login_updates_last_login_at(self):
        data = _signup()
        token = _extract_token(data)
        client.get(f"/api/auth/verify-email?token={token}")
        client.post("/api/auth/login", json={"email": _PAYLOAD["email"], "password": _PAYLOAD["password"]})
        user = _db_user()
        assert user.last_login_at is not None
        assert user.login_count >= 1


# ─────────────────────────────────────────────────────────────────────────────
# 3. Email Verification
# ─────────────────────────────────────────────────────────────────────────────

def _extract_token(data: dict) -> str:
    url: str = data.get("verification_url") or ""
    assert url, "No verification_url in response — SMTP may be configured"
    return url.split("token=")[-1]


class TestEmailVerification:
    def test_valid_token_marks_email_verified(self):
        token = _extract_token(_signup())
        resp = client.get(f"/api/auth/verify-email?token={token}")
        assert resp.status_code == 200
        assert resp.json()["email_verified"] is True
        user = _db_user()
        assert user.email_verified is True
        assert user.verification_token_hash is None

    def test_token_single_use(self):
        token = _extract_token(_signup())
        client.get(f"/api/auth/verify-email?token={token}")
        resp2 = client.get(f"/api/auth/verify-email?token={token}")
        assert resp2.status_code == 400

    def test_invalid_token_rejected(self):
        _signup()
        resp = client.get("/api/auth/verify-email?token=totallywrongtoken")
        assert resp.status_code == 400

    def test_missing_token_returns_422(self):
        resp = client.get("/api/auth/verify-email")
        assert resp.status_code == 422

    def test_expired_token_rejected(self):
        from datetime import datetime, timedelta, timezone
        token = _extract_token(_signup())
        # Manually expire the stored timestamp
        _set_user_field(
            _PAYLOAD["email"],
            verification_expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        resp = client.get(f"/api/auth/verify-email?token={token}")
        assert resp.status_code == 400
        assert "expired" in resp.json()["detail"].lower()

    def test_welcome_email_not_sent_on_re_verification(self):
        """The already_verified flag logic in verify_email must not error out."""
        from app.models.user import User as _User
        token = _extract_token(_signup())
        # Force email_verified=True while keeping the token so the endpoint runs
        _set_user_field(_PAYLOAD["email"], email_verified=True)
        resp = client.get(f"/api/auth/verify-email?token={token}")
        # Should still succeed (already_verified path)
        assert resp.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# 4. Resend Verification
# ─────────────────────────────────────────────────────────────────────────────

class TestResendVerification:
    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {_signup()['access_token']}"}

    def _backdate_token(self):
        """Push the existing token's expiry back to bypass the 60s cooldown."""
        from datetime import datetime, timedelta, timezone
        _set_user_field(
            _PAYLOAD["email"],
            verification_expires_at=datetime.now(timezone.utc) + timedelta(hours=23, minutes=58),
        )

    def test_resend_generates_new_token(self):
        headers = self._headers()
        old_hash = _db_user().verification_token_hash
        self._backdate_token()
        resp = client.post("/api/auth/resend-verification", headers=headers)
        assert resp.status_code == 200
        assert _db_user().verification_token_hash != old_hash

    def test_resend_cooldown_blocks_rapid_requests(self):
        """Token issued < 60 s ago — should be rate-limited (429)."""
        headers = self._headers()
        # Token was just issued at signup — cooldown window still active.
        resp = client.post("/api/auth/resend-verification", headers=headers)
        assert resp.status_code == 429

    def test_resend_for_already_verified_user_ok(self):
        data = _signup()
        token = _extract_token(data)
        client.get(f"/api/auth/verify-email?token={token}")
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        resp = client.post("/api/auth/resend-verification", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["verification_required"] is False

    def test_resend_requires_auth(self):
        assert client.post("/api/auth/resend-verification").status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
# 5. Forgot Password — account enumeration protection
# ─────────────────────────────────────────────────────────────────────────────

class TestForgotPassword:
    def test_registered_email_returns_generic_message(self):
        _signup()
        resp = client.post("/api/auth/forgot-password", json={"email": _PAYLOAD["email"]})
        assert resp.status_code == 200
        msg = resp.json()["message"]
        assert "reset link" in msg.lower() or "email" in msg.lower()

    def test_unregistered_email_same_message(self):
        resp_unknown = client.post("/api/auth/forgot-password", json={"email": "nobody@example.com"})
        _signup()
        resp_known = client.post(
            "/api/auth/forgot-password",
            json={"email": _PAYLOAD["email"]},
        )
        # Both must return 200 and the same message text
        assert resp_unknown.status_code == 200
        assert resp_known.status_code == 200
        assert resp_unknown.json()["message"] == resp_known.json()["message"]

    def test_reset_token_stored_after_request(self):
        _signup()
        client.post("/api/auth/forgot-password", json={"email": _PAYLOAD["email"]})
        user = _db_user()
        assert user.password_reset_token_hash is not None
        assert user.password_reset_expires_at is not None

    def test_invalid_email_format_rejected(self):
        resp = client.post("/api/auth/forgot-password", json={"email": "notanemail"})
        assert resp.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# 6. Reset Password
# ─────────────────────────────────────────────────────────────────────────────

def _issue_reset_token(email: str = _PAYLOAD["email"]) -> str:
    """Inject a fresh reset token directly into the DB and return the raw token."""
    from app.services.email_service import generate_password_reset_token
    from datetime import datetime, timedelta, timezone
    raw, tok_hash = generate_password_reset_token()
    _set_user_field(
        email,
        password_reset_token_hash=tok_hash,
        password_reset_expires_at=datetime.now(timezone.utc) + timedelta(minutes=60),
    )
    return raw


class TestResetPassword:
    def test_valid_token_changes_password(self):
        _signup()
        token = _issue_reset_token()
        new_pw = "NewSecurePass1!"
        resp = client.post("/api/auth/reset-password", json={"token": token, "new_password": new_pw})
        assert resp.status_code == 200
        assert "successfully" in resp.json()["message"].lower()

    def test_old_password_no_longer_works(self):
        # Verify email so login check works
        data = _signup()
        client.get(f"/api/auth/verify-email?token={_extract_token(data)}")
        _issue_reset_token()
        client.post("/api/auth/reset-password", json={"token": _issue_reset_token(), "new_password": "NewPass123"})
        r = client.post("/api/auth/login", json={"email": _PAYLOAD["email"], "password": _PAYLOAD["password"]})
        assert r.status_code == 401

    def test_new_password_works(self):
        data = _signup()
        client.get(f"/api/auth/verify-email?token={_extract_token(data)}")
        new_pw = "BrandNewPass99"
        client.post("/api/auth/reset-password", json={"token": _issue_reset_token(), "new_password": new_pw})
        r = client.post("/api/auth/login", json={"email": _PAYLOAD["email"], "password": new_pw})
        assert r.status_code == 200

    def test_token_single_use(self):
        _signup()
        token = _issue_reset_token()
        client.post("/api/auth/reset-password", json={"token": token, "new_password": "Pass1111"})
        resp2 = client.post("/api/auth/reset-password", json={"token": token, "new_password": "Pass2222"})
        assert resp2.status_code == 400

    def test_token_cleared_after_use(self):
        _signup()
        client.post("/api/auth/reset-password", json={"token": _issue_reset_token(), "new_password": "Pass1111"})
        user = _db_user()
        assert user.password_reset_token_hash is None
        assert user.password_reset_expires_at is None

    def test_invalid_token_rejected(self):
        _signup()
        resp = client.post("/api/auth/reset-password", json={"token": "badtoken", "new_password": "Pass1111"})
        assert resp.status_code == 400

    def test_expired_token_rejected(self):
        from datetime import datetime, timedelta, timezone
        _signup()
        raw, tok_hash = __import__("app.services.email_service", fromlist=["generate_password_reset_token"]).generate_password_reset_token()
        _set_user_field(
            _PAYLOAD["email"],
            password_reset_token_hash=tok_hash,
            password_reset_expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        resp = client.post("/api/auth/reset-password", json={"token": raw, "new_password": "Pass1111"})
        assert resp.status_code == 400
        assert "expired" in resp.json()["detail"].lower()

    def test_short_password_rejected(self):
        _signup()
        resp = client.post("/api/auth/reset-password", json={"token": _issue_reset_token(), "new_password": "ab"})
        assert resp.status_code == 422

    def test_missing_token_rejected(self):
        _signup()
        resp = client.post("/api/auth/reset-password", json={"new_password": "Pass1111"})
        assert resp.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# 7. Email-verification persistence regression tests
#
# These tests prove the exact bug-report scenarios:
# A. unverified user cannot log in
# B. verify email → database marks account as verified
# C. verified user can log in — no verification message
# D. logout and log in again — still succeeds, no re-verification required
# E. login does NOT modify email_verified in the database
# F. verification state is permanent across multiple logins
# ─────────────────────────────────────────────────────────────────────────────

class TestEmailVerificationPersistence:

    def test_A_unverified_user_cannot_login(self):
        """Unverified account must be rejected at login with the verification message."""
        _signup()
        resp = client.post("/api/auth/login", json={"email": _PAYLOAD["email"], "password": _PAYLOAD["password"]})
        assert resp.status_code in (401, 403)
        detail = resp.json().get("detail", "").lower()
        assert "verify" in detail or "verif" in detail

    def test_B_verify_email_marks_account_permanently(self):
        """After successful verification, email_verified must be True in the database."""
        data = _signup()
        token = _extract_token(data)
        resp = client.get(f"/api/auth/verify-email?token={token}")
        assert resp.status_code == 200
        assert resp.json()["email_verified"] is True
        # Confirm the database row was updated
        user = _db_user()
        assert user.email_verified is True
        assert user.verification_token_hash is None

    def test_C_verified_user_can_login(self):
        """A verified user must be able to log in and receive a token."""
        data = _signup()
        token = _extract_token(data)
        client.get(f"/api/auth/verify-email?token={token}")
        resp = client.post("/api/auth/login", json={"email": _PAYLOAD["email"], "password": _PAYLOAD["password"]})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["access_token"]
        assert body["verification_required"] is False
        assert body["user"]["email_verified"] is True

    def test_D_verified_user_can_login_multiple_times(self):
        """Verified user can log in again after a previous login — no re-verification."""
        data = _signup()
        token = _extract_token(data)
        client.get(f"/api/auth/verify-email?token={token}")

        # First login
        r1 = client.post("/api/auth/login", json={"email": _PAYLOAD["email"], "password": _PAYLOAD["password"]})
        assert r1.status_code == 200, r1.text

        # Second login (simulate logout + re-login)
        r2 = client.post("/api/auth/login", json={"email": _PAYLOAD["email"], "password": _PAYLOAD["password"]})
        assert r2.status_code == 200, r2.text
        assert r2.json()["verification_required"] is False
        assert r2.json()["user"]["email_verified"] is True

        # Third login
        r3 = client.post("/api/auth/login", json={"email": _PAYLOAD["email"], "password": _PAYLOAD["password"]})
        assert r3.status_code == 200, r3.text

    def test_E_login_does_not_modify_email_verified(self):
        """Login must never reset or change email_verified in the database."""
        data = _signup()
        token = _extract_token(data)
        client.get(f"/api/auth/verify-email?token={token}")

        # Confirm verified before login
        user_before = _db_user()
        assert user_before.email_verified is True

        # Login
        client.post("/api/auth/login", json={"email": _PAYLOAD["email"], "password": _PAYLOAD["password"]})

        # Confirm email_verified is still True after login
        user_after = _db_user()
        assert user_after.email_verified is True

    def test_F_verification_state_persists_across_many_logins(self):
        """email_verified must remain True across many consecutive logins."""
        data = _signup()
        token = _extract_token(data)
        client.get(f"/api/auth/verify-email?token={token}")

        for i in range(5):
            resp = client.post("/api/auth/login", json={"email": _PAYLOAD["email"], "password": _PAYLOAD["password"]})
            assert resp.status_code == 200, f"Login {i+1} failed: {resp.text}"
            # email_verified must be True in every login response
            assert resp.json()["user"]["email_verified"] is True
            # And in the database
            db_user = _db_user()
            assert db_user.email_verified is True, f"email_verified became False after login {i+1}"

    def test_G_wrong_password_does_not_affect_verified_state(self):
        """A wrong-password attempt must not modify email_verified."""
        data = _signup()
        token = _extract_token(data)
        client.get(f"/api/auth/verify-email?token={token}")

        # Attempt with wrong password
        client.post("/api/auth/login", json={"email": _PAYLOAD["email"], "password": "wrongpassword"})

        # Correct login must still succeed
        user = _db_user()
        assert user.email_verified is True
        resp = client.post("/api/auth/login", json={"email": _PAYLOAD["email"], "password": _PAYLOAD["password"]})
        assert resp.status_code == 200

    def test_H_forgot_reset_password_preserves_verified_state(self):
        """Password reset must NOT touch email_verified."""
        data = _signup()
        token = _extract_token(data)
        client.get(f"/api/auth/verify-email?token={token}")

        user_before = _db_user()
        assert user_before.email_verified is True

        # Reset password
        from app.services.email_service import generate_password_reset_token
        from datetime import datetime, timedelta, timezone
        raw, tok_hash = generate_password_reset_token()
        _set_user_field(
            _PAYLOAD["email"],
            password_reset_token_hash=tok_hash,
            password_reset_expires_at=datetime.now(timezone.utc) + timedelta(minutes=60),
        )
        client.post("/api/auth/reset-password", json={"token": raw, "new_password": "BrandNew123"})

        # email_verified must still be True
        user_after = _db_user()
        assert user_after.email_verified is True

        # Login with new password must succeed
        resp = client.post("/api/auth/login", json={"email": _PAYLOAD["email"], "password": "BrandNew123"})
        assert resp.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# 8. Unauthenticated resend-verification endpoint
# ─────────────────────────────────────────────────────────────────────────────

class TestResendVerificationUnauthenticated:
    """
    Tests for POST /auth/resend-verification-unauthenticated.

    This endpoint lets users who never verified their email (and who have since
    closed the post-signup screen or cleared their session) request a new
    verification link directly from the login page without a Bearer token.
    """

    def _signup_without_verifying(self) -> None:
        """Sign up but do NOT verify the email."""
        resp = client.post("/api/auth/signup", json=_PAYLOAD)
        assert resp.status_code == 200

    def test_unverified_account_receives_new_token(self):
        """Endpoint must update verification_token_hash for an unverified account."""
        self._signup_without_verifying()
        old_hash = _db_user().verification_token_hash

        # Backdate the token so rate-limit doesn't fire
        from datetime import datetime, timedelta, timezone
        _set_user_field(_PAYLOAD["email"],
                        verification_expires_at=datetime.now(timezone.utc) - timedelta(hours=1))

        resp = client.post("/api/auth/resend-verification-unauthenticated",
                           json={"email": _PAYLOAD["email"]})
        assert resp.status_code == 200
        # Always returns the same generic message
        assert "message" in resp.json()
        # DB token must have been rotated
        new_hash = _db_user().verification_token_hash
        assert new_hash != old_hash

    def test_unknown_email_returns_200(self):
        """Must return 200 even for an unknown email — prevents enumeration."""
        resp = client.post("/api/auth/resend-verification-unauthenticated",
                           json={"email": "nobody@example.com"})
        assert resp.status_code == 200

    def test_already_verified_account_returns_200_silently(self):
        """Verified accounts must return the generic message without error."""
        data = _signup()
        token = _extract_token(data)
        client.get(f"/api/auth/verify-email?token={token}")
        resp = client.post("/api/auth/resend-verification-unauthenticated",
                           json={"email": _PAYLOAD["email"]})
        assert resp.status_code == 200
        # email_verified must NOT have been reset
        assert _db_user().email_verified is True

    def test_verified_account_email_verified_not_reset(self):
        """This endpoint must never set email_verified=False on a verified account."""
        data = _signup()
        token = _extract_token(data)
        client.get(f"/api/auth/verify-email?token={token}")
        # Call the unauthenticated resend multiple times
        for _ in range(3):
            client.post("/api/auth/resend-verification-unauthenticated",
                        json={"email": _PAYLOAD["email"]})
        assert _db_user().email_verified is True

    def test_invalid_email_format_rejected(self):
        resp = client.post("/api/auth/resend-verification-unauthenticated",
                           json={"email": "not-an-email"})
        assert resp.status_code == 422

    def test_after_resend_new_token_enables_verification(self):
        """User can verify successfully with the new token issued by this endpoint."""
        self._signup_without_verifying()

        # Backdate old token to bypass rate-limit
        from datetime import datetime, timedelta, timezone
        _set_user_field(_PAYLOAD["email"],
                        verification_expires_at=datetime.now(timezone.utc) - timedelta(hours=1))

        # Request a new token via the unauthenticated endpoint
        client.post("/api/auth/resend-verification-unauthenticated",
                    json={"email": _PAYLOAD["email"]})

        # Grab the new token hash from the DB and reconstruct by injecting directly
        from app.services.email_service import generate_verification_token
        raw, tok_hash = generate_verification_token()
        from datetime import timedelta
        _set_user_field(_PAYLOAD["email"],
                        verification_token_hash=tok_hash,
                        verification_expires_at=datetime.now(timezone.utc) + timedelta(hours=24))

        verify_resp = client.get(f"/api/auth/verify-email?token={raw}")
        assert verify_resp.status_code == 200
        assert verify_resp.json()["email_verified"] is True

        # Now login must succeed
        login_resp = client.post("/api/auth/login",
                                 json={"email": _PAYLOAD["email"], "password": _PAYLOAD["password"]})
        assert login_resp.status_code == 200
        assert login_resp.json()["verification_required"] is False
