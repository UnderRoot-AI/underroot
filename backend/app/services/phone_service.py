import base64
import hashlib
import secrets
import urllib.parse
import urllib.request
from app.core.config import settings

def generate_phone_otp() -> tuple[str, str]:
    otp = f"{secrets.randbelow(1_000_000):06d}"
    return otp, hashlib.sha256(otp.encode()).hexdigest()

def hash_phone_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode()).hexdigest()

def send_phone_otp(phone: str, otp: str) -> bool:
    provider = settings.sms_provider.lower().strip()
    if provider == "twilio" and settings.twilio_account_sid and settings.twilio_auth_token and settings.twilio_from_number:
        url = f"https://api.twilio.com/2010-04-01/Accounts/{urllib.parse.quote(settings.twilio_account_sid)}/Messages.json"
        body = urllib.parse.urlencode({
            "To": phone,
            "From": settings.twilio_from_number,
            "Body": f"Your Smart Soil Health verification code is {otp}. It expires in {settings.phone_otp_expire_minutes} minutes."
        }).encode()
        token = base64.b64encode(f"{settings.twilio_account_sid}:{settings.twilio_auth_token}".encode()).decode()
        req = urllib.request.Request(url, data=body, headers={"Authorization": f"Basic {token}"}, method="POST")
        with urllib.request.urlopen(req, timeout=20) as response:
            return 200 <= response.status < 300
    return False
