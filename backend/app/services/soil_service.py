"""
Soil health score calculator.

Score is computed deterministically from the same thresholds used in soil_analyzer.py.
Units: N/P/K in kg/ha (consistent across the system).

Scoring logic:
- Each of 8 parameters contributes up to 12.5 points (8 × 12.5 = 100 max).
- Optimal → full 12.5 points.
- Low or High → partial credit based on how far from optimal boundary.
- Critical → 0 points for that parameter.
- Missing → parameter is excluded from denominator so partial tests are not penalised.

Status thresholds:
- Excellent  : 80–100
- Good       : 60–79
- Needs Attention : 30–59
- Poor       : 1–29
- Awaiting Data : 0 (no parameters at all)
"""
from __future__ import annotations

# Mirror of thresholds in soil_analyzer.PARAM_RULES — keep in sync.
_PARAMS: dict[str, dict] = {
    "ph":             {"good": (6.0, 7.5), "clo": 4.5,  "chi": 9.0},
    "nitrogen":       {"good": (150, 280),  "clo": 50.0, "chi": 600.0},   # kg/ha
    "phosphorus":     {"good": (15, 45),    "clo": 5.0,  "chi": 150.0},   # kg/ha
    "potassium":      {"good": (200, 400),  "clo": 80.0, "chi": 800.0},   # kg/ha
    "ec":             {"good": (0.2, 1.5),  "clo": None, "chi": 4.0},
    "moisture":       {"good": (20, 60),    "clo": 5.0,  "chi": None},
    "temperature":    {"good": (15, 35),    "clo": 5.0,  "chi": 45.0},
    "organic_carbon": {"good": (0.5, 2.0),  "clo": 0.2,  "chi": None},
}

_POINTS_EACH = 12.5  # 8 × 12.5 = 100


def _param_score(value: float, rule: dict) -> float:
    lo, hi = rule["good"]
    clo, chi = rule["clo"], rule["chi"]

    # Critical → 0
    if clo is not None and value < clo:
        return 0.0
    if chi is not None and value > chi:
        return 0.0

    # Optimal → full
    if lo <= value <= hi:
        return _POINTS_EACH

    # Low — partial: linear decay from optimal boundary to critical (or 0)
    if value < lo:
        floor = clo if clo is not None else 0.0
        span = lo - floor
        if span <= 0:
            return 0.0
        return round(_POINTS_EACH * max(0.0, (value - floor) / span), 2)

    # High — partial: linear decay from optimal boundary to critical (or 2× hi)
    else:
        ceil = chi if chi is not None else hi * 2
        span = ceil - hi
        if span <= 0:
            return 0.0
        return round(_POINTS_EACH * max(0.0, (ceil - value) / span), 2)


def calculate_health(params: dict) -> tuple[float, str]:
    present = [(k, v) for k, v in params.items() if k in _PARAMS and v is not None]
    if not present:
        return 0.0, "Awaiting Data"

    total_points = sum(_param_score(float(v), _PARAMS[k]) for k, v in present)
    # Scale to 0–100 based on parameters that were actually provided
    max_points = len(present) * _POINTS_EACH
    score = round(total_points / max_points * 100, 1) if max_points else 0.0
    score = max(0.0, min(100.0, score))

    if score >= 80:
        status = "Excellent"
    elif score >= 60:
        status = "Good"
    elif score > 0:
        status = "Needs Attention"
    else:
        status = "Poor"

    return score, status
