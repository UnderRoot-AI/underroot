from app.services.ml_service import predict_crops, predict_fertilizer

def crop_recommendations(p: dict):
    model = predict_crops(p)
    if model:
        return model
    # Fallback: rule-based on pH
    ph = p.get("ph")
    if ph is not None and float(ph) < 6.0:
        return [{
            "crop": "Potato",
            "suitability": 82,
            "season": "Rabi (Oct–Nov sowing)",
            "expected_duration_days": 100,
            "reason": (
                "Aalu (potato) does well in acidic soil like yours (pH below 6). "
                "Plant seed potatoes 20–25 cm apart. Water every 7–10 days. "
                "Ready to dig in about 3 months. Apply DAP and MOP (Potash) at planting."
            ),
        }]
    if ph is not None and float(ph) > 7.8:
        return [{
            "crop": "Barley",
            "suitability": 80,
            "season": "Rabi (Oct–Nov sowing)",
            "expected_duration_days": 120,
            "reason": (
                "Jau (barley) grows well in alkaline soil like yours (pH above 7.8). "
                "Sow in October–November. Needs only 2–3 waterings — less work than wheat. "
                "Apply 60 kg Urea per acre at sowing time."
            ),
        }]
    return [{
        "crop": "Wheat",
        "suitability": 78,
        "season": "Rabi (Oct–Nov sowing)",
        "expected_duration_days": 120,
        "reason": (
            "Gehun (wheat) is a reliable choice for your soil. "
            "Sow in October–November. Water 5–6 times during the season. "
            "Apply 1 bag DAP at sowing and 1 bag Urea in two splits. "
            "Ready to harvest in about 4 months."
        ),
    }]

def fertilizer_recommendations(p: dict):
    model = predict_fertilizer(p)
    if model:
        return model
    # Fallback: organic advice with real actionable details
    return [{
        "name": "Farmyard Manure (Gobar Khad)",
        "type": "organic",
        "quantity": "4–5 tonnes (2–3 trolley-loads) per acre",
        "frequency": "Apply 2–3 weeks before sowing, plough into soil",
        "reason": (
            "Your soil will benefit from well-rotted farmyard manure (gobar khad). "
            "Spread 2–3 trolley-loads evenly across your field, then plough it in. "
            "This improves soil structure, holds moisture, and slowly feeds your crop all season. "
            "You can also add 50 kg of Neem Khali (neem cake) per acre alongside the manure "
            "to protect roots from soil pests."
        ),
        "precautions": [
            "Use only well-rotted / fully decomposed manure — fresh dung burns crop roots.",
            "Apply 2–3 weeks before sowing so it mixes well into the soil.",
            "Store manure under shade to prevent nutrient loss from sun and rain.",
        ],
    }]
