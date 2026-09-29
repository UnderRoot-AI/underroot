from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.user import User
from app.schemas.auth import (
    Signup, Login, AuthResponse, UserOut, ProfileUpdate,
    VerifyEmailResponse, PhoneOtpRequest, VerifyPhoneOtpRequest,
    PhoneVerificationResponse, ForgotPasswordRequest, ResetPasswordRequest,
    MessageResponse,
)
from app.core.security import hash_password, verify_password, create_access_token, get_current_user
from app.services.email_service import (
    generate_verification_token, hash_verification_token, send_verification_email,
    send_welcome_email, generate_password_reset_token, hash_password_reset_token,
    send_password_reset_email, send_password_changed_email,
)
from app.core.config import settings
from app.services.phone_service import generate_phone_otp, hash_phone_otp, send_phone_otp

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=AuthResponse)
def signup(data: Signup, db: Session = Depends(get_db)):
    email = str(data.email).lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(409, "Email already registered")
    token, token_hash = generate_verification_token()
    user = User(
        name=data.name, email=email, password_hash=hash_password(data.password),
        phone=data.phone, language=data.language, state=data.state, district=data.district,
        city_village=data.city_village, email_verified=False, phone_verified=not bool(data.phone),
        verification_token_hash=token_hash,
        verification_expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db.add(user); db.commit(); db.refresh(user)
    verification_url = f"{settings.frontend_url}/verify-email?token={token}"
    sent = send_verification_email(email, data.name, verification_url)
    return {
        "access_token": create_access_token(user.id),
        "user": user,
        # verification_required is true until email is verified.
        # Phone verification is NOT part of the signup flow.
        "verification_required": not user.email_verified,
        # Returned only for local development when SMTP is not configured.
        "verification_url": None if sent else verification_url,
    }


@router.post("/login", response_model=AuthResponse)
def login(data: Login, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == str(data.email).lower()).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    if not user.email_verified:
        raise HTTPException(
            401,
            "Please verify your email address before signing in. "
            "Check your inbox for the verification link, or request a new one.",
        )
    user.last_login_at = datetime.now(timezone.utc)
    user.login_count = int(user.login_count or 0) + 1
    db.commit(); db.refresh(user)
    return {
        "access_token": create_access_token(user.id),
        "user": user,
        "verification_required": False,
    }


@router.get("/verify-email", response_model=VerifyEmailResponse)
def verify_email(token: str, db: Session = Depends(get_db)):
    digest = hash_verification_token(token)
    user = db.query(User).filter(User.verification_token_hash == digest).first()
    if not user:
        # Check if a user with this token was already verified (token cleared after first use)
        raise HTTPException(400, "Invalid or already used verification link. Request a new one if needed.")
    expires = user.verification_expires_at
    if expires and expires.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(400, "Verification link has expired. Please request a new verification email.")
    already_verified = user.email_verified
    user.email_verified = True
    user.verification_token_hash = None
    user.verification_expires_at = None
    db.commit()
    # Send welcome email on first verification only
    if not already_verified:
        send_welcome_email(user.email, user.name)
    return {"message": "Email verified successfully", "email_verified": True}


# Resend cooldown: allow at most one resend per 60 seconds.
_RESEND_COOLDOWN_SECONDS = 60

@router.post("/resend-verification", response_model=AuthResponse)
def resend_verification(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.email_verified:
        return {"access_token": create_access_token(user.id), "user": user, "verification_required": False}
    # Rate-limit: if a token was issued less than 60 seconds ago, reject the request.
    if user.verification_expires_at:
        issued_threshold = datetime.now(timezone.utc) + timedelta(hours=24) - timedelta(seconds=_RESEND_COOLDOWN_SECONDS)
        expires_aware = user.verification_expires_at.replace(tzinfo=timezone.utc)
        if expires_aware > issued_threshold:
            raise HTTPException(
                429,
                f"Please wait {_RESEND_COOLDOWN_SECONDS} seconds before requesting another verification email.",
            )
    token, token_hash = generate_verification_token()
    user.verification_token_hash = token_hash
    user.verification_expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    db.commit(); db.refresh(user)
    verification_url = f"{settings.frontend_url}/verify-email?token={token}"
    sent = send_verification_email(user.email, user.name, verification_url)
    return {
        "access_token": create_access_token(user.id),
        "user": user,
        "verification_required": True,
        "verification_url": None if sent else verification_url,
    }


# ── Password reset ────────────────────────────────────────────────────────────

# Minimum interval between password-reset requests: 60 seconds.
_RESET_REQUEST_COOLDOWN_SECONDS = 60

@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Always returns the same generic message to prevent user enumeration.
    The reset link is only sent when the email actually exists.
    Rate-limited to one request per 60 seconds per account (silently enforced).
    """
    user = db.query(User).filter(User.email == str(data.email).lower()).first()
    if user:
        # Silently skip sending if a reset was requested within the last 60 seconds.
        can_send = True
        if user.password_reset_expires_at:
            remaining_lifetime = timedelta(minutes=settings.password_reset_expire_minutes) - timedelta(seconds=_RESET_REQUEST_COOLDOWN_SECONDS)
            too_recent_threshold = datetime.now(timezone.utc) + remaining_lifetime
            expires_aware = user.password_reset_expires_at.replace(tzinfo=timezone.utc)
            if expires_aware > too_recent_threshold:
                can_send = False  # Cooldown active — return generic message without sending
        if can_send:
            token, token_hash = generate_password_reset_token()
            user.password_reset_token_hash = token_hash
            user.password_reset_expires_at = (
                datetime.now(timezone.utc)
                + timedelta(minutes=settings.password_reset_expire_minutes)
            )
            db.commit()
            reset_url = f"{settings.frontend_url}/reset-password?token={token}"
            send_password_reset_email(user.email, user.name, reset_url)
    return {"message": "If an account with that email exists, a password reset link has been sent."}


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    digest = hash_password_reset_token(data.token)
    user = db.query(User).filter(User.password_reset_token_hash == digest).first()
    if not user:
        raise HTTPException(400, "Invalid or expired password reset link")
    expires = user.password_reset_expires_at
    if not expires or expires.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(400, "Password reset link has expired. Please request a new one.")
    user.password_hash = hash_password(data.new_password)
    user.password_reset_token_hash = None
    user.password_reset_expires_at = None
    db.commit()
    send_password_changed_email(user.email, user.name)
    return {"message": "Password reset successfully. You can now sign in with your new password."}


# ── Profile ───────────────────────────────────────────────────────────────────

@router.post("/request-phone-otp", response_model=PhoneVerificationResponse)
def request_phone_otp(data: PhoneOtpRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    phone = data.phone.strip()
    if not user.phone or user.phone.strip() != phone:
        raise HTTPException(400, "The phone number must match the phone number saved in your profile")
    otp, otp_hash = generate_phone_otp()
    user.phone_otp_hash = otp_hash
    user.phone_otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.phone_otp_expire_minutes)
    user.phone_otp_attempts = 0
    db.commit()
    delivered = send_phone_otp(phone, otp)
    return {
        "message": "OTP sent to your phone" if delivered else "Development OTP generated. Configure Twilio SMS for real SMS delivery.",
        "phone_verified": bool(user.phone_verified),
        "development_otp": None if delivered else otp,
    }


@router.post("/verify-phone-otp", response_model=PhoneVerificationResponse)
def verify_phone_otp(data: VerifyPhoneOtpRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.phone_verified:
        return {"message": "Phone number is already verified", "phone_verified": True}
    if not user.phone_otp_hash or not user.phone_otp_expires_at:
        raise HTTPException(400, "Request a new phone verification code first")
    if user.phone_otp_expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(400, "The phone verification code has expired")
    if int(user.phone_otp_attempts or 0) >= 5:
        raise HTTPException(429, "Too many incorrect attempts. Request a new code.")
    user.phone_otp_attempts = int(user.phone_otp_attempts or 0) + 1
    if hash_phone_otp(data.otp.strip()) != user.phone_otp_hash:
        db.commit()
        raise HTTPException(400, "Invalid phone verification code")
    user.phone_verified = True
    user.phone_otp_hash = None
    user.phone_otp_expires_at = None
    user.phone_otp_attempts = 0
    db.commit(); db.refresh(user)
    return {"message": "Phone number verified successfully", "phone_verified": True}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.put("/me", response_model=UserOut)
def update_me(data: ProfileUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    updates = data.model_dump(exclude_unset=True)
    if "phone" in updates and updates["phone"] != user.phone:
        user.phone_verified = not bool(updates["phone"])
        user.phone_otp_hash = None
        user.phone_otp_expires_at = None
        user.phone_otp_attempts = 0
    for key, value in updates.items():
        setattr(user, key, value)
    db.commit(); db.refresh(user)
    return user
