"""
Soil parameter analysis engine.

All thresholds are centralized in PARAM_RULES.
Units: N/P/K in kg/ha (consistent with frontend soilParameters.ts and PDF report).
Thresholds are indicative ranges for Indian agricultural conditions and are intended
as decision-support screening only — not a substitute for a certified soil lab report.
"""
from __future__ import annotations
from app.services.recommendation_service import crop_recommendations, fertilizer_recommendations

# ── Centralized threshold definitions ────────────────────────────────────────
# Each entry:
#   label  : human-readable name
#   unit   : display unit (consistent with frontend)
#   good   : (low, high) optimal range
#   low    : message when below optimal
#   high   : message when above optimal
#   critical_low  : value below which status = "Critical" (optional)
#   critical_high : value above which status = "Critical" (optional)

PARAM_RULES: dict[str, dict] = {
    "ph": {
        "label": "pH",
        "unit": "",
        "good": (6.0, 7.5),
        "critical_low": 4.5,
        "critical_high": 9.0,
        "low": "Soil is acidic — may limit nutrient availability and beneficial microbial activity.",
        "high": "Soil is alkaline — may reduce availability of phosphorus, iron and zinc.",
    },
    "nitrogen": {
        "label": "Nitrogen (N)",
        "unit": "kg/ha",
        "good": (150, 280),   # medium–high availability range, kg/ha
        "critical_low": 50,
        "critical_high": 600,
        "low": "Nitrogen is low — crop will show pale/yellowing leaves and slow growth.",
        "high": "Nitrogen is very high — may cause excessive vegetative growth and leaching risk.",
    },
    "phosphorus": {
        "label": "Phosphorus (P)",
        "unit": "kg/ha",
        "good": (15, 45),    # medium availability range, kg/ha
        "critical_low": 5,
        "critical_high": 150,
        "low": "Phosphorus is low — root development and early crop growth may be limited.",
        "high": "Phosphorus is very high — may block uptake of zinc and iron.",
    },
    "potassium": {
        "label": "Potassium (K)",
        "unit": "kg/ha",
        "good": (200, 400),  # medium–high availability range, kg/ha
        "critical_low": 80,
        "critical_high": 800,
        "low": "Potassium is low — crop resistance to drought and disease may be reduced.",
        "high": "Potassium is very high — may interfere with uptake of calcium and magnesium.",
    },
    "ec": {
        "label": "Electrical Conductivity (EC)",
        "unit": "dS/m",
        "good": (0.2, 1.5),
        "critical_low": None,
        "critical_high": 4.0,
        "low": "EC is low — interpret cautiously; may indicate low mineral content.",
        "high": "EC is elevated — salinity risk; sensitive crops may show stress.",
    },
    "moisture": {
        "label": "Soil Moisture",
        "unit": "%",
        "good": (20, 60),
        "critical_low": 5,
        "critical_high": None,
        "low": "Moisture is low at time of sampling — irrigation or rainfall may be needed.",
        "high": "Moisture is high at time of sampling — waterlogging risk; ensure drainage.",
    },
    "temperature": {
        "label": "Soil Temperature",
        "unit": "°C",
        "good": (15, 35),
        "critical_low": 5,
        "critical_high": 45,
        "low": "Soil temperature is low — microbial activity and germination may be slow.",
        "high": "Soil temperature is high — beneficial microbes may be suppressed.",
    },
    "organic_carbon": {
        "label": "Organic Carbon",
        "unit": "%",
        "good": (0.5, 2.0),
        "critical_low": 0.2,
        "critical_high": None,
        "low": "Organic carbon is low — soil structure, water retention and microbial diversity are limited.",
        "high": "Organic carbon is high — generally beneficial; confirm with lab for peat/wetland soils.",
    },
}

REQUIRED = list(PARAM_RULES.keys())


def _status(value: float, rule: dict) -> str:
    lo, hi = rule["good"]
    clo = rule.get("critical_low")
    chi = rule.get("critical_high")
    if clo is not None and value < clo:
        return "Critical"
    if chi is not None and value > chi:
        return "Critical"
    if lo <= value <= hi:
        return "Optimal"
    if value < lo:
        return "Low"
    return "High"


def analyze_parameters(params: dict) -> dict:
    results: list[dict] = []
    missing: list[str] = []

    for key, rule in PARAM_RULES.items():
        raw = params.get(key)
        if raw is None:
            missing.append(key)
            results.append({
                "key": key,
                "label": rule["label"],
                "value": None,
                "unit": rule["unit"],
                "status": "Missing",
                "message": "Value not provided — enter this parameter for a complete analysis.",
            })
            continue

        value = float(raw)
        status = _status(value, rule)

        if status == "Optimal":
            message = "Within the optimal range used by this analyzer."
        elif status == "Low":
            message = rule["low"]
        elif status == "High":
            message = rule["high"]
        else:  # Critical
            lo, hi = rule["good"]
            if value < lo:
                message = f"CRITICAL — {rule['low']}"
            else:
                message = f"CRITICAL — {rule['high']}"

        results.append({
            "key": key,
            "label": rule["label"],
            "value": value,
            "unit": rule["unit"],
            "status": status,
            "message": message,
        })

    present = [r for r in results if r["status"] != "Missing"]
    n_total = len(REQUIRED)
    n_present = len(present)
    n_optimal = sum(1 for r in present if r["status"] == "Optimal")

    completeness = round(n_present / n_total * 100, 1)
    screening_score = round(n_optimal / n_total * 100, 1) if n_total else 0

    # Build observation lists
    deficiencies = [r["label"] for r in present if r["status"] in ("Low", "Critical") and float(r["value"]) < PARAM_RULES[r["key"]]["good"][0]]
    excesses = [r["label"] for r in present if r["status"] in ("High", "Critical") and float(r["value"]) > PARAM_RULES[r["key"]]["good"][1]]
    warnings = [r["label"] for r in present if r["status"] == "Critical"]

    return {
        "completeness": completeness,
        "missing_parameters": missing,
        "parameter_analysis": results,
        "screening_score": screening_score,
        "deficiencies": deficiencies,
        "excesses": excesses,
        "warnings": warnings,
    }


def analyze_soil(params: dict) -> dict:
    analysis = analyze_parameters(params)
    crops = crop_recommendations(params)
    fertilizers = fertilizer_recommendations(params)
    return {**analysis, "crop_recommendations": crops, "fertilizer_recommendations": fertilizers}
