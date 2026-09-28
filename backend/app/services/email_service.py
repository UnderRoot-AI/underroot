"""
Enterprise email service for UnderRoot.

Features
--------
- Beautiful branded HTML emails for every event
- Plain-text fallback in every email (multipart/alternative)
- Async sending via ThreadPoolExecutor so FastAPI routes never block
- Console fallback when SMTP is not configured (dev mode)
- Structured logging for every send attempt
- Single send_email() primitive; all typed helpers sit on top
- Token utilities (verification + password reset) live here
"""

from __future__ import annotations

import hashlib
import logging
import secrets
import smtplib
import textwrap
from concurrent.futures import ThreadPoolExecutor
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger("underroot.email")
_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="email")

# ─────────────────────────────────────────────────────────────────────────────
# Brand / design constants
# ─────────────────────────────────────────────────────────────────────────────
_GREEN = "#166534"
_LIGHT = "#eaf6ec"
_BG    = "#f5f8f4"
_BORDER = "#dce6de"
_TEXT  = "#17251d"
_MUTED = "#6c7b70"

# ─────────────────────────────────────────────────────────────────────────────
# Token utilities
# ─────────────────────────────────────────────────────────────────────────────

def generate_verification_token() -> tuple[str, str]:
    """Return (raw_token, sha256_hash). Store only the hash."""
    raw = secrets.token_urlsafe(32)
    return raw, _sha256(raw)


def hash_verification_token(token: str) -> str:
    return _sha256(token)


def generate_password_reset_token() -> tuple[str, str]:
    """Return (raw_token, sha256_hash). Store only the hash."""
    raw = secrets.token_urlsafe(32)
    return raw, _sha256(raw)


def hash_password_reset_token(token: str) -> str:
    return _sha256(token)


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


# ─────────────────────────────────────────────────────────────────────────────
# HTML layout helpers
# ─────────────────────────────────────────────────────────────────────────────

def _wrap_html(title: str, body_html: str) -> str:
    """Wrap body_html in the standard branded layout."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{title}</title>
</head>
<body style="margin:0;padding:0;background:{_BG};font-family:-apple-system,'Segoe UI',system-ui,Arial,sans-serif;color:{_TEXT};">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:{_BG};padding:40px 0;">
    <tr><td align="center">
      <table width="580" cellpadding="0" cellspacing="0" style="max-width:580px;width:100%;">

        <!-- HEADER -->
        <tr><td style="background:{_GREEN};border-radius:16px 16px 0 0;padding:28px 36px;">
          <table cellpadding="0" cellspacing="0">
            <tr>
              <td style="width:42px;height:42px;background:rgba(255,255,255,.18);border-radius:11px;text-align:center;vertical-align:middle;font-size:22px;">🌿</td>
              <td style="padding-left:12px;color:#fff;font-size:20px;font-weight:800;letter-spacing:-.02em;">UnderRoot</td>
            </tr>
          </table>
        </td></tr>

        <!-- BODY -->
        <tr><td style="background:#fff;padding:36px 36px 28px;border-left:1px solid {_BORDER};border-right:1px solid {_BORDER};">
          {body_html}
        </td></tr>

        <!-- FOOTER -->
        <tr><td style="background:{_LIGHT};border:1px solid {_BORDER};border-top:0;border-radius:0 0 16px 16px;padding:20px 36px;text-align:center;font-size:11px;color:{_MUTED};line-height:1.7;">
          This email was sent by <b>UnderRoot — Smart Soil Health Detection System</b>.<br/>
          If you did not request this, you can safely ignore it.<br/>
          <span style="color:{_BORDER};">─────────────────────</span><br/>
          © UnderRoot. All rights reserved.
        </td></tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


def _cta_button(text: str, url: str) -> str:
    return (
        f'<table cellpadding="0" cellspacing="0" style="margin:24px 0;">'
        f'<tr><td style="background:{_GREEN};border-radius:10px;">'
        f'<a href="{url}" style="display:inline-block;padding:14px 28px;color:#fff;font-size:14px;font-weight:700;text-decoration:none;letter-spacing:-.01em;">{text}</a>'
        f'</td></tr></table>'
    )


def _info_box(html: str) -> str:
    return (
        f'<div style="background:{_LIGHT};border:1px solid {_BORDER};border-radius:10px;'
        f'padding:14px 18px;margin:20px 0;font-size:13px;line-height:1.7;">'
        f'{html}</div>'
    )


def _h1(text: str) -> str:
    return f'<h1 style="margin:0 0 8px;font-size:24px;font-weight:800;letter-spacing:-.03em;color:{_TEXT};">{text}</h1>'


def _p(text: str) -> str:
    return f'<p style="margin:12px 0;font-size:14px;line-height:1.7;color:{_MUTED};">{text}</p>'


def _divider() -> str:
    return f'<hr style="border:none;border-top:1px solid {_BORDER};margin:22px 0;"/>'


# ─────────────────────────────────────────────────────────────────────────────
# Core send primitive
# ─────────────────────────────────────────────────────────────────────────────

def _smtp_configured() -> bool:
    return bool(
        settings.smtp_host
        and settings.smtp_user
        and settings.smtp_password
        and settings.smtp_from
    )


def _do_send(to: str, subject: str, html: str, plain: str) -> None:
    """Blocking send. Always called inside the thread pool."""
    from_addr = settings.smtp_from
    from_name = getattr(settings, "email_from_name", "UnderRoot")
    from_header = f"{from_name} <{from_addr}>"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = from_header
    msg["To"]      = to
    msg["X-Mailer"] = "UnderRoot EmailService/2.0"
    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html,  "html",  "utf-8"))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.sendmail(from_addr, [to], msg.as_bytes())
        logger.info("email sent  to=%s subject=%r", to, subject)
    except Exception as exc:
        logger.error("email failed to=%s subject=%r error=%s", to, subject, exc)
        raise


def _console_send(to: str, subject: str, plain: str) -> None:
    border = "─" * 60
    logger.info(
        "\n%s\n📧 DEV EMAIL (SMTP not configured)\nTo:      %s\nSubject: %s\n%s\n%s\n%s",
        border, to, subject, border, textwrap.dedent(plain).strip(), border,
    )


def send_email(to: str, subject: str, html: str, plain: str) -> bool:
    """
    Fire-and-forget email.  Runs in the thread pool so it never blocks
    the FastAPI request cycle.  Falls back to console logging when SMTP
    is not configured (development mode).

    Returns True when SMTP is configured (email queued), False when falling
    back to console (dev mode) — callers use this to decide whether to expose
    raw URLs in API responses.
    """
    if not _smtp_configured():
        _console_send(to, subject, plain)
        return False
    _pool.submit(_do_send, to, subject, html, plain)
    return True


# ─────────────────────────────────────────────────────────────────────────────
# Typed email helpers
# ─────────────────────────────────────────────────────────────────────────────

def send_verification_email(email: str, name: str, verification_url: str) -> bool:
    """
    Send account email-verification link.
    Returns True when SMTP is configured (email queued), False in dev/console mode.
    Callers use the return value to decide whether to surface the raw URL in the
    API response for local development.
    """
    subject = "Verify your UnderRoot account"

    html_body = (
        _h1("Verify your email address")
        + _p(f"Hi <b>{name}</b>, welcome to <b>UnderRoot</b>!")
        + _p("Please verify your email address to activate your account and start monitoring your soil health.")
        + _cta_button("Verify Email Address", verification_url)
        + _info_box(
            f'<b>Link expires in 24 hours.</b><br/>'
            f'If the button doesn\'t work, copy and paste this URL:<br/>'
            f'<a href="{verification_url}" style="color:{_GREEN};font-size:12px;word-break:break-all;">{verification_url}</a>'
        )
        + _divider()
        + _p("If you didn't create an UnderRoot account, you can safely ignore this email.")
    )

    plain = (
        f"Hi {name},\n\n"
        "Welcome to UnderRoot — Smart Soil Health Detection System!\n\n"
        "Please verify your email address by opening the link below:\n\n"
        f"{verification_url}\n\n"
        "This link expires in 24 hours.\n\n"
        "If you didn't create this account, please ignore this email.\n\n"
        "— The UnderRoot Team"
    )

    return send_email(email, subject, _wrap_html(subject, html_body), plain)


def send_welcome_email(email: str, name: str) -> None:
    """
    Sent after email is successfully verified.
    """
    subject = "Your UnderRoot account is ready 🌱"
    dashboard_url = f"{settings.frontend_url}/dashboard"

    html_body = (
        _h1("Your account is verified!")
        + _p(f"Hi <b>{name}</b>, your email has been verified and your UnderRoot account is fully active.")
        + _info_box(
            "🌱 <b>Here's what you can do now:</b><br/><br/>"
            "• <b>Run a soil test</b> — upload your soil report or use a connected probe<br/>"
            "• <b>Get AI recommendations</b> — crops and fertilizers tailored to your soil<br/>"
            "• <b>Track history</b> — compare tests over time<br/>"
            "• <b>Ask the assistant</b> — get instant farming advice"
        )
        + _cta_button("Go to my Dashboard", dashboard_url)
        + _divider()
        + _p("Questions? Reply to this email or use the in-app assistant anytime.")
    )

    plain = (
        f"Hi {name},\n\n"
        "Your UnderRoot account is now fully verified and active!\n\n"
        "What you can do:\n"
        "  - Run a soil test (upload report or use a probe)\n"
        "  - Get AI crop and fertilizer recommendations\n"
        "  - Track soil health history\n"
        "  - Ask the AI farming assistant\n\n"
        f"Go to your dashboard: {dashboard_url}\n\n"
        "— The UnderRoot Team"
    )

    send_email(email, subject, _wrap_html(subject, html_body), plain)


def send_password_reset_email(email: str, name: str, reset_url: str) -> None:
    """
    Send password reset link. Expires in 1 hour.
    """
    subject = "Reset your UnderRoot password"
    expire_minutes = getattr(settings, "password_reset_expire_minutes", 60)
    expire_label = f"{expire_minutes} minutes"

    html_body = (
        _h1("Reset your password")
        + _p(f"Hi <b>{name}</b>, we received a request to reset the password for your UnderRoot account.")
        + _cta_button("Reset Password", reset_url)
        + _info_box(
            f'<b>⏱ This link expires in {expire_label}.</b><br/>'
            f'If the button doesn\'t work, copy and paste this URL:<br/>'
            f'<a href="{reset_url}" style="color:{_GREEN};font-size:12px;word-break:break-all;">{reset_url}</a>'
        )
        + _divider()
        + _p(
            "If you didn't request a password reset, please ignore this email. "
            "Your password will not be changed unless you follow the link above."
        )
        + _p("<b>For your security:</b> never share this link with anyone.")
    )

    plain = (
        f"Hi {name},\n\n"
        "We received a request to reset your UnderRoot password.\n\n"
        "Open the link below to set a new password:\n\n"
        f"{reset_url}\n\n"
        f"This link expires in {expire_label}.\n\n"
        "If you didn't request a password reset, you can safely ignore this email.\n\n"
        "— The UnderRoot Team"
    )

    send_email(email, subject, _wrap_html(subject, html_body), plain)


def send_password_changed_email(email: str, name: str) -> None:
    """
    Confirmation sent after a successful password change.
    """
    subject = "Your UnderRoot password was changed"
    login_url = f"{settings.frontend_url}/login"

    html_body = (
        _h1("Password changed successfully")
        + _p(f"Hi <b>{name}</b>, your UnderRoot account password was just changed.")
        + _info_box(
            "✅ <b>Your password has been updated.</b><br/><br/>"
            "If you made this change, no further action is needed.<br/>"
            "If you did <b>not</b> change your password, please contact us immediately "
            "by replying to this email."
        )
        + _cta_button("Sign in to your account", login_url)
        + _divider()
        + _p("If this wasn't you, please secure your account immediately.")
    )

    plain = (
        f"Hi {name},\n\n"
        "Your UnderRoot account password was successfully changed.\n\n"
        "If you made this change, no action is needed.\n\n"
        "If you did NOT change your password, please contact us immediately.\n\n"
        f"Sign in: {login_url}\n\n"
        "— The UnderRoot Team"
    )

    send_email(email, subject, _wrap_html(subject, html_body), plain)


def send_soil_report_email(email: str, name: str, report_summary: dict) -> None:
    """
    Send soil test result summary email.

    report_summary keys (all optional):
        health_score, ph, nitrogen, phosphorus, potassium,
        ec, moisture, temperature, organic_carbon, test_date
    """
    subject = "Your UnderRoot Soil Test Results"
    dashboard_url = f"{settings.frontend_url}/report"

    score = report_summary.get("health_score", "—")
    score_color = _GREEN if isinstance(score, (int, float)) and score >= 65 else "#d97706"

    def _row(label: str, key: str, unit: str = "") -> str:
        val = report_summary.get(key)
        if val is None:
            return ""
        return (
            f'<tr>'
            f'<td style="padding:9px 12px;border-bottom:1px solid {_BORDER};font-size:13px;color:{_MUTED};">{label}</td>'
            f'<td style="padding:9px 12px;border-bottom:1px solid {_BORDER};font-size:13px;font-weight:700;text-align:right;">{val}{unit}</td>'
            f'</tr>'
        )

    params_rows = (
        _row("pH", "ph")
        + _row("Nitrogen (N)", "nitrogen", " mg/kg")
        + _row("Phosphorus (P)", "phosphorus", " mg/kg")
        + _row("Potassium (K)", "potassium", " mg/kg")
        + _row("Electrical Conductivity", "ec", " dS/m")
        + _row("Moisture", "moisture", "%")
        + _row("Temperature", "temperature", " °C")
        + _row("Organic Carbon", "organic_carbon", "%")
    )

    score_block = (
        f'<div style="text-align:center;margin:20px 0;">'
        f'<div style="display:inline-block;background:{_LIGHT};border:2px solid {score_color};border-radius:50%;'
        f'width:90px;height:90px;line-height:90px;font-size:30px;font-weight:800;color:{score_color};">'
        f'{score}</div>'
        f'<div style="font-size:12px;color:{_MUTED};margin-top:8px;">Soil Health Score</div>'
        f'</div>'
    ) if score != "—" else ""

    html_body = (
        _h1("Your soil test results are ready")
        + _p(f"Hi <b>{name}</b>, your latest UnderRoot soil analysis has been completed.")
        + score_block
        + (
            f'<table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid {_BORDER};border-radius:10px;overflow:hidden;margin:16px 0;">'
            f'<thead><tr><th style="background:{_LIGHT};padding:10px 12px;text-align:left;font-size:11px;font-weight:800;color:{_MUTED};text-transform:uppercase;letter-spacing:.06em;">Parameter</th>'
            f'<th style="background:{_LIGHT};padding:10px 12px;text-align:right;font-size:11px;font-weight:800;color:{_MUTED};text-transform:uppercase;letter-spacing:.06em;">Value</th></tr></thead>'
            f'<tbody>{params_rows}</tbody></table>'
            if params_rows else ""
        )
        + _cta_button("View full report & recommendations", dashboard_url)
        + _divider()
        + _p("Your full report including crop and fertilizer recommendations is available in the dashboard.")
    )

    param_lines = "\n".join(
        f"  {k.replace('_', ' ').title()}: {v}"
        for k, v in report_summary.items()
        if k != "health_score" and v is not None
    )

    plain = (
        f"Hi {name},\n\n"
        "Your UnderRoot soil test results are ready.\n\n"
        + (f"Soil Health Score: {score}\n\n" if score != "—" else "")
        + (f"Parameters:\n{param_lines}\n\n" if param_lines else "")
        + f"View full report: {dashboard_url}\n\n"
        "— The UnderRoot Team"
    )

    send_email(email, subject, _wrap_html(subject, html_body), plain)
