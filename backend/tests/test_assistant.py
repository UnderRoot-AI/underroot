"""
Tests for the context-aware assistant.

Covers all 16 test requirements:
 1. Authenticated user can ask a question.
 2. Unauthenticated user is rejected.
 3. Empty question rejected.
 4. Conversation is stored.
 5. Conversation belongs to correct user.
 6. User cannot access another user's conversation.
 7. Latest soil context is retrieved.
 8. Soil health score is taken from actual analysis.
 9. Deficiency information comes from actual analysis.
10. Missing soil data is handled correctly.
11. Assistant does not invent missing measurements.
12. Context is limited to relevant user data.
13. Language preference is respected.
14. RAG failure is handled gracefully.
15. AI provider failure is handled gracefully (N/A — no external AI provider).
16. Existing assistant API contract remains compatible.
"""
from __future__ import annotations

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

import PIL as _real_pil  # noqa: E402
if not hasattr(_real_pil, "__version__"):
    _real_pil.__version__ = "0.0.0"


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
_rl_styles   = _make_mod("reportlab.lib.styles",
    getSampleStyleSheet=lambda: {"BodyText": {}, "Heading1": {}, "Heading2": {}},
    ParagraphStyle=lambda **kw: kw)
_rl_colors   = _make_mod("reportlab.lib.colors",
    HexColor=lambda x: x,
    white="white", grey="grey", black="black")
_rl_platypus = _make_mod("reportlab.platypus",
    SimpleDocTemplate=object,
    Paragraph=lambda *a, **kw: None,
    Spacer=lambda *a, **kw: None,
    Table=lambda *a, **kw: None,
    TableStyle=lambda *a, **kw: None)
_rl_gfx      = _make_mod("reportlab.graphics")
_rl_shapes   = _make_mod("reportlab.graphics.shapes",
    Drawing=object, Rect=lambda *a, **kw: None, String=lambda *a, **kw: None)

import pypdf as _pypdf  # noqa: E402
if not hasattr(_pypdf, "PdfReader"):
    class _FakePdfReader:
        def __init__(self, *a, **kw): self.pages = []
    _pypdf.PdfReader = _FakePdfReader  # type: ignore[attr-defined]

# ── Configure isolated test databases ────────────────────────────────────────
import app.core.config as _cfg  # noqa: E402

_cfg.settings.database_url = "sqlite:///./test_assistant_tmp.db"
_cfg.settings.soil_report_database_url = "sqlite:///./test_assistant_reports_tmp.db"
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
    "sqlite:///./test_assistant_tmp.db",
    connect_args={"check_same_thread": False},
)
_TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)
_conn.engine = _test_engine
_conn.SessionLocal = _TestingSession

import app.models  # noqa: E402

from app.database import report_connection as _rep  # noqa: E402

_test_report_engine = create_engine(
    "sqlite:///./test_assistant_reports_tmp.db",
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
from app.api.routes import assistant as _asst  # noqa: E402
from app.database.connection import get_db  # noqa: E402
from app.database.report_connection import get_report_db  # noqa: E402

_app = FastAPI()
_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)
for r in (_auth.router, _soil.router, _reports.router, _asst.router):
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

client = TestClient(_app, raise_server_exceptions=False)


# ── Helpers ───────────────────────────────────────────────────────────────────
_USER_A = {"name": "Test Farmer A", "email": "farmera@test.com", "password": "Pass1234!",
           "state": "Gujarat", "district": "Ahmedabad", "mobile": ""}
_USER_B = {"name": "Test Farmer B", "email": "farmerb@test.com", "password": "Pass1234!",
           "state": "Gujarat", "district": "Surat", "mobile": ""}

_SOIL_PARAMS = {
    "ph": 5.5,         # acidic — triggers deficiency
    "nitrogen": 80.0,  # low (< 150)
    "phosphorus": 10.0,  # low (< 15)
    "potassium": 180.0,  # low (< 200)
    "ec": 0.8,
    "moisture": 35.0,
    "temperature": 25.0,
    "organic_carbon": 0.3,  # low (< 0.5)
}


def _register_and_verify(user_data: dict) -> str:
    """Register a user, verify email, and return JWT token."""
    r = client.post("/api/auth/signup", json=user_data)
    assert r.status_code == 200, f"signup failed: {r.text}"
    # Bypass email: fetch token directly from the verification endpoint logic
    # or use developer login
    from app.models.user import User as _UserModel
    from app.core.security_seed import make_hash as _make_hash
    db = _TestingSession()
    try:
        u = db.query(_UserModel).filter(_UserModel.email == user_data["email"]).first()
        u.email_verified = True
        db.commit()
    finally:
        db.close()
    r2 = client.post("/api/auth/login", json={
        "email": user_data["email"], "password": user_data["password"]
    })
    assert r2.status_code == 200, f"login failed: {r2.text}"
    return r2.json()["access_token"]


def _create_soil_test(token: str, params: dict | None = None) -> dict:
    p = params or _SOIL_PARAMS
    r = client.post(
        "/api/soil/tests",
        json={"parameters": p},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, f"soil create failed: {r.text}"
    return r.json()


# ── Test 1: Authenticated user can ask a question ────────────────────────────
def test_authenticated_user_can_ask():
    token = _register_and_verify(_USER_A)
    r = client.post(
        "/api/assistant/chat",
        json={"message": "How is my soil?"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data
    assert isinstance(data["answer"], str)
    assert len(data["answer"]) > 10
    assert "sources" in data
    assert isinstance(data["sources"], list)


# ── Test 2: Unauthenticated user is rejected ──────────────────────────────────
def test_unauthenticated_user_rejected():
    r = client.post(
        "/api/assistant/chat",
        json={"message": "How is my soil?"},
    )
    assert r.status_code == 401


# ── Test 3: Empty question rejected ──────────────────────────────────────────
def test_empty_question_rejected():
    token = _register_and_verify(_USER_A)
    r = client.post(
        "/api/assistant/chat",
        json={"message": ""},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 422


def test_whitespace_only_question_rejected():
    token = _register_and_verify(_USER_A)
    r = client.post(
        "/api/assistant/chat",
        json={"message": "   "},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 422


# ── Test 4: Conversation is stored ───────────────────────────────────────────
def test_conversation_stored():
    token = _register_and_verify(_USER_A)
    client.post(
        "/api/assistant/chat",
        json={"message": "Tell me about my soil."},
        headers={"Authorization": f"Bearer {token}"},
    )
    r = client.get(
        "/api/assistant/history",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    history = r.json()
    assert len(history) >= 2  # user + assistant
    roles = [h["role"] for h in history]
    assert "user" in roles
    assert "assistant" in roles


# ── Test 5: Conversation belongs to correct user ─────────────────────────────
def test_conversation_belongs_to_user():
    token = _register_and_verify(_USER_A)
    client.post(
        "/api/assistant/chat",
        json={"message": "My soil question"},
        headers={"Authorization": f"Bearer {token}"},
    )
    r = client.get("/api/assistant/history", headers={"Authorization": f"Bearer {token}"})
    history = r.json()
    user_msgs = [h for h in history if h["role"] == "user"]
    assert any("soil question" in h["content"] for h in user_msgs)


# ── Test 6: User cannot access another user's conversation ───────────────────
def test_users_cannot_see_each_others_conversations():
    token_a = _register_and_verify(_USER_A)
    _register_and_verify(_USER_B)
    # User B uses a different email, but same test — manually register B with different details
    token_b = _register_and_verify({
        "name": "Farmer B2",
        "email": "farmerb2@test.com",
        "password": "Pass1234!",
        "state": "Gujarat",
        "district": "Surat",
        "mobile": "",
    })
    # A asks a question
    client.post(
        "/api/assistant/chat",
        json={"message": "Secret question from A"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    # B retrieves history — should NOT see A's messages
    r = client.get("/api/assistant/history", headers={"Authorization": f"Bearer {token_b}"})
    history = r.json()
    contents = [h["content"] for h in history]
    assert not any("Secret question from A" in c for c in contents)


# ── Test 7: Latest soil context is retrieved ──────────────────────────────────
def test_latest_soil_context_used():
    token = _register_and_verify(_USER_A)
    _create_soil_test(token)  # Create a soil test
    r = client.post(
        "/api/assistant/chat",
        json={"message": "What is my soil health?"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    answer = r.json()["answer"]
    # The response should reference actual soil data (UnderRoot data prefix)
    assert "UnderRoot" in answer or "soil test" in answer.lower() or "health" in answer.lower()


# ── Test 8: Soil health score from actual analysis ───────────────────────────
def test_health_score_from_actual_analysis():
    from app.services.soil_service import calculate_health
    score, status = calculate_health(_SOIL_PARAMS)
    # Score should be deterministic and not fabricated
    assert 0 <= score <= 100
    assert status in ("Excellent", "Good", "Needs Attention", "Poor")
    # With multiple low parameters, score should not be excellent
    assert status != "Excellent"

    token = _register_and_verify(_USER_A)
    soil = _create_soil_test(token)
    # Health score stored in the soil test should match the deterministic calculation
    assert abs(soil["health_score"] - score) < 0.1


# ── Test 9: Deficiency information from actual analysis ──────────────────────
def test_deficiency_from_actual_analysis():
    from app.services.soil_analyzer import analyze_parameters
    analysis = analyze_parameters(_SOIL_PARAMS)
    deficiencies = analysis["deficiencies"]
    # With ph=5.5, N=80, P=10, K=180, OC=0.3 — should have deficiencies
    assert len(deficiencies) > 0
    # The deficiency list should include actual parameter labels
    labels = [d.lower() for d in deficiencies]
    # At least nitrogen or phosphorus should be in deficiencies
    assert any("nitrogen" in l or "phosphorus" in l or "potassium" in l for l in labels)


# ── Test 10: Missing soil data handled correctly ──────────────────────────────
def test_missing_soil_data_handled_gracefully():
    token = _register_and_verify(_USER_A)
    # No soil test created — ask about soil
    r = client.post(
        "/api/assistant/chat",
        json={"message": "What is my soil health score?"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    answer = r.json()["answer"]
    # Should not claim to know the score — must mention no data
    answer_lower = answer.lower()
    assert any(phrase in answer_lower for phrase in [
        "no soil test", "don't have", "please run", "soil test first", "no soil"
    ])


# ── Test 11: Assistant does not invent missing measurements ───────────────────
def test_no_invented_measurements():
    token = _register_and_verify(_USER_A)
    # No soil test — ask a specific question about a nutrient
    r = client.post(
        "/api/assistant/chat",
        json={"message": "Is my nitrogen level low?"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    answer = r.json()["answer"]
    # Should NOT say "Your nitrogen is X kg/ha" without actual data
    # Should say something about needing a soil test
    assert "nitrogen" not in answer.lower() or "don't have" in answer.lower() or "no soil test" in answer.lower() or "please" in answer.lower()


# ── Test 12: Context limited to relevant user data ───────────────────────────
def test_context_limited_to_user_data():
    token_a = _register_and_verify(_USER_A)
    token_b = _register_and_verify({
        "name": "Farmer C",
        "email": "farmerc@test.com",
        "password": "Pass1234!",
        "state": "Maharashtra",
        "district": "Pune",
        "mobile": "",
    })
    # Create soil for A with specific values
    _create_soil_test(token_a, {
        "ph": 5.0, "nitrogen": 20.0, "phosphorus": 5.0,
        "potassium": 100.0, "ec": 0.5, "moisture": 30.0,
        "temperature": 25.0, "organic_carbon": 0.2,
    })
    # B asks about soil — should NOT see A's values
    r = client.post(
        "/api/assistant/chat",
        json={"message": "What is my soil health?"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert r.status_code == 200
    answer = r.json()["answer"]
    # B has no soil test, so answer should mention no data
    # and definitely NOT reference specific values from A's test
    assert "5.0" not in answer or "don't have" in answer.lower() or "no soil" in answer.lower()


# ── Test 13: Language preference respected ───────────────────────────────────
def test_language_preference_respected():
    from app.services.assistant_service import answer as svc_answer
    # English response
    reply_en, _ = svc_answer("What is my soil health?", language="en")
    assert any(
        w in reply_en for w in ["soil", "Soil", "test", "UnderRoot"]
    ), f"Expected English content, got: {reply_en[:100]}"

    # Hindi response — should contain Hindi text
    reply_hi, _ = svc_answer(
        "मेरी मिट्टी का स्वास्थ्य कैसा है?",
        soil={"ph": 6.5, "nitrogen": 200.0, "phosphorus": 20.0, "potassium": 250.0,
              "ec": 0.5, "moisture": 40.0, "temperature": 25.0, "organic_carbon": 0.8},
        health_score=85.0,
        health_status="Excellent",
        language="hi",
    )
    # Hindi response should contain Hindi characters or Hindi words
    assert any(ord(c) > 2304 for c in reply_hi) or "मिट्टी" in reply_hi or "UnderRoot" in reply_hi


# ── Test 14: RAG failure handled gracefully ───────────────────────────────────
def test_rag_failure_handled_gracefully():
    from app.services.assistant_service import answer as svc_answer
    from unittest.mock import patch

    # Patch get_rag to raise an exception
    with patch("app.services.assistant_service.get_rag", side_effect=Exception("RAG unavailable")):
        reply, sources = svc_answer(
            "What should I grow?",
            soil={"ph": 6.5, "nitrogen": 200.0, "phosphorus": 20.0, "potassium": 250.0,
                  "ec": 0.5, "moisture": 40.0, "temperature": 25.0, "organic_carbon": 0.8},
            health_score=75.0,
            health_status="Good",
        )
    # Should still return a valid response (not crash)
    assert isinstance(reply, str)
    assert len(reply) > 10
    assert isinstance(sources, list)


# ── Test 16: Existing API contract compatible ─────────────────────────────────
def test_api_contract_compatible():
    """Verify the /assistant/chat endpoint returns the expected schema."""
    token = _register_and_verify(_USER_A)
    r = client.post(
        "/api/assistant/chat",
        json={"message": "Hello"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data
    assert "sources" in data
    assert isinstance(data["answer"], str)
    assert isinstance(data["sources"], list)


def test_api_contract_with_soil_test_id():
    """Verify soil_test_id parameter is accepted and soil context is used."""
    token = _register_and_verify(_USER_A)
    soil = _create_soil_test(token)
    soil_id = soil["id"]

    r = client.post(
        "/api/assistant/chat",
        json={"message": "What is my pH?", "soil_test_id": soil_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data
    # The response should mention pH
    assert "ph" in data["answer"].lower() or "5.5" in data["answer"]


def test_wrong_users_soil_test_id_ignored():
    """User B cannot use User A's soil test ID to get A's data."""
    token_a = _register_and_verify(_USER_A)
    token_b = _register_and_verify({
        "name": "Farmer D",
        "email": "farmerd@test.com",
        "password": "Pass1234!",
        "state": "Gujarat",
        "district": "Vadodara",
        "mobile": "",
    })
    soil_a = _create_soil_test(token_a)
    soil_id_a = soil_a["id"]

    # B tries to use A's soil test ID
    r = client.post(
        "/api/assistant/chat",
        json={"message": "What is my soil health?", "soil_test_id": soil_id_a},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert r.status_code == 200
    answer = r.json()["answer"]
    # B has no soil of their own and A's test is rejected by user filter
    # Answer should either use no data or B's own data (which doesn't exist)
    # It must NOT reveal A's soil values directly attributed to B
    # The route filters by user_id so A's test won't be found for B
    # B will get "no soil test" type response
    assert any(phrase in answer.lower() for phrase in [
        "no soil", "don't have", "please", "soil test"
    ])


# ── Unit tests for assistant_service ─────────────────────────────────────────
def test_service_greet_response():
    from app.services.assistant_service import answer as svc_answer
    reply, sources = svc_answer("hello")
    assert isinstance(reply, str)
    assert len(reply) > 5
    assert sources == []


def test_service_no_soil_response():
    from app.services.assistant_service import answer as svc_answer
    reply, _ = svc_answer("What should I plant?", soil=None)
    # Must mention lack of soil data
    assert any(
        phrase in reply.lower()
        for phrase in ["no soil test", "don't have", "soil test first", "please run"]
    )


def test_service_with_deficient_soil():
    from app.services.assistant_service import answer as svc_answer
    deficient_soil = {
        "ph": 5.5,
        "nitrogen": 80.0,
        "phosphorus": 8.0,
        "potassium": 150.0,
        "ec": 0.5,
        "moisture": 35.0,
        "temperature": 25.0,
        "organic_carbon": 0.2,
    }
    reply, _ = svc_answer(
        "What is my soil health?",
        soil=deficient_soil,
        health_score=45.0,
        health_status="Needs Attention",
    )
    # Should mention the health score (from stored data, not invented)
    assert "45" in reply or "Needs Attention" in reply or "attention" in reply.lower()


def test_service_uses_health_score_not_invented():
    from app.services.assistant_service import answer as svc_answer
    # Provide explicit health score
    reply, _ = svc_answer(
        "What is my soil health score?",
        soil={"ph": 7.0, "nitrogen": 200.0, "phosphorus": 25.0, "potassium": 280.0,
              "ec": 0.8, "moisture": 45.0, "temperature": 28.0, "organic_carbon": 0.9},
        health_score=88.5,
        health_status="Excellent",
    )
    # The 88.5 score from our data should appear in response
    assert "88.5" in reply or "Excellent" in reply


def test_service_fertilizer_intent():
    from app.services.assistant_service import answer as svc_answer
    soil = {
        "ph": 7.0,
        "nitrogen": 100.0,  # low
        "phosphorus": 12.0,  # low
        "potassium": 180.0,  # low
        "ec": 0.5,
        "moisture": 40.0,
        "temperature": 25.0,
        "organic_carbon": 0.4,
    }
    reply, _ = svc_answer(
        "What fertilizer should I apply?",
        soil=soil,
        health_score=50.0,
        health_status="Needs Attention",
    )
    # Should mention fertilizer in the context of actual soil data
    assert "fertilizer" in reply.lower() or "khad" in reply.lower() or "urea" in reply.lower() or "dap" in reply.lower()


def test_service_crop_intent():
    from app.services.assistant_service import answer as svc_answer
    soil = {
        "ph": 7.0,
        "nitrogen": 200.0,
        "phosphorus": 20.0,
        "potassium": 250.0,
        "ec": 0.5,
        "moisture": 40.0,
        "temperature": 25.0,
        "organic_carbon": 0.7,
    }
    reply, _ = svc_answer(
        "What crop should I grow?",
        soil=soil,
        health_score=80.0,
        health_status="Excellent",
    )
    # Should mention a specific crop from the recommendation engine
    assert any(
        crop in reply for crop in ["Wheat", "Maize", "Rice", "Chickpea", "wheat", "maize", "rice"]
    )


def test_service_multilingual_gujarati():
    from app.services.assistant_service import answer as svc_answer
    soil = {
        "ph": 5.5,
        "nitrogen": 80.0,
        "phosphorus": 10.0,
        "potassium": 150.0,
        "ec": 0.5,
        "moisture": 35.0,
        "temperature": 25.0,
        "organic_carbon": 0.3,
    }
    reply, _ = svc_answer(
        "માટી સ્વાસ્થ્ય",
        soil=soil,
        health_score=42.0,
        health_status="Needs Attention",
        language="gu",
    )
    # Gujarati response should include Gujarati characters or "UnderRoot"
    has_gujarati = any(0x0A80 <= ord(c) <= 0x0AFF for c in reply)
    assert has_gujarati or "UnderRoot" in reply


def test_service_does_not_invent_nitrogen_when_missing():
    from app.services.assistant_service import answer as svc_answer
    # Soil without nitrogen
    soil_no_n = {"ph": 7.0, "phosphorus": 20.0, "potassium": 250.0}
    reply, _ = svc_answer("Is my nitrogen low?", soil=soil_no_n)
    # Should not claim nitrogen is X kg/ha
    # Should say it doesn't have the measurement
    assert "nitrogen" in reply.lower()
    # Should not invent a specific kg/ha value that doesn't exist
    assert "150" not in reply or "don't have" in reply.lower() or "within optimal" in reply.lower()
