from datetime import datetime, timedelta, timezone
import base64
import hashlib
import hmac
import os
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.config import settings
from app.database.connection import get_db
from app.models.user import User

bearer = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
    return "pbkdf2_sha256$310000$" + base64.b64encode(salt).decode() + "$" + base64.b64encode(digest).decode()

def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, iterations, salt_b64, digest_b64 = encoded.split("$", 3)
        if scheme != "pbkdf2_sha256": return False
        salt = base64.b64decode(salt_b64); expected = base64.b64decode(digest_b64)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(iterations))
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False

def create_access_token(user_id: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode({"sub": str(user_id), "role": "user", "exp": exp}, settings.jwt_secret, algorithm="HS256")

def create_developer_token() -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode({"sub": "developer", "role": "developer", "exp": exp}, settings.jwt_secret, algorithm="HS256")

def decode_token(credentials: HTTPAuthorizationCredentials | None):
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        return jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=["HS256"])
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> User:
    payload = decode_token(credentials)
    if payload.get("role") not in (None, "user"):
        raise HTTPException(status_code=403, detail="User access required")
    try: user_id = int(payload["sub"])
    except Exception: raise HTTPException(status_code=401, detail="Invalid user token")
    user = db.get(User, user_id)
    if not user: raise HTTPException(status_code=401, detail="User not found")
    return user

def get_current_developer(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> dict:
    payload = decode_token(credentials)
    if payload.get("role") != "developer" or payload.get("sub") != "developer":
        raise HTTPException(status_code=403, detail="Developer access required")
    return payload
