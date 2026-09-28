from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class Signup(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    phone: str | None = None
    language: str = "en"
    state: str | None = None
    district: str | None = None
    city_village: str | None = None

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
