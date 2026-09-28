from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./smart_soil.db"
    soil_report_database_url: str = "sqlite:///./soil_reports.db"
    jwt_secret: str = "dev-secret-change-this-key-32-bytes-minimum"
    access_token_expire_minutes: int = 1440
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5175,http://127.0.0.1:5175"
    upload_dir: str = "uploads"
    model_dir: str = "ml_models"
    rag_dir: str = "data/knowledge"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    email_from_name: str = "UnderRoot"
    password_reset_expire_minutes: int = 60
    frontend_url: str = "http://localhost:5173"
    hardware_baudrate: int = 9600
    # "mock" → simulated SoilX measurements (no physical device needed)
    # "serial" → real device connected via USB/serial port (existing behaviour)
    # "ble" → reserved for future SoilX BLE/GATT integration
    hardware_mode: str = "mock"
    developer_email: str = "underroot@gmail.com"
    developer_password: str = "underroot4"
    developer_password_hash: str = ""
    sms_provider: str = "console"
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from_number: str = ""
    phone_otp_expire_minutes: int = 10

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]

    @property
    def upload_path(self) -> Path:
        return Path(self.upload_dir)

    @property
    def model_path(self) -> Path:
        return Path(self.model_dir)

    @property
    def rag_path(self) -> Path:
        return Path(self.rag_dir)

settings = Settings()
if not settings.developer_password_hash:
    # The developer password is only a local default; production deployments should set DEVELOPER_PASSWORD_HASH.
    from app.core.security_seed import make_hash
    settings.developer_password_hash = make_hash(settings.developer_password)
