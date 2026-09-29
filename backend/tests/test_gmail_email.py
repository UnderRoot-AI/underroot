"""
Tests for the Gmail API email transport.

Covers:
  1.  _gmail_configured() → True when all four settings are present
  2.  _gmail_configured() → False when any setting is missing
  3.  Gmail is selected (not Resend) when Gmail is fully configured
  4.  Resend is selected when Gmail is NOT configured but RESEND_API_KEY is set
  5.  SMTP is selected when neither Gmail nor Resend are configured
  6.  Console fallback when no provider is configured
  7.  MIME message contains both plain-text and HTML parts
  8.  Gmail API call uses userId="me"
  9.  _do_send_gmail logs success without exposing secrets
  10. _do_send_gmail raises on API error (no silent swallow)
  11. Gmail API errors are logged safely (no secrets in log output)

The Google API client is fully mocked — no real network calls are made.
"""
from __future__ import annotations

import logging
import sys
import types
import unittest.mock as mock

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
_cfg.settings.resend_api_key = ""
_cfg.settings.gmail_client_id = ""
_cfg.settings.gmail_client_secret = ""
_cfg.settings.gmail_refresh_token = ""
_cfg.settings.gmail_sender_email = ""

import app.services.email_service as _es  # noqa: E402

# ─────────────────────────────────────────────────────────────────────────────
# Helpers / fixtures
# ─────────────────────────────────────────────────────────────────────────────

_FAKE_GMAIL_SETTINGS = {
    "gmail_client_id": "fake-client-id.apps.googleusercontent.com",
    "gmail_client_secret": "fake-client-secret",
    "gmail_refresh_token": "fake-refresh-token",
    "gmail_sender_email": "underroot.ai@gmail.com",
}


def _apply_gmail_settings():
    for k, v in _FAKE_GMAIL_SETTINGS.items():
        setattr(_cfg.settings, k, v)


def _clear_gmail_settings():
    for k in _FAKE_GMAIL_SETTINGS:
        setattr(_cfg.settings, k, "")


@pytest.fixture(autouse=True)
def _reset_settings():
    """Ensure each test starts with a clean provider configuration."""
    _clear_gmail_settings()
    _cfg.settings.resend_api_key = ""
    _cfg.settings.smtp_host = ""
    yield
    _clear_gmail_settings()
    _cfg.settings.resend_api_key = ""
    _cfg.settings.smtp_host = ""


class _GmailActive:
    """
    Context manager that:
      - sets all four GMAIL_* settings (so _gmail_configured() → True)
      - stubs google.oauth2.credentials.Credentials and
        googleapiclient.discovery.build so no real HTTP calls occur
      - patches _pool.submit to call the function synchronously
    Returns the mock execute() callable via .mock_execute.
    """

    def __init__(self, side_effect=None):
        self._side_effect = side_effect
        self._patches = []
        self.mock_execute = None
        self.mock_send_call = None

    def __enter__(self):
        _apply_gmail_settings()

        # Build a realistic-looking mock for the Gmail service chain:
        #   service.users().messages().send(userId=..., body=...).execute()
        mock_execute = mock.MagicMock(return_value={"id": "fake-message-id"})
        if self._side_effect is not None:
            mock_execute.side_effect = self._side_effect
        self.mock_execute = mock_execute

        mock_send_resource = mock.MagicMock()
        mock_send_resource.return_value.execute = mock_execute
        self.mock_send_call = mock_send_resource

        mock_messages = mock.MagicMock()
        mock_messages.send = mock_send_resource

        mock_users = mock.MagicMock()
        mock_users.return_value.messages.return_value = mock_messages

        mock_service = mock.MagicMock()
        mock_service.users = mock_users

        mock_build = mock.MagicMock(return_value=mock_service)
        mock_credentials_cls = mock.MagicMock()

        # Stub google packages
        google_pkg = types.ModuleType("google")
        google_oauth2 = types.ModuleType("google.oauth2")
        google_oauth2_creds = types.ModuleType("google.oauth2.credentials")
        google_oauth2_creds.Credentials = mock_credentials_cls
        google_auth = types.ModuleType("google.auth")
        googleapiclient = types.ModuleType("googleapiclient")
        googleapiclient_discovery = types.ModuleType("googleapiclient.discovery")
        googleapiclient_discovery.build = mock_build
        google_auth_httplib2 = types.ModuleType("google_auth_httplib2")
        google_auth_oauthlib = types.ModuleType("google_auth_oauthlib")

        p_mods = mock.patch.dict(sys.modules, {
            "google": google_pkg,
            "google.oauth2": google_oauth2,
            "google.oauth2.credentials": google_oauth2_creds,
            "google.auth": google_auth,
            "googleapiclient": googleapiclient,
            "googleapiclient.discovery": googleapiclient_discovery,
            "google_auth_httplib2": google_auth_httplib2,
            "google_auth_oauthlib": google_auth_oauthlib,
        })
        p_mods.start()
        self._patches.append(p_mods)

        # Run pool.submit synchronously
        def _sync_submit(fn, *args, **kwargs):
            fn(*args, **kwargs)

        p_pool = mock.patch.object(_es._pool, "submit", side_effect=_sync_submit)
        p_pool.start()
        self._patches.append(p_pool)

        self._mock_build = mock_build
        self._mock_credentials_cls = mock_credentials_cls
        return self

    def __exit__(self, *args):
        for p in reversed(self._patches):
            p.stop()
        _clear_gmail_settings()


# ═══════════════════════════════════════════════════════════════════════════════
# 1. _gmail_configured() → True when all four settings are present
# ═══════════════════════════════════════════════════════════════════════════════
def test_gmail_configured_true_when_all_settings_present():
    _apply_gmail_settings()
    assert _es._gmail_configured() is True


# ═══════════════════════════════════════════════════════════════════════════════
# 2. _gmail_configured() → False when any setting is missing
# ═══════════════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize("missing_key", list(_FAKE_GMAIL_SETTINGS.keys()))
def test_gmail_configured_false_when_any_setting_missing(missing_key):
    _apply_gmail_settings()
    setattr(_cfg.settings, missing_key, "")
    assert _es._gmail_configured() is False


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Gmail is selected (not Resend) when Gmail is fully configured
# ═══════════════════════════════════════════════════════════════════════════════
def test_gmail_selected_over_resend_when_configured():
    _cfg.settings.resend_api_key = "re_fake_key"

    with _GmailActive() as ctx:
        result = _es.send_email(
            "user@example.com", "Subject", "<p>html</p>", "plain"
        )

    assert result is True
    # Gmail execute must have been called
    ctx.mock_execute.assert_called_once()


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Resend is selected when Gmail is NOT configured but RESEND_API_KEY is set
# ═══════════════════════════════════════════════════════════════════════════════
def test_resend_selected_when_gmail_not_configured():
    _cfg.settings.resend_api_key = "re_fake_key"
    # Gmail is NOT configured (cleared by autouse fixture)

    resend_mod = types.ModuleType("resend")
    emails_cls = mock.MagicMock()
    resend_mod.Emails = emails_cls
    resend_mod.api_key = ""
    send_mock = mock.MagicMock(return_value={"id": "resend-test-id"})
    resend_mod.Emails.send = send_mock

    def _sync_submit(fn, *args, **kwargs):
        fn(*args, **kwargs)

    with mock.patch.dict(sys.modules, {"resend": resend_mod}):
        with mock.patch.object(_es._pool, "submit", side_effect=_sync_submit):
            result = _es.send_email(
                "user@example.com", "Subject", "<p>html</p>", "plain"
            )

    assert result is True
    send_mock.assert_called_once()


# ═══════════════════════════════════════════════════════════════════════════════
# 5. SMTP is selected when neither Gmail nor Resend are configured
# ═══════════════════════════════════════════════════════════════════════════════
def test_smtp_selected_when_gmail_and_resend_not_configured():
    _cfg.settings.smtp_host = "smtp.example.com"
    _cfg.settings.smtp_user = "user@example.com"
    _cfg.settings.smtp_password = "secret"
    _cfg.settings.smtp_from = "noreply@example.com"

    def _sync_submit(fn, *args, **kwargs):
        fn(*args, **kwargs)

    with mock.patch("smtplib.SMTP") as mock_smtp_cls:
        mock_smtp = mock.MagicMock()
        mock_smtp_cls.return_value.__enter__ = mock.MagicMock(return_value=mock_smtp)
        mock_smtp_cls.return_value.__exit__ = mock.MagicMock(return_value=False)
        with mock.patch.object(_es._pool, "submit", side_effect=_sync_submit):
            result = _es.send_email(
                "user@example.com", "Subject", "<p>html</p>", "plain"
            )

    assert result is True

    # cleanup
    _cfg.settings.smtp_host = ""
    _cfg.settings.smtp_user = ""
    _cfg.settings.smtp_password = ""
    _cfg.settings.smtp_from = ""


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Console fallback when no provider is configured
# ═══════════════════════════════════════════════════════════════════════════════
def test_console_fallback_when_no_provider_configured(caplog):
    with caplog.at_level(logging.INFO, logger="underroot.email"):
        result = _es.send_email(
            "user@example.com", "Test Subject", "<p>html</p>", "plain text"
        )

    assert result is False
    assert any("DEV EMAIL" in r.message for r in caplog.records)


# ═══════════════════════════════════════════════════════════════════════════════
# 7. MIME message contains both plain-text and HTML parts
# ═══════════════════════════════════════════════════════════════════════════════
def test_gmail_mime_message_has_both_plain_and_html_parts():
    import base64
    from email import message_from_bytes

    captured_body = {}

    def _capture_send(userId, body):  # noqa: N803
        captured_body.update(body)
        m = mock.MagicMock()
        m.execute.return_value = {"id": "x"}
        return m

    with _GmailActive() as ctx:
        # Override the send call to capture the raw body
        ctx.mock_send_call.side_effect = _capture_send

        _es._do_send_gmail(
            "recipient@example.com",
            "Hello",
            "<p>HTML content</p>",
            "Plain content",
        )

    assert "raw" in captured_body
    decoded = base64.urlsafe_b64decode(captured_body["raw"] + "==")
    msg = message_from_bytes(decoded)

    content_types = [part.get_content_type() for part in msg.walk()]
    assert "text/plain" in content_types
    assert "text/html" in content_types


# ═══════════════════════════════════════════════════════════════════════════════
# 8. Gmail API call uses userId="me"
# ═══════════════════════════════════════════════════════════════════════════════
def test_gmail_api_uses_userid_me():
    with _GmailActive() as ctx:
        _es._do_send_gmail(
            "recipient@example.com",
            "Hello",
            "<p>html</p>",
            "plain",
        )

    # The send() call must have been invoked with userId="me"
    call_kwargs = ctx.mock_send_call.call_args
    assert call_kwargs is not None
    assert call_kwargs.kwargs.get("userId") == "me" or (
        len(call_kwargs.args) > 0 and call_kwargs.args[0] == "me"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 9. Success is logged without exposing OAuth secrets
# ═══════════════════════════════════════════════════════════════════════════════
def test_gmail_success_logged_without_secrets(caplog):
    with _GmailActive():
        with caplog.at_level(logging.INFO, logger="underroot.email"):
            _es._do_send_gmail(
                "user@example.com", "Subject", "<p>html</p>", "plain"
            )

    # Must have a success log entry
    assert any("gmail email sent" in r.message for r in caplog.records)

    # Secrets must never appear in any log message
    for record in caplog.records:
        assert _FAKE_GMAIL_SETTINGS["gmail_client_secret"] not in record.message
        assert _FAKE_GMAIL_SETTINGS["gmail_refresh_token"] not in record.message
        assert _FAKE_GMAIL_SETTINGS["gmail_client_id"] not in record.message


# ═══════════════════════════════════════════════════════════════════════════════
# 10. _do_send_gmail raises on API error (no silent swallow)
# ═══════════════════════════════════════════════════════════════════════════════
def test_gmail_api_error_propagates():
    boom = RuntimeError("Gmail API quota exceeded")

    with _GmailActive(side_effect=boom):
        with pytest.raises(RuntimeError, match="Gmail API quota exceeded"):
            _es._do_send_gmail(
                "user@example.com", "Subject", "<p>html</p>", "plain"
            )


# ═══════════════════════════════════════════════════════════════════════════════
# 11. Gmail API errors are logged safely (no secrets in log output)
# ═══════════════════════════════════════════════════════════════════════════════
def test_gmail_error_logged_without_secrets(caplog):
    boom = RuntimeError("some gmail failure")

    with _GmailActive(side_effect=boom):
        with caplog.at_level(logging.ERROR, logger="underroot.email"):
            with pytest.raises(RuntimeError):
                _es._do_send_gmail(
                    "user@example.com", "Subject", "<p>html</p>", "plain"
                )

    assert any("gmail email failed" in r.message for r in caplog.records)

    for record in caplog.records:
        assert _FAKE_GMAIL_SETTINGS["gmail_client_secret"] not in record.message
        assert _FAKE_GMAIL_SETTINGS["gmail_refresh_token"] not in record.message
