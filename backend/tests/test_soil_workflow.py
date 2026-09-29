"""
Tests for the soil analysis workflow:
  - soil_service.calculate_health (scoring)
  - soil_analyzer.analyze_parameters (parameter analysis)
  - recommendation_service (recommendations driven by soil data)
  - SoilParameters schema validation
  - soil + report API routes (create, analyze, generate report)

These tests do NOT require an active server — they use FastAPI TestClient.
Heavy optional dependencies (ML, OCR, PDF) are stubbed out.
"""
from __future__ import annotations

import json
import sys
import types

# ── Stub out heavy optional dependencies ─────────────────────────────────────
_STUBS = [
    "joblib", "sklearn", "sklearn.preprocessing", "sklearn.ensemble",
    "pytesseract", "fitz",
    "pyserial", "serial", "pandas",
]
for _mod in _STUBS:
    if _mod not in sys.modules:
        sys.modules[_mod] = types.ModuleType(_mod)

# PIL is already installed (Pillow); just ensure version attr exists for pypdf.
import PIL as _real_pil  # noqa: E402
if not hasattr(_real_pil, "__version__"):
    _real_pil.__version__ = "0.0.0"

# ── Stub reportlab sub-modules with required attributes ───────────────────────
def _make_mod(name: str, **attrs):
    m = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    sys.modules[name] = m
    return m

_rl          = _make_mod("reportlab")
_rl_lib      = _make_mod("reportlab.lib")
_rl_ps       = _make_mod("reportlab.lib.pagesizes",  A4=(595.27, 841.89), letter=(612, 792))
_rl_units    = _make_mod("reportlab.lib.units",  mm=2.8346, cm=28.346, inch=72)
class _SS(dict):
    """Minimal StyleSheet1 stub — supports dict access and .add()."""
    def add(self, style, alias=None):
        key = getattr(style, "name", None) or (style.get("name") if isinstance(style, dict) else None)
        if key:
            self[key] = style

def _fake_sss():
    return _SS({"BodyText": {}, "Heading1": {}, "Heading2": {}, "Normal": {}})

class _Noop:
    """Stub for any ReportLab class.

    * Stores all kwargs as attributes so ``ParagraphStyle(name="Foo")`` exposes
      ``.name`` correctly and ``_SS.add()`` can index it.
    * When used as ``BaseDocTemplate`` the first positional arg is the output
      buffer; ``build()`` writes a minimal ``%PDF`` signature so tests can
      assert on the magic bytes.
    """
    def __init__(self, *a, **kw):
        from io import BytesIO as _BIO
        self._buf = a[0] if a and isinstance(a[0], _BIO) else None
        # Expose all kwargs as attributes (e.g. name="RptTitle" → self.name)
        for k, v in kw.items():
            setattr(self, k, v)
    def __call__(self, *a, **kw): return self
    def setStyle(self, *a, **kw): pass
    def build(self, *a, **kw):
        if self._buf is not None:
            self._buf.write(b"%PDF-test\n")
    def addPageTemplates(self, *a, **kw): pass
    def _restrictSize(self, *a, **kw): pass
    imageWidth = 100
    imageHeight = 100

_rl_styles   = _make_mod("reportlab.lib.styles",
    getSampleStyleSheet=_fake_sss,
    ParagraphStyle=_Noop)
_rl_colors   = _make_mod("reportlab.lib.colors",
    HexColor=lambda x: x,
    white="white", grey="grey", black="black")
_rl_platypus = _make_mod("reportlab.platypus",
    SimpleDocTemplate=_Noop, BaseDocTemplate=_Noop,
    Frame=_Noop, PageTemplate=_Noop,
    Paragraph=_Noop, Spacer=_Noop,
    Table=_Noop, TableStyle=_Noop,
    KeepTogether=_Noop, HRFlowable=_Noop,
    Image=_Noop)
_rl_gfx      = _make_mod("reportlab.graphics")
_rl_shapes   = _make_mod("reportlab.graphics.shapes",
    Drawing=object, Rect=lambda *a, **kw: None, String=lambda *a, **kw: None)

# Stub pypdf.PdfReader so OCR client import doesn't fail
import pypdf as _pypdf  # noqa: E402
if not hasattr(_pypdf, "PdfReader"):
    class _FakePdfReader:
        def __init__(self, *a, **kw): self.pages = []
    _pypdf.PdfReader = _FakePdfReader  # type: ignore[attr-defined]

# ── Configure test databases ──────────────────────────────────────────────────
# Use a unique filename so this module never shares data with test_auth_flows.py
import app.core.config as _cfg  # noqa: E402

_cfg.settings.database_url = "sqlite:///./test_soil_workflow_tmp.db"
_cfg.settings.soil_report_database_url = "sqlite:///./test_soil_workflow_reports_tmp.db"
_cfg.settings.smtp_host = ""
_cfg.settings.hardware_mode = "mock"

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
import pytest  # noqa: E402

from app.database import connection as _conn  # noqa: E402
from app.database.connection import Base  # noqa: E402

_test_engine = create_engine(
    "sqlite:///./test_soil_workflow_tmp.db",
    connect_args={"check_same_thread": False},
)
_TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)
_conn.engine = _test_engine
_conn.SessionLocal = _TestingSession

import app.models  # noqa: E402  — register ORM models

from app.database import report_connection as _rep  # noqa: E402

_test_report_engine = create_engine(
    "sqlite:///./test_soil_workflow_reports_tmp.db",
    connect_args={"check_same_thread": False},
)
_rep.report_engine = _test_report_engine
_rep.ReportSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_test_report_engine)

from app.database.report_connection import ReportBase  # noqa: E402
from app.models.soil_report_record import SoilReportRecord  # noqa: E402

Base.metadata.create_all(bind=_test_engine)
ReportBase.metadata.create_all(bind=_test_report_engine)

from app.database.migrations import ensure_soil_test_columns, ensure_report_columns  # noqa: E402
ensure_soil_test_columns()
ensure_report_columns(_test_report_engine)


# ── Fixture: wipe and recreate tables before every integration test ───────────
# Mirrors the autouse fixture in test_auth_flows.py so that each test starts
# with a completely empty database regardless of run order or prior runs.
@pytest.fixture(autouse=True)
def _clean_db():
    Base.metadata.drop_all(bind=_test_engine)
    Base.metadata.create_all(bind=_test_engine)
    ReportBase.metadata.drop_all(bind=_test_report_engine)
    ReportBase.metadata.create_all(bind=_test_report_engine)
    ensure_soil_test_columns()
    ensure_report_columns(_test_report_engine)
    yield
    Base.metadata.drop_all(bind=_test_engine)
    ReportBase.metadata.drop_all(bind=_test_report_engine)

from app.api.routes import auth as _auth, soil as _soil, reports as _reports  # noqa: E402
from app.api.routes import recommendations as _recs, history as _hist  # noqa: E402
from app.database.connection import get_db  # noqa: E402
from app.database.report_connection import get_report_db  # noqa: E402

_app = FastAPI()
_app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
for r in (_auth.router, _soil.router, _reports.router, _recs.router, _hist.router):
    _app.include_router(r, prefix="/api")


def _override_db():
    db = _TestingSession()
    try:
        yield db
    finally:
        db.close()


def _override_report_db():
    db = _rep.ReportSessionLocal()
    try:
        yield db
    finally:
        db.close()


_app.dependency_overrides[get_db] = _override_db
_app.dependency_overrides[get_report_db] = _override_report_db

client = TestClient(_app, raise_server_exceptions=True)

# ── Sample test data (do not hardcode as permanent values) ────────────────────
_SAMPLE_PARAMS = {
    "ph": 7.4,
    "ec": 0.62,
    "nitrogen": 238.0,
    "phosphorus": 19.6,
    "potassium": 286.0,
    "organic_carbon": 0.58,
    "moisture": 24.8,
    "temperature": 27.3,
}


# ── Unit tests: soil_service ──────────────────────────────────────────────────

def test_calculate_health_all_optimal():
    from app.services.soil_service import calculate_health
    score, status = calculate_health({
        "ph": 6.8, "nitrogen": 200, "phosphorus": 30, "potassium": 300,
        "ec": 0.8, "moisture": 40, "temperature": 25, "organic_carbon": 1.0,
    })
    assert score == 100.0
    assert status == "Excellent"


def test_calculate_health_empty():
    from app.services.soil_service import calculate_health
    score, status = calculate_health({})
    assert score == 0.0
    assert status == "Awaiting Data"


def test_calculate_health_ph_only_optimal():
    from app.services.soil_service import calculate_health
    score, status = calculate_health({"ph": 7.0})
    assert score == 100.0


def test_calculate_health_critical_ph():
    from app.services.soil_service import calculate_health
    score, status = calculate_health({"ph": 3.0})
    assert score == 0.0
    assert status == "Poor"


def test_calculate_health_sample_data():
    """Sample data should produce a deterministic, repeatable score."""
    from app.services.soil_service import calculate_health
    score1, _ = calculate_health(_SAMPLE_PARAMS)
    score2, _ = calculate_health(_SAMPLE_PARAMS)
    assert score1 == score2  # deterministic
    assert 0.0 <= score1 <= 100.0


def test_calculate_health_n_low():
    from app.services.soil_service import calculate_health
    score, status = calculate_health({"nitrogen": 30})  # below 150 kg/ha
    # Should be partial, not optimal
    assert score < 100.0


# ── Unit tests: soil_analyzer ─────────────────────────────────────────────────

def test_analyze_parameters_optimal():
    from app.services.soil_analyzer import analyze_parameters
    result = analyze_parameters({"ph": 6.8, "nitrogen": 200})
    ph_r = next(r for r in result["parameter_analysis"] if r["key"] == "ph")
    n_r  = next(r for r in result["parameter_analysis"] if r["key"] == "nitrogen")
    assert ph_r["status"] == "Optimal"
    assert n_r["status"]  == "Optimal"


def test_analyze_parameters_low():
    from app.services.soil_analyzer import analyze_parameters
    result = analyze_parameters({"ph": 5.0})
    ph_r = next(r for r in result["parameter_analysis"] if r["key"] == "ph")
    assert ph_r["status"] == "Low"


def test_analyze_parameters_critical_ph():
    from app.services.soil_analyzer import analyze_parameters
    result = analyze_parameters({"ph": 3.0})
    ph_r = next(r for r in result["parameter_analysis"] if r["key"] == "ph")
    assert ph_r["status"] == "Critical"
    # warnings contains human-readable labels (e.g. "pH"), not internal keys
    assert result["warnings"], "Expected at least one critical warning"
    assert any("pH" in w for w in result["warnings"])


def test_analyze_parameters_missing():
    from app.services.soil_analyzer import analyze_parameters
    result = analyze_parameters({"ph": 7.0})
    # All others should be missing
    missing = result["missing_parameters"]
    assert "nitrogen" in missing


def test_analyze_parameters_deficiencies():
    from app.services.soil_analyzer import analyze_parameters
    result = analyze_parameters({"nitrogen": 50})  # Low
    assert "Nitrogen (N)" in result["deficiencies"]


def test_analyze_parameters_deterministic():
    from app.services.soil_analyzer import analyze_parameters
    r1 = analyze_parameters(_SAMPLE_PARAMS)
    r2 = analyze_parameters(_SAMPLE_PARAMS)
    assert r1 == r2


def test_analyze_units():
    from app.services.soil_analyzer import PARAM_RULES
    assert PARAM_RULES["nitrogen"]["unit"] == "kg/ha"
    assert PARAM_RULES["phosphorus"]["unit"] == "kg/ha"
    assert PARAM_RULES["potassium"]["unit"] == "kg/ha"


# ── Unit tests: schema validation ─────────────────────────────────────────────

def test_schema_invalid_ph():
    from pydantic import ValidationError
    from app.schemas.soil import SoilParameters
    import pytest
    with pytest.raises(ValidationError, match="ph"):
        SoilParameters(ph=20.0)  # above 14


def test_schema_invalid_negative():
    from pydantic import ValidationError
    from app.schemas.soil import SoilParameters
    import pytest
    with pytest.raises(ValidationError):
        SoilParameters(nitrogen=-5.0)


def test_schema_empty_fails():
    from pydantic import ValidationError
    from app.schemas.soil import SoilParameters
    import pytest
    with pytest.raises(ValidationError, match="At least one"):
        SoilParameters()


def test_schema_valid_sample():
    from app.schemas.soil import SoilParameters
    p = SoilParameters(**_SAMPLE_PARAMS)
    assert p.ph == 7.4
    assert p.nitrogen == 238.0


# ── Unit tests: recommendations ───────────────────────────────────────────────

def test_crop_recs_use_ph():
    from app.services.recommendation_service import crop_recommendations
    recs = crop_recommendations({"ph": 5.0})  # acidic
    assert len(recs) > 0
    # Acidic → should not suggest barley (alkaline crop)
    names = [r["crop"] for r in recs]
    assert "Barley" not in names


def test_crop_recs_high_n():
    from app.services.recommendation_service import crop_recommendations
    recs = crop_recommendations({"ph": 7.0, "nitrogen": 200})  # high N
    names = [r["crop"] for r in recs]
    assert "Wheat" in names or "Maize" in names


def test_fertilizer_recs_n_low():
    from app.services.recommendation_service import fertilizer_recommendations
    recs = fertilizer_recommendations({"nitrogen": 50})  # low N
    names = [r["name"] for r in recs]
    assert any("Urea" in n or "DAP" in n for n in names)


def test_fertilizer_recs_oc_low():
    from app.services.recommendation_service import fertilizer_recommendations
    recs = fertilizer_recommendations({"organic_carbon": 0.2})  # very low
    names = [r["name"] for r in recs]
    assert any("Manure" in n or "Compost" in n or "compost" in n or "Gobar" in n for n in names)


# ── Integration tests: API routes ─────────────────────────────────────────────

def _register_and_login(email: str, password: str = "Test@1234"):
    """
    Sign up → extract verification token from verification_url → verify email → login.

    The production auth contract is preserved exactly:
    - POST /api/auth/signup  (fields: name, email, password)
    - GET  /api/auth/verify-email?token=<token>
    - POST /api/auth/login   (fields: email, password)
    Login is blocked for unverified accounts, so verification must succeed first.
    """
    from urllib.parse import urlparse, parse_qs

    # 1. Signup (state + district are now required fields)
    r = client.post("/api/auth/signup", json={
        "email": email, "password": password, "name": "Test User",
        "state": "Gujarat", "district": "Mehsana",
    })
    assert r.status_code in (200, 201), r.text
    data = r.json()

    # 2. Extract token from verification_url (present when SMTP is not configured)
    verification_url = data.get("verification_url")
    assert verification_url, (
        f"verification_url missing from signup response — "
        f"cannot verify email. Response: {data}"
    )
    parsed = urlparse(verification_url)
    token = parse_qs(parsed.query).get("token", [None])[0]
    assert token, f"token not found in verification_url: {verification_url}"

    # 3. Verify email
    vr = client.get("/api/auth/verify-email", params={"token": token})
    assert vr.status_code == 200, f"Email verification failed: {vr.text}"

    # 4. Login
    r2 = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r2.status_code == 200, f"Login failed: {r2.text}"
    return {"Authorization": f"Bearer {r2.json()['access_token']}"}


def test_create_soil_test_and_analyze():
    headers = _register_and_login("soiltest1@example.com")
    payload = {
        "location": "Test Field",
        "parameters": _SAMPLE_PARAMS,
        "notes": "automated test",
    }
    r = client.post("/api/soil/tests", json=payload, headers=headers)
    assert r.status_code == 200, r.text
    test = r.json()
    assert test["health_score"] > 0
    assert test["health_status"] in ("Excellent", "Good", "Needs Attention", "Poor")
    assert test["parameters"]["ph"] == 7.4

    test_id = test["id"]

    # Retrieve
    r2 = client.get(f"/api/soil/tests/{test_id}", headers=headers)
    assert r2.status_code == 200
    assert r2.json()["id"] == test_id

    # Analyze
    r3 = client.get(f"/api/soil/tests/{test_id}/analysis", headers=headers)
    assert r3.status_code == 200
    analysis = r3.json()
    assert "parameter_analysis" in analysis["analysis"]
    assert "crop_recommendations" in analysis["analysis"]
    assert "fertilizer_recommendations" in analysis["analysis"]
    assert "deficiencies" in analysis["analysis"]
    assert "warnings" in analysis["analysis"]


def test_soil_test_invalid_input():
    headers = _register_and_login("soiltest_invalid@example.com")
    # ph out of range
    r = client.post("/api/soil/tests", json={"parameters": {"ph": 20.0}}, headers=headers)
    assert r.status_code == 422

    # no parameters at all
    r2 = client.post("/api/soil/tests", json={"parameters": {}}, headers=headers)
    assert r2.status_code == 422


def test_ownership_enforcement():
    """User A cannot access User B's soil test."""
    headers_a = _register_and_login("owner_a@example.com")
    headers_b = _register_and_login("owner_b@example.com")

    # A creates a test
    r = client.post("/api/soil/tests", json={"parameters": {"ph": 7.0}}, headers=headers_a)
    test_id = r.json()["id"]

    # B tries to access A's test — should fail
    r2 = client.get(f"/api/soil/tests/{test_id}", headers=headers_b)
    assert r2.status_code == 404


def test_history_returns_own_tests():
    headers = _register_and_login("hist_user@example.com")
    # Create two tests
    for _ in range(2):
        client.post("/api/soil/tests", json={"parameters": {"ph": 7.0}}, headers=headers)
    r = client.get("/api/history", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 2
    # All must have required keys
    for item in data:
        assert "id" in item
        assert "health_score" in item
        assert "parameters" in item


def test_list_tests():
    headers = _register_and_login("list_test@example.com")
    client.post("/api/soil/tests", json={"parameters": {"ph": 7.0, "nitrogen": 180}}, headers=headers)
    r = client.get("/api/soil/tests", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_generate_report():
    headers = _register_and_login("report_user@example.com")
    r = client.post("/api/soil/tests", json={"parameters": _SAMPLE_PARAMS, "location": "Report Test"}, headers=headers)
    test_id = r.json()["id"]

    r2 = client.post("/api/reports/generate", json={"soil_test_id": test_id}, headers=headers)
    assert r2.status_code == 200
    report = r2.json()
    assert report["soil_test_id"] == test_id
    assert report["status"] in ("generated", "verified")


def test_recommendations_use_soil_data():
    """Crop recommendations must vary with soil parameters."""
    headers = _register_and_login("rec_user@example.com")

    # Acidic soil
    r = client.post("/api/soil/tests", json={"parameters": {"ph": 5.0}}, headers=headers)
    acid_id = r.json()["id"]

    # Alkaline soil
    r = client.post("/api/soil/tests", json={"parameters": {"ph": 8.5}}, headers=headers)
    alk_id = r.json()["id"]

    r_acid = client.get(f"/api/recommendations/crops?soil_test_id={acid_id}", headers=headers)
    r_alk  = client.get(f"/api/recommendations/crops?soil_test_id={alk_id}", headers=headers)

    assert r_acid.status_code == 200
    assert r_alk.status_code == 200

    crops_acid = [c["crop"] for c in r_acid.json()]
    crops_alk  = [c["crop"] for c in r_alk.json()]

    # Alkaline → Barley or Mustard; Acidic → Potato or Groundnut
    # They should differ (different soils → different recommendations)
    assert set(crops_acid) != set(crops_alk), \
        f"Expected different crops for acid vs alkaline soil but got: {crops_acid} vs {crops_alk}"


# ── PDF download tests ────────────────────────────────────────────────────────
# The ReportLab stub (_Noop) writes b"%PDF-test\n" when build() is called,
# so all assertions below work without a real PDF renderer.

def _setup_test_and_report(email: str):
    """Register user, create a soil test, generate a report, return (headers, test_id, report_id)."""
    headers = _register_and_login(email)
    r = client.post(
        "/api/soil/tests",
        json={"parameters": _SAMPLE_PARAMS, "location": "PDF Test Field"},
        headers=headers,
    )
    assert r.status_code == 200, r.text
    test_id = r.json()["id"]

    r2 = client.post(
        "/api/reports/generate",
        json={"soil_test_id": test_id},
        headers=headers,
    )
    assert r2.status_code == 200, r2.text
    report_id = r2.json()["id"]
    return headers, test_id, report_id


def test_pdf_download_authenticated_owner_200():
    """Authenticated owner gets 200 + application/pdf + Content-Disposition attachment."""
    headers, _, report_id = _setup_test_and_report("pdf_owner@example.com")

    r = client.get(f"/api/reports/{report_id}/pdf", headers=headers)

    assert r.status_code == 200, r.text
    assert r.headers["content-type"] == "application/pdf"
    cd = r.headers.get("content-disposition", "")
    assert "attachment" in cd, f"Expected attachment in Content-Disposition, got: {cd!r}"
    assert "filename" in cd, f"Expected filename in Content-Disposition, got: {cd!r}"


def test_pdf_download_body_starts_with_pdf_magic():
    """Response body starts with the %PDF magic bytes (stub writes b'%PDF-test\\n')."""
    headers, _, report_id = _setup_test_and_report("pdf_magic@example.com")

    r = client.get(f"/api/reports/{report_id}/pdf", headers=headers)

    assert r.status_code == 200
    assert isinstance(r.content, bytes), "Response body must be bytes"
    assert r.content[:4] == b"%PDF", (
        f"Expected body to start with %PDF, got: {r.content[:8]!r}"
    )


def test_pdf_download_unauthenticated_rejected():
    """Request without an Authorization header must be rejected with 401."""
    headers, _, report_id = _setup_test_and_report("pdf_noauth@example.com")

    r = client.get(f"/api/reports/{report_id}/pdf")   # no auth header

    assert r.status_code == 401, f"Expected 401, got {r.status_code}: {r.text}"


def test_pdf_download_nonexistent_report_404():
    """Requesting a report ID that does not exist returns 404."""
    headers = _register_and_login("pdf_noexist@example.com")

    r = client.get("/api/reports/999999/pdf", headers=headers)

    assert r.status_code == 404, f"Expected 404, got {r.status_code}: {r.text}"


def test_pdf_download_other_users_report_forbidden():
    """User B cannot download User A's report — must receive 404 (ownership enforced)."""
    headers_a, _, report_id_a = _setup_test_and_report("pdf_owner_a@example.com")
    headers_b = _register_and_login("pdf_owner_b@example.com")

    r = client.get(f"/api/reports/{report_id_a}/pdf", headers=headers_b)

    assert r.status_code == 404, (
        f"Expected 404 when user B requests user A's report, got {r.status_code}: {r.text}"
    )


def test_pdf_download_report_without_soil_test_404():
    """A report that has no linked soil_test_id returns 404 with a useful detail message."""
    from app.models.report import Report as _R

    headers = _register_and_login("pdf_nostem@example.com")

    # Retrieve user id via a soil test creation then delete the link
    r_st = client.post(
        "/api/soil/tests", json={"parameters": _SAMPLE_PARAMS}, headers=headers
    )
    test_id = r_st.json()["id"]

    r_gen = client.post(
        "/api/reports/generate", json={"soil_test_id": test_id}, headers=headers
    )
    report_id = r_gen.json()["id"]

    # Sever the soil_test_id link directly in the DB
    db = _TestingSession()
    try:
        rpt = db.query(_R).filter(_R.id == report_id).first()
        rpt.soil_test_id = None
        db.commit()
    finally:
        db.close()

    r = client.get(f"/api/reports/{report_id}/pdf", headers=headers)

    assert r.status_code == 404, f"Expected 404 for report without soil test, got {r.status_code}"
    detail = r.json().get("detail", "")
    assert detail, "Expected a non-empty detail message for missing soil test"


def test_pdf_download_invalid_report_id_422():
    """Non-integer path segment for report_id returns 422 (FastAPI path validation)."""
    headers = _register_and_login("pdf_invalid_id@example.com")

    r = client.get("/api/reports/not-a-number/pdf", headers=headers)

    assert r.status_code == 422, f"Expected 422 for non-integer report ID, got {r.status_code}"


def test_pdf_generate_nonexistent_soil_test_404():
    """POST /reports/generate with a soil_test_id that does not belong to the user returns 404."""
    headers = _register_and_login("pdf_gen_notest@example.com")

    r = client.post(
        "/api/reports/generate",
        json={"soil_test_id": 999999},
        headers=headers,
    )

    assert r.status_code == 404, f"Expected 404 for missing soil test, got {r.status_code}: {r.text}"


def test_pdf_download_content_disposition_filename_contains_soil_id():
    """Content-Disposition filename includes the soil test ID."""
    headers, test_id, report_id = _setup_test_and_report("pdf_filename@example.com")

    r = client.get(f"/api/reports/{report_id}/pdf", headers=headers)

    assert r.status_code == 200
    cd = r.headers.get("content-disposition", "")
    assert str(test_id) in cd, (
        f"Expected soil test ID {test_id} in Content-Disposition, got: {cd!r}"
    )
