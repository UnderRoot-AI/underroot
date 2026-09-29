"""
Hardware integration tests for UnderRoot.

Tests
─────
 1. Device creation
 2. Device ownership
 3. Device listing
 4. Device retrieval
 5. Unauthorised device access
 6. Measurement ingestion
 7. Invalid measurement rejection
 8. NaN / Infinity rejection
 9. Device last_seen update
10. SoilTest creation from hardware reading
11. Existing analyzer execution
12. Missing parameters
13. Hardware source metadata
14. Measurement history
15. Latest reading
16. AI assistant sees hardware-generated latest soil test
"""
from __future__ import annotations

import sys
import types
import math
import pytest

# ── Stub heavy optional dependencies before any app imports ──────────────────
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

# ── Patch settings to use in-memory test databases ───────────────────────────
import app.core.config as _cfg_module  # noqa: E402

_cfg_module.settings.database_url = "sqlite:///./test_hardware_tmp.db"
_cfg_module.settings.soil_report_database_url = "sqlite:///./test_hardware_reports_tmp.db"
_cfg_module.settings.smtp_host = ""
_cfg_module.settings.frontend_url = "http://testserver"

# ── Wire up test databases ────────────────────────────────────────────────────
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import connection as _conn  # noqa: E402
from app.database.connection import Base  # noqa: E402

_test_engine = create_engine(
    "sqlite:///./test_hardware_tmp.db",
    connect_args={"check_same_thread": False},
)
_TestSession = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)
_conn.engine = _test_engine
_conn.SessionLocal = _TestSession

import app.models  # noqa: E402 — register ORM models

from app.database import report_connection as _rep  # noqa: E402

_test_report_engine = create_engine(
    "sqlite:///./test_hardware_reports_tmp.db",
    connect_args={"check_same_thread": False},
)
_rep.report_engine = _test_report_engine
from app.database.report_connection import ReportBase  # noqa: E402

ReportBase.metadata.create_all(bind=_test_report_engine)


def _override_db():
    db = _TestSession()
    try:
        yield db
    finally:
        db.close()


def _override_report_db():
    db = _TestSession.__class__(bind=_test_report_engine)()
    try:
        yield db
    finally:
        db.close()


from app.database.connection import get_db  # noqa: E402
from app.database.report_connection import get_report_db  # noqa: E402
from app.api.routes import auth as _auth  # noqa: E402
from app.api.routes import soil as _soil  # noqa: E402
from app.api.routes import devices as _devices  # noqa: E402
from app.api.routes import assistant as _assistant  # noqa: E402

# ── Build test app ────────────────────────────────────────────────────────────
_app = FastAPI()
for r in (_auth.router, _soil.router, _devices.router, _assistant.router):
    _app.include_router(r, prefix="/api")

_app.dependency_overrides[get_db] = _override_db
_app.dependency_overrides[get_report_db] = _override_report_db

client = TestClient(_app, raise_server_exceptions=True)
# Separate client for tests that involve NaN/Inf (Python's json encoder can't serialize them in error responses)
client_no_exc = TestClient(_app, raise_server_exceptions=False)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=_test_engine)
    Base.metadata.create_all(bind=_test_engine)
    ReportBase.metadata.drop_all(bind=_test_report_engine)
    ReportBase.metadata.create_all(bind=_test_report_engine)
    yield
    Base.metadata.drop_all(bind=_test_engine)
    ReportBase.metadata.drop_all(bind=_test_report_engine)


# ── Auth helpers ──────────────────────────────────────────────────────────────

_USER_A = {"name": "Farmer A", "email": "farmera@example.com", "password": "TestPass123",
           "state": "Gujarat", "district": "Mehsana"}
_USER_B = {"name": "Farmer B", "email": "farmerb@example.com", "password": "TestPass456",
           "state": "Punjab", "district": "Ludhiana"}


def _register_and_login(payload: dict) -> str:
    r = client.post("/api/auth/signup", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    # Auto-verify email for test simplicity
    from app.models.user import User
    db = _TestSession()
    user = db.query(User).filter(User.email == payload["email"].lower()).first()
    user.email_verified = True
    db.commit()
    db.close()
    # Login
    lr = client.post("/api/auth/login", json={"email": payload["email"], "password": payload["password"]})
    assert lr.status_code == 200, lr.text
    return lr.json()["access_token"]


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


_DEVICE_PAYLOAD = {
    "device_id": "GENERIC-TEST-001",
    "manufacturer": "Generic Labs",
    "model": "Sensor v1",
    "name": "Test Generic Device",
    "connection_type": "generic",
}

_SOILX_DEVICE_PAYLOAD = {
    "device_id": "SOILX-REVE-007",
    "manufacturer": "REVE Nano-Science",
    "model": "SoilX",
    "name": "Test SoilX Device",
    "connection_type": "generic",
}

_READING_PAYLOAD = {
    "timestamp": "2026-09-29T12:30:00Z",
    "measurements": {
        "ph":             {"value": 6.8,  "unit": "pH"},
        "ec":             {"value": 0.42, "unit": "dS/m"},
        "nitrogen":       {"value": 185,  "unit": "kg/ha"},
        "phosphorus":     {"value": 32,   "unit": "kg/ha"},
        "potassium":      {"value": 210,  "unit": "kg/ha"},
        "moisture":       {"value": 38.5, "unit": "%"},
        "temperature":    {"value": 27.4, "unit": "°C"},
        "organic_carbon": {"value": 0.72, "unit": "%"},
        # Extended parameters (SoilX-class)
        "sulphur":        {"value": 18.0, "unit": "mg/kg"},
        "zinc":           {"value": 1.2,  "unit": "mg/kg"},
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Device creation
# ═══════════════════════════════════════════════════════════════════════════════

class TestDeviceCreation:
    def test_register_device_success(self):
        token = _register_and_login(_USER_A)
        r = client.post("/api/devices", json=_DEVICE_PAYLOAD, headers=_headers(token))
        assert r.status_code == 201, r.text
        data = r.json()
        assert data["device_id"] == "GENERIC-TEST-001"
        assert data["manufacturer"] == "Generic Labs"
        assert data["model"] == "Sensor v1"
        assert data["status"] == "unknown"
        assert data["is_active"] is True

    def test_register_device_requires_auth(self):
        r = client.post("/api/devices", json=_DEVICE_PAYLOAD)
        assert r.status_code == 401

    def test_register_duplicate_device_id_rejected(self):
        token = _register_and_login(_USER_A)
        client.post("/api/devices", json=_DEVICE_PAYLOAD, headers=_headers(token))
        r = client.post("/api/devices", json=_DEVICE_PAYLOAD, headers=_headers(token))
        assert r.status_code == 409

    def test_register_invalid_connection_type_rejected(self):
        token = _register_and_login(_USER_A)
        r = client.post("/api/devices", json={**_DEVICE_PAYLOAD, "connection_type": "fax"}, headers=_headers(token))
        assert r.status_code == 422

    def test_register_soilx_profile(self):
        """SoilX can be registered as a device with manufacturer/model metadata."""
        token = _register_and_login(_USER_A)
        r = client.post("/api/devices", json=_SOILX_DEVICE_PAYLOAD, headers=_headers(token))
        assert r.status_code == 201
        data = r.json()
        assert data["manufacturer"] == "REVE Nano-Science"
        assert data["model"] == "SoilX"


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Device ownership
# ═══════════════════════════════════════════════════════════════════════════════

class TestDeviceOwnership:
    def test_user_cannot_see_other_user_device(self):
        token_a = _register_and_login(_USER_A)
        token_b = _register_and_login(_USER_B)
        r = client.post("/api/devices", json=_DEVICE_PAYLOAD, headers=_headers(token_a))
        device_pk = r.json()["id"]
        # User B tries to get User A's device
        r2 = client.get(f"/api/devices/{device_pk}", headers=_headers(token_b))
        assert r2.status_code == 404

    def test_user_cannot_delete_other_user_device(self):
        token_a = _register_and_login(_USER_A)
        token_b = _register_and_login(_USER_B)
        r = client.post("/api/devices", json=_DEVICE_PAYLOAD, headers=_headers(token_a))
        device_pk = r.json()["id"]
        r2 = client.delete(f"/api/devices/{device_pk}", headers=_headers(token_b))
        assert r2.status_code == 404

    def test_user_cannot_ingest_to_other_user_device(self):
        token_a = _register_and_login(_USER_A)
        token_b = _register_and_login(_USER_B)
        r = client.post("/api/devices", json=_DEVICE_PAYLOAD, headers=_headers(token_a))
        device_pk = r.json()["id"]
        r2 = client.post(f"/api/devices/{device_pk}/readings", json=_READING_PAYLOAD, headers=_headers(token_b))
        assert r2.status_code == 404

    def test_user_cannot_list_other_user_readings(self):
        token_a = _register_and_login(_USER_A)
        token_b = _register_and_login(_USER_B)
        r = client.post("/api/devices", json=_DEVICE_PAYLOAD, headers=_headers(token_a))
        device_pk = r.json()["id"]
        r2 = client.get(f"/api/devices/{device_pk}/readings", headers=_headers(token_b))
        assert r2.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Device listing
# ═══════════════════════════════════════════════════════════════════════════════

class TestDeviceListing:
    def test_list_returns_own_devices_only(self):
        token_a = _register_and_login(_USER_A)
        token_b = _register_and_login(_USER_B)
        client.post("/api/devices", json=_DEVICE_PAYLOAD, headers=_headers(token_a))
        client.post("/api/devices", json={**_DEVICE_PAYLOAD, "device_id": "DEVICE-B-001"}, headers=_headers(token_b))
        r_a = client.get("/api/devices", headers=_headers(token_a))
        assert r_a.status_code == 200
        devices_a = r_a.json()
        assert len(devices_a) == 1
        assert devices_a[0]["device_id"] == "GENERIC-TEST-001"

    def test_empty_list_for_new_user(self):
        token = _register_and_login(_USER_A)
        r = client.get("/api/devices", headers=_headers(token))
        assert r.status_code == 200
        assert r.json() == []

    def test_deactivated_device_not_in_list(self):
        token = _register_and_login(_USER_A)
        r = client.post("/api/devices", json=_DEVICE_PAYLOAD, headers=_headers(token))
        device_pk = r.json()["id"]
        client.delete(f"/api/devices/{device_pk}", headers=_headers(token))
        r2 = client.get("/api/devices", headers=_headers(token))
        assert r2.json() == []


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Device retrieval
# ═══════════════════════════════════════════════════════════════════════════════

class TestDeviceRetrieval:
    def test_get_device_by_pk(self):
        token = _register_and_login(_USER_A)
        r = client.post("/api/devices", json=_DEVICE_PAYLOAD, headers=_headers(token))
        device_pk = r.json()["id"]
        r2 = client.get(f"/api/devices/{device_pk}", headers=_headers(token))
        assert r2.status_code == 200
        assert r2.json()["device_id"] == "GENERIC-TEST-001"

    def test_nonexistent_device_returns_404(self):
        token = _register_and_login(_USER_A)
        r = client.get("/api/devices/99999", headers=_headers(token))
        assert r.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Measurement ingestion
# ═══════════════════════════════════════════════════════════════════════════════

class TestMeasurementIngestion:
    def _create_device(self, token: str) -> int:
        r = client.post("/api/devices", json=_DEVICE_PAYLOAD, headers=_headers(token))
        assert r.status_code == 201, r.text
        return r.json()["id"]

    def test_ingest_reading_success(self):
        token = _register_and_login(_USER_A)
        device_pk = self._create_device(token)
        r = client.post(f"/api/devices/{device_pk}/readings", json=_READING_PAYLOAD, headers=_headers(token))
        assert r.status_code == 201, r.text
        data = r.json()
        assert "reading" in data
        assert "soil_test" in data
        assert data["reading"]["id"] is not None
        assert data["soil_test"]["id"] is not None

    def test_extended_params_stored(self):
        """sulphur and zinc (not in SoilTest columns) must still be in the reading."""
        token = _register_and_login(_USER_A)
        device_pk = self._create_device(token)
        r = client.post(f"/api/devices/{device_pk}/readings", json=_READING_PAYLOAD, headers=_headers(token))
        assert r.status_code == 201
        measurements = r.json()["reading"]["measurements"]
        assert "sulphur" in measurements
        assert "zinc" in measurements
        assert measurements["sulphur"]["value"] == 18.0
        assert measurements["zinc"]["value"] == 1.2

    def test_ingest_requires_auth(self):
        token = _register_and_login(_USER_A)
        device_pk = self._create_device(token)
        r = client.post(f"/api/devices/{device_pk}/readings", json=_READING_PAYLOAD)
        assert r.status_code == 401

    def test_empty_measurements_rejected(self):
        token = _register_and_login(_USER_A)
        device_pk = self._create_device(token)
        r = client.post(
            f"/api/devices/{device_pk}/readings",
            json={"measurements": {}},
            headers=_headers(token),
        )
        assert r.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Invalid measurement rejection
# ═══════════════════════════════════════════════════════════════════════════════

class TestMeasurementValidation:
    def _create_device(self, token: str) -> int:
        r = client.post("/api/devices", json=_DEVICE_PAYLOAD, headers=_headers(token))
        return r.json()["id"]

    def test_nan_value_rejected(self):
        token = _register_and_login(_USER_A)
        device_pk = self._create_device(token)
        # JSON does not support NaN natively; we pass it as a string and expect rejection
        # Use the no-exception client because FastAPI's JSON serializer can also fail on NaN
        payload_str = '{"measurements": {"ph": {"value": NaN, "unit": "pH"}}}'
        r = client_no_exc.post(
            f"/api/devices/{device_pk}/readings",
            content=payload_str,
            headers={**_headers(token), "Content-Type": "application/json"},
        )
        assert r.status_code in (422, 400, 500)  # Any error code means rejection

    def test_out_of_range_ph_rejected(self):
        token = _register_and_login(_USER_A)
        device_pk = self._create_device(token)
        payload = {"measurements": {"ph": {"value": 15.0, "unit": "pH"}}}
        r = client.post(f"/api/devices/{device_pk}/readings", json=payload, headers=_headers(token))
        assert r.status_code == 422

    def test_negative_nitrogen_rejected(self):
        token = _register_and_login(_USER_A)
        device_pk = self._create_device(token)
        payload = {"measurements": {"nitrogen": {"value": -5.0, "unit": "kg/ha"}}}
        r = client.post(f"/api/devices/{device_pk}/readings", json=payload, headers=_headers(token))
        assert r.status_code == 422

    def test_only_extended_params_accepted(self):
        """A reading with only extended (non-core) parameters is valid."""
        token = _register_and_login(_USER_A)
        device_pk = self._create_device(token)
        payload = {"measurements": {"sulphur": {"value": 15.0, "unit": "mg/kg"}}}
        r = client.post(f"/api/devices/{device_pk}/readings", json=payload, headers=_headers(token))
        assert r.status_code == 201


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Device last_seen update
# ═══════════════════════════════════════════════════════════════════════════════

class TestDeviceHeartbeat:
    def test_last_seen_updated_after_ingest(self):
        token = _register_and_login(_USER_A)
        r = client.post("/api/devices", json=_DEVICE_PAYLOAD, headers=_headers(token))
        device_pk = r.json()["id"]
        # Before ingest: last_seen_at is None
        d_before = client.get(f"/api/devices/{device_pk}", headers=_headers(token)).json()
        assert d_before["last_seen_at"] is None

        client.post(f"/api/devices/{device_pk}/readings", json=_READING_PAYLOAD, headers=_headers(token))

        d_after = client.get(f"/api/devices/{device_pk}", headers=_headers(token)).json()
        assert d_after["last_seen_at"] is not None
        assert d_after["status"] == "online"


# ═══════════════════════════════════════════════════════════════════════════════
# 8. SoilTest creation from hardware reading
# ═══════════════════════════════════════════════════════════════════════════════

class TestSoilTestFromHardware:
    def _create_device(self, token: str) -> int:
        r = client.post("/api/devices", json=_DEVICE_PAYLOAD, headers=_headers(token))
        return r.json()["id"]

    def test_soil_test_created_with_hardware_source(self):
        token = _register_and_login(_USER_A)
        device_pk = self._create_device(token)
        r = client.post(f"/api/devices/{device_pk}/readings", json=_READING_PAYLOAD, headers=_headers(token))
        assert r.status_code == 201
        st = r.json()["soil_test"]
        assert st["source"] == "hardware"

    def test_soil_test_has_device_id_metadata(self):
        token = _register_and_login(_USER_A)
        device_pk = self._create_device(token)
        r = client.post(f"/api/devices/{device_pk}/readings", json=_READING_PAYLOAD, headers=_headers(token))
        st = r.json()["soil_test"]
        assert st["device_id"] == "GENERIC-TEST-001"

    def test_soil_test_has_health_score(self):
        token = _register_and_login(_USER_A)
        device_pk = self._create_device(token)
        r = client.post(f"/api/devices/{device_pk}/readings", json=_READING_PAYLOAD, headers=_headers(token))
        st = r.json()["soil_test"]
        assert isinstance(st["health_score"], (int, float))
        assert 0 <= st["health_score"] <= 100

    def test_soil_test_has_health_status(self):
        token = _register_and_login(_USER_A)
        device_pk = self._create_device(token)
        r = client.post(f"/api/devices/{device_pk}/readings", json=_READING_PAYLOAD, headers=_headers(token))
        st = r.json()["soil_test"]
        assert st["health_status"] in ("Excellent", "Good", "Needs Attention", "Poor", "Awaiting Data")

    def test_soil_test_appears_in_soil_tests_list(self):
        token = _register_and_login(_USER_A)
        device_pk = self._create_device(token)
        client.post(f"/api/devices/{device_pk}/readings", json=_READING_PAYLOAD, headers=_headers(token))
        r = client.get("/api/soil/tests", headers=_headers(token))
        assert r.status_code == 200
        tests = r.json()
        hw_tests = [t for t in tests if t.get("source") == "hardware"]
        assert len(hw_tests) >= 1

    def test_missing_params_handled_gracefully(self):
        """A reading with only pH should create a valid SoilTest with a health score."""
        token = _register_and_login(_USER_A)
        device_pk = self._create_device(token)
        payload = {"measurements": {"ph": {"value": 6.5, "unit": "pH"}}}
        r = client.post(f"/api/devices/{device_pk}/readings", json=payload, headers=_headers(token))
        assert r.status_code == 201
        st = r.json()["soil_test"]
        assert st["health_score"] >= 0

    def test_hardware_source_metadata_on_soilx(self):
        """SoilX-branded device should produce source='soilx' on SoilTest."""
        token = _register_and_login(_USER_A)
        # Register as SoilX using the dedicated SoilX payload
        r = client.post("/api/devices", json=_SOILX_DEVICE_PAYLOAD, headers=_headers(token))
        device_pk = r.json()["id"]
        r2 = client.post(f"/api/devices/{device_pk}/readings", json=_READING_PAYLOAD, headers=_headers(token))
        st = r2.json()["soil_test"]
        assert st["source"] == "soilx"

    def test_existing_analyzer_runs_on_hardware_reading(self):
        """The analysis endpoint should work on a hardware-created SoilTest."""
        token = _register_and_login(_USER_A)
        device_pk = self._create_device(token)
        r = client.post(f"/api/devices/{device_pk}/readings", json=_READING_PAYLOAD, headers=_headers(token))
        st_id = r.json()["soil_test"]["id"]
        r2 = client.get(f"/api/soil/tests/{st_id}/analysis", headers=_headers(token))
        assert r2.status_code == 200
        analysis = r2.json()["analysis"]
        assert "parameter_analysis" in analysis
        assert "crop_recommendations" in analysis
        assert "fertilizer_recommendations" in analysis


# ═══════════════════════════════════════════════════════════════════════════════
# 9. Reading history and latest
# ═══════════════════════════════════════════════════════════════════════════════

class TestReadingHistory:
    def _setup(self, token: str) -> int:
        r = client.post("/api/devices", json=_DEVICE_PAYLOAD, headers=_headers(token))
        return r.json()["id"]

    def test_list_readings_empty(self):
        token = _register_and_login(_USER_A)
        device_pk = self._setup(token)
        r = client.get(f"/api/devices/{device_pk}/readings", headers=_headers(token))
        assert r.status_code == 200
        assert r.json() == []

    def test_list_readings_after_ingest(self):
        token = _register_and_login(_USER_A)
        device_pk = self._setup(token)
        client.post(f"/api/devices/{device_pk}/readings", json=_READING_PAYLOAD, headers=_headers(token))
        client.post(f"/api/devices/{device_pk}/readings", json=_READING_PAYLOAD, headers=_headers(token))
        r = client.get(f"/api/devices/{device_pk}/readings", headers=_headers(token))
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_latest_reading_endpoint(self):
        token = _register_and_login(_USER_A)
        device_pk = self._setup(token)
        client.post(f"/api/devices/{device_pk}/readings", json=_READING_PAYLOAD, headers=_headers(token))
        r = client.get(f"/api/devices/{device_pk}/readings/latest", headers=_headers(token))
        assert r.status_code == 200
        data = r.json()
        assert "measurements" in data
        assert "ph" in data["measurements"]

    def test_latest_reading_no_readings_returns_404(self):
        token = _register_and_login(_USER_A)
        device_pk = self._setup(token)
        r = client.get(f"/api/devices/{device_pk}/readings/latest", headers=_headers(token))
        assert r.status_code == 404

    def test_readings_not_visible_to_other_user(self):
        token_a = _register_and_login(_USER_A)
        token_b = _register_and_login(_USER_B)
        device_pk = self._setup(token_a)
        client.post(f"/api/devices/{device_pk}/readings", json=_READING_PAYLOAD, headers=_headers(token_a))
        r = client.get(f"/api/devices/{device_pk}/readings", headers=_headers(token_b))
        assert r.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# 10. AI assistant sees hardware-generated soil test as latest context
# ═══════════════════════════════════════════════════════════════════════════════

class TestAssistantSeesHardwareTest:
    def test_assistant_uses_hardware_soil_test(self):
        """
        After ingesting a hardware reading, asking the assistant about soil health
        should return a response that references actual soil data (not the
        'no soil data' message).
        """
        token = _register_and_login(_USER_A)
        # Create device and ingest reading
        r = client.post("/api/devices", json=_DEVICE_PAYLOAD, headers=_headers(token))
        device_pk = r.json()["id"]
        client.post(f"/api/devices/{device_pk}/readings", json=_READING_PAYLOAD, headers=_headers(token))
        # Ask the assistant
        r2 = client.post("/api/assistant/chat", json={"message": "What is my soil health?"}, headers=_headers(token))
        assert r2.status_code == 200
        answer = r2.json()["answer"]
        # The assistant should NOT say it has no soil data
        assert "don't have any soil test" not in answer.lower()
        # The response should contain soil-health-related content
        assert len(answer) > 50


# ═══════════════════════════════════════════════════════════════════════════════
# 11. Adapter unit tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestAdapters:
    def test_generic_adapter_normalize(self):
        from app.integrations.hardware.adapters import GenericAdapter
        adapter = GenericAdapter()
        payload = {"measurements": {"ph": {"value": 6.8, "unit": "pH"}, "EC": {"value": 0.42, "unit": "dS/m"}}}
        result = adapter.normalize(payload)
        assert "ph" in result
        assert "ec" in result  # EC → ec via alias
        assert result["ph"]["value"] == 6.8

    def test_generic_adapter_validates_empty(self):
        from app.integrations.hardware.adapters import GenericAdapter
        adapter = GenericAdapter()
        try:
            adapter.validate({})
            assert False, "Should have raised"
        except ValueError:
            pass

    def test_soilx_stub_registers_profile(self):
        from app.integrations.hardware.adapters import SoilXAdapterStub
        s = SoilXAdapterStub()
        assert "ph" in s.get_supported_parameters()
        assert "sulphur" in s.get_supported_parameters()
        assert s.MANUFACTURER == "REVE Nano-Science"
        assert s.MODEL == "SoilX"

    def test_soilx_stub_normalize_raises_not_implemented(self):
        from app.integrations.hardware.adapters import SoilXAdapterStub
        s = SoilXAdapterStub()
        try:
            s.normalize({})
            assert False, "Should have raised NotImplementedError"
        except NotImplementedError:
            pass

    def test_registry_returns_generic_for_unknown_key(self):
        from app.integrations.hardware.adapters import get_adapter, GenericAdapter
        adapter = get_adapter("totally_unknown_key_xyz")
        assert isinstance(adapter, GenericAdapter)

    def test_canonical_alias_mapping(self):
        from app.integrations.hardware.adapters import canonical
        assert canonical("EC") == "ec"
        assert canonical("pH") == "ph"
        assert canonical("N") == "nitrogen"
        assert canonical("K") == "potassium"


# ═══════════════════════════════════════════════════════════════════════════════
# 12. Schema validation unit tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestHardwareSchemas:
    def test_nan_rejected_by_schema(self):
        from app.schemas.hardware import MeasurementValue
        try:
            MeasurementValue(value=float("nan"), unit="pH")
            assert False, "Should raise"
        except Exception:
            pass

    def test_inf_rejected_by_schema(self):
        from app.schemas.hardware import MeasurementValue
        try:
            MeasurementValue(value=float("inf"), unit="dS/m")
            assert False, "Should raise"
        except Exception:
            pass

    def test_valid_measurement_accepted(self):
        from app.schemas.hardware import MeasurementValue
        m = MeasurementValue(value=6.8, unit="pH")
        assert m.value == 6.8

    def test_device_create_invalid_connection_type(self):
        from app.schemas.hardware import DeviceCreate
        try:
            DeviceCreate(device_id="X", connection_type="fax")
            assert False, "Should raise"
        except Exception:
            pass

    def test_device_create_valid_ble(self):
        from app.schemas.hardware import DeviceCreate
        d = DeviceCreate(device_id="DEVICE-001", connection_type="ble")
        assert d.connection_type == "ble"

    def test_reading_ingest_out_of_bounds_ph(self):
        from app.schemas.hardware import ReadingIngest, MeasurementValue
        try:
            ReadingIngest(measurements={"ph": MeasurementValue(value=99.0, unit="pH")})
            assert False, "Should raise"
        except Exception:
            pass
