from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator
import re

# Indian mobile number: optional, but if supplied must be 10 digits starting with 6–9
# Accepts bare 10-digit format (e.g. 9876543210) or +91 prefixed (e.g. +919876543210)
_PHONE_RE = re.compile(r"^(\+91[-\s]?|0)?[6-9]\d{9}$")

class Signup(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    phone: str | None = None
    language: str = "en"
    state: str = Field(min_length=1, max_length=120)
    district: str = Field(min_length=1, max_length=120)
    city_village: str | None = None

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be blank")
        return v.strip()

    @field_validator("state")
    @classmethod
    def state_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("State is required")
        return v.strip()

    @field_validator("district")
    @classmethod
    def district_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("District is required")
        return v.strip()

    @field_validator("phone")
    @classmethod
    def phone_format(cls, v: str | None) -> str | None:
        if v is None:
            return v
        cleaned = v.strip()
        if not cleaned:
            return None
        if not _PHONE_RE.match(cleaned):
            raise ValueError(
                "Enter a valid Indian mobile number (10 digits, starting with 6–9), "
                "e.g. 9876543210 or +91 9876543210"
            )
        return cleaned

class Login(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: str
    phone: str | None = None
    language: str
    location: str | None = None
    state: str | None = None
    district: str | None = None
    city_village: str | None = None
    email_verified: bool
    phone_verified: bool = False
    created_at: datetime
    last_login_at: datetime | None = None
    login_count: int = 0

class AuthResponse(BaseModel):
    access_token: str
    user: UserOut
    verification_required: bool = False
    verification_url: str | None = None

class ProfileUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    language: str | None = None
    location: str | None = None
    state: str | None = None
    district: str | None = None
    city_village: str | None = None

class VerifyEmailResponse(BaseModel):
    message: str
    email_verified: bool

class PhoneOtpRequest(BaseModel):
    phone: str = Field(min_length=7, max_length=40)

class VerifyPhoneOtpRequest(BaseModel):
    otp: str = Field(min_length=4, max_length=8)

class PhoneVerificationResponse(BaseModel):
    message: str
    phone_verified: bool
    development_otp: str | None = None

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=6, max_length=128)

class MessageResponse(BaseModel):
    message: str

class DeleteAccountRequest(BaseModel):
    password: str = Field(min_length=1, max_length=128)
