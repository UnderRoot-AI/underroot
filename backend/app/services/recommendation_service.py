"""
Rule-based recommendation engine.

Crop and fertilizer recommendations are driven by actual soil parameter values.
The ML model (ml_service.py) is used when available; rule-based logic is the
reliable fallback so the system always returns useful recommendations.

Units: N/P/K in kg/ha.
"""
from __future__ import annotations
from app.services.ml_service import predict_crops, predict_fertilizer


def _f(params: dict, key: str) -> float | None:
    v = params.get(key)
    return float(v) if v is not None else None


def crop_recommendations(p: dict) -> list[dict]:
    """Return crop recommendations driven by actual soil parameters."""
    # Try ML model first
    model_result = predict_crops(p)
    if model_result:
        return model_result

    # Rule-based fallback — uses actual parameter values
    ph = _f(p, "ph")
    n = _f(p, "nitrogen")
    moisture = _f(p, "moisture")
    k = _f(p, "potassium")

    results: list[dict] = []

    # ── pH-based primary crop selection ──────────────────────────────────────
    if ph is not None and ph < 5.5:
        results.append({
            "crop": "Potato",
            "suitability": 84,
            "season": "Rabi (Oct–Nov sowing)",
            "expected_duration_days": 100,
            "reason": (
                f"Your soil pH of {ph:.1f} is acidic. Aalu (potato) does well in acidic conditions. "
                "Plant seed potatoes 20–25 cm apart. Water every 7–10 days. "
                "Ready to dig in about 3 months. Apply DAP and MOP at planting."
            ),
        })
        results.append({
            "crop": "Groundnut",
            "suitability": 76,
            "season": "Kharif (Jun–Jul sowing)",
            "expected_duration_days": 110,
            "reason": (
                f"Groundnut (moongfali) tolerates mildly acidic soil (your pH: {ph:.1f}). "
                "Sow 5 cm deep after first monsoon rain. Very low water requirement. "
                "Do not over-apply nitrogen; add gypsum at flowering for good pod fill."
            ),
        })
    elif ph is not None and ph > 8.0:
        results.append({
            "crop": "Barley",
            "suitability": 82,
            "season": "Rabi (Oct–Nov sowing)",
            "expected_duration_days": 120,
            "reason": (
                f"Your soil pH of {ph:.1f} is alkaline. Jau (barley) handles alkaline conditions well. "
                "Sow in October–November. Needs only 2–3 waterings. "
                "Apply 60 kg Urea per acre at sowing."
            ),
        })
        results.append({
            "crop": "Mustard",
            "suitability": 78,
            "season": "Rabi (Oct–Nov sowing)",
            "expected_duration_days": 110,
            "reason": (
                f"Sarson (mustard) grows well in your slightly alkaline soil (pH {ph:.1f}). "
                "Sow in October. Needs only 2–3 waterings. Harvest when pods turn golden-yellow."
            ),
        })
    else:
        # Near-neutral pH — select based on nutrient availability
        if n is not None and n >= 150:
            results.append({
                "crop": "Wheat",
                "suitability": 85,
                "season": "Rabi (Oct–Nov sowing)",
                "expected_duration_days": 120,
                "reason": (
                    f"Your soil nitrogen is {n:.0f} kg/ha"
                    + (f" and pH is {ph:.1f}" if ph else "")
                    + ". Gehun (wheat) is an excellent choice. "
                    "Sow in October–November. Water 5–6 times. "
                    "Apply DAP at sowing and split Urea applications. "
                    "Ready to harvest in about 4 months."
                ),
            })
            results.append({
                "crop": "Maize",
                "suitability": 78,
                "season": "Kharif (Jun–Jul sowing)",
                "expected_duration_days": 110,
                "reason": (
                    f"Makka (maize) suits your soil nutrient profile (N: {n:.0f} kg/ha). "
                    "Sow after first monsoon rain. Keep soil moist. "
                    "Apply Urea in two splits: half at sowing, half when knee-high."
                ),
            })
        elif moisture is not None and moisture >= 30:
            results.append({
                "crop": "Rice",
                "suitability": 80,
                "season": "Kharif (Jun–Jul sowing)",
                "expected_duration_days": 120,
                "reason": (
                    f"Your soil moisture is {moisture:.1f}% and conditions suit chawal (rice). "
                    "Transplant seedlings after nursery. Keep field flooded in early weeks. "
                    "Use DAP at transplanting and Urea 20 days after."
                ),
            })
            results.append({
                "crop": "Pigeonpea",
                "suitability": 72,
                "season": "Kharif (Jun–Jul sowing)",
                "expected_duration_days": 150,
                "reason": (
                    "Arhar/Tur (pigeonpea) has deep roots and handles variable moisture well. "
                    "Sow at monsoon start. Drought-tolerant once established. "
                    "Fixes nitrogen — good to grow before a cereal crop."
                ),
            })
        else:
            # Generic balanced fallback
            results.append({
                "crop": "Chickpea",
                "suitability": 76,
                "season": "Rabi (Oct–Nov sowing)",
                "expected_duration_days": 110,
                "reason": (
                    "Chana (chickpea) is a reliable pulse for near-neutral soil. "
                    "Sow in October–November. Needs very little water — rain is usually enough. "
                    "Being a legume, it adds nitrogen to your soil for the next crop."
                ),
            })
            results.append({
                "crop": "Wheat",
                "suitability": 72,
                "season": "Rabi (Oct–Nov sowing)",
                "expected_duration_days": 120,
                "reason": (
                    "Gehun (wheat) is suitable for your soil conditions. "
                    "Sow in October–November. Water 5–6 times. Apply DAP and Urea at sowing."
                ),
            })

    return results[:3]


def fertilizer_recommendations(p: dict) -> list[dict]:
    """Return fertilizer recommendations based on actual nutrient deficiencies."""
    # Try ML model first
    model_result = predict_fertilizer(p)
    if model_result:
        return model_result

    # Rule-based fallback using actual N, P, K values (kg/ha thresholds)
    n = _f(p, "nitrogen")
    phos = _f(p, "phosphorus")
    k = _f(p, "potassium")
    oc = _f(p, "organic_carbon")
    ec = _f(p, "ec")

    n_low = n is not None and n < 150
    p_low = phos is not None and phos < 15
    k_low = k is not None and k < 200
    n_ok = n is None or n >= 150
    p_ok = phos is None or phos >= 15
    k_ok = k is None or k >= 200
    oc_low = oc is not None and oc < 0.5

    results: list[dict] = []

    # Organic matter first if low
    if oc_low:
        results.append({
            "name": "Farmyard Manure (Gobar Khad)",
            "type": "organic",
            "quantity": "4–5 tonnes (2–3 trolley-loads) per acre",
            "frequency": "Apply 2–3 weeks before sowing, plough into soil",
            "reason": (
                f"Your organic carbon is {oc:.2f}% which is below the optimal 0.5%. "
                "Spread 2–3 trolley-loads of well-rotted farmyard manure evenly and plough in. "
                "This improves soil structure, holds moisture, and slowly feeds your crop. "
                "Add 50 kg Neem Khali (neem cake) per acre alongside to protect roots from pests."
            ),
            "precautions": [
                "Use only well-rotted / fully decomposed manure — fresh dung burns roots.",
                "Apply 2–3 weeks before sowing so it mixes well into the soil.",
                "Store manure under shade to prevent nutrient loss.",
            ],
        })

    # NPK deficiency combinations
    if n_low and p_low:
        results.append({
            "name": "DAP (Di-Ammonium Phosphate)",
            "type": "inorganic",
            "quantity": "1 bag (50 kg) per acre",
            "frequency": "Apply at sowing time, mix into soil",
            "reason": (
                f"Soil nitrogen ({n:.0f} kg/ha) and phosphorus ({phos:.1f} kg/ha) are both below optimal. "
                "DAP (18:46:0) provides both N and P together — 1 bag per acre at sowing. "
                "Also add half a bag of Urea 30 days after sowing."
            ),
            "precautions": [
                "Mix DAP into soil before planting — do not leave on surface.",
                "Do not mix with Urea before applying.",
                "Water the field after application.",
            ],
        })
    elif n_low:
        results.append({
            "name": "Urea (46% N)",
            "type": "inorganic",
            "quantity": "1 bag (45 kg) per acre",
            "frequency": "Split: half at sowing, half 30 days later",
            "reason": (
                f"Soil nitrogen is {n:.0f} kg/ha — below the optimal 150 kg/ha. "
                "Urea (46% N) is the most economical source. Apply in two splits to prevent losses. "
                "Do not apply all at once or rain will wash it away."
            ),
            "precautions": [
                "Never apply Urea when soil is wet or just before heavy rain.",
                "Apply in the evening to reduce volatilisation loss.",
                "Do not store opened bags near moisture.",
            ],
        })
    elif p_low:
        results.append({
            "name": "Single Super Phosphate (SSP)",
            "type": "inorganic",
            "quantity": "25 kg per acre",
            "frequency": "Apply at sowing time, mix into soil",
            "reason": (
                f"Phosphorus is {phos:.1f} kg/ha — below the optimal 15 kg/ha. "
                "SSP is a cost-effective phosphorus source. Mix into soil before planting. "
                "Also provides sulphur which helps in protein synthesis."
            ),
            "precautions": [
                "Do not apply in waterlogged conditions.",
                "Mix well into the root zone — broadcast and plough in.",
            ],
        })

    if k_low:
        results.append({
            "name": "MOP (Muriate of Potash, 60% K₂O)",
            "type": "inorganic",
            "quantity": "25–30 kg per acre",
            "frequency": "Apply at sowing time",
            "reason": (
                f"Potassium is {k:.0f} kg/ha — below the optimal 200 kg/ha. "
                "MOP improves drought and disease resistance. Apply at sowing, mixed into soil. "
                "Potassium also improves grain and fruit quality."
            ),
            "precautions": [
                "Do not mix with Urea before applying.",
                "Avoid applying on wet soil surface.",
            ],
        })

    # Salinity warning
    if ec is not None and ec > 2.0:
        results.append({
            "name": "Gypsum (Calcium Sulphate)",
            "type": "inorganic",
            "quantity": "200–400 kg per acre",
            "frequency": "Apply once before sowing",
            "reason": (
                f"Your EC is {ec:.2f} dS/m, which indicates elevated salinity. "
                "Gypsum helps reclaim saline soils by replacing sodium with calcium. "
                "Apply before sowing and irrigate to leach salts below the root zone."
            ),
            "precautions": [
                "Ensure good drainage before applying gypsum.",
                "Follow up with a leaching irrigation after application.",
            ],
        })

    # If all NPK are adequate, recommend balanced maintenance
    if n_ok and p_ok and k_ok and not oc_low and ec is None or (ec is not None and ec <= 2.0):
        if not results:
            results.append({
                "name": "Balanced NPK Maintenance",
                "type": "inorganic",
                "quantity": "NPK 12:32:16 — 1 bag (50 kg) per acre",
                "frequency": "Apply at sowing",
                "reason": (
                    "Your major soil nutrients appear to be in a reasonable range. "
                    "A balanced NPK fertilizer (12:32:16 or similar) at sowing will maintain productivity. "
                    "Supplement with organic matter annually to sustain soil health long-term."
                ),
                "precautions": [
                    "Always follow with irrigation.",
                    "Do not exceed recommended dose — excess fertilizer harms soil biology.",
                ],
            })

    # Ensure at least one recommendation is always returned
    if not results:
        results.append({
            "name": "Farmyard Manure (Gobar Khad)",
            "type": "organic",
            "quantity": "4–5 tonnes (2–3 trolley-loads) per acre",
            "frequency": "Apply 2–3 weeks before sowing, plough into soil",
            "reason": (
                "Well-rotted farmyard manure is the safest general soil amendment. "
                "It improves structure, water retention, and slowly provides all nutrients. "
                "Recommended as a base treatment regardless of soil status."
            ),
            "precautions": [
                "Use only well-rotted / fully decomposed manure.",
                "Apply 2–3 weeks before sowing.",
            ],
        })

    return results[:3]
