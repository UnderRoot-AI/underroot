from __future__ import annotations
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from app.core.config import settings

# Crop metadata: (season, days_to_harvest, farmer_friendly_reason)
CROP_META = {
    "Wheat": (
        "Rabi (Oct–Nov sowing)",
        120,
        "Gehun (wheat) grows well in your soil. Sow in October–November. "
        "Water 5–6 times during the season. Ready to cut in about 4 months. "
        "Use Urea and DAP fertilizer at sowing time for good yield.",
    ),
    "Maize": (
        "Kharif (Jun–Jul sowing)",
        110,
        "Makka (maize) is a good choice for your soil. Sow after first rain in June–July. "
        "Water regularly — do not let soil dry out. Harvest in about 3.5 months. "
        "Apply Urea in two parts: half at sowing, half when plant is knee-high.",
    ),
    "Rice": (
        "Kharif (Jun–Jul sowing)",
        120,
        "Chawal (rice/paddy) suits your soil. Needs good water supply — keep field flooded in early weeks. "
        "Transplant seedlings after 25–30 days in nursery. Ready in about 4 months. "
        "Use DAP at transplanting and Urea 20 days after transplanting.",
    ),
    "Groundnut": (
        "Kharif (Jun–Jul sowing)",
        110,
        "Moongfali (groundnut) grows well here. Sow seeds 5 cm deep after first rain. "
        "Does not need much water — 1 watering every 10 days is enough. "
        "Do not use too much nitrogen; add gypsum (100 kg/acre) at flowering for good pods.",
    ),
    "Cotton": (
        "Kharif (Apr–May sowing)",
        160,
        "Kapas (cotton) can grow in your soil. Sow in April–May. "
        "Needs regular watering every 10–15 days. Picking starts after about 5 months. "
        "Apply NPK 120:60:60 kg/ha. Watch for bollworm pest — spray if needed.",
    ),
    "Potato": (
        "Rabi (Oct–Nov sowing)",
        100,
        "Aalu (potato) does well in slightly acidic soil like yours. "
        "Plant seed potatoes 20–25 cm apart in rows. Water every 7–10 days. "
        "Ready to dig in about 3 months. Apply DAP and Potash (MOP) at planting.",
    ),
    "Barley": (
        "Rabi (Oct–Nov sowing)",
        120,
        "Jau (barley) handles your soil conditions well. Sow in October–November. "
        "Needs less water than wheat — water only 2–3 times. "
        "Low-cost crop; apply 60 kg Urea per acre at sowing.",
    ),
    "Chickpea": (
        "Rabi (Oct–Nov sowing)",
        110,
        "Chana (chickpea) is a good pulse for your soil. Sow in October–November. "
        "Needs very little water — rain is usually enough. "
        "Being a legume, it adds nitrogen back to your soil for the next crop. "
        "Use Rhizobium seed treatment before sowing for best results.",
    ),
    "Pigeonpea": (
        "Kharif (Jun–Jul sowing)",
        150,
        "Arhar/Tur (pigeonpea) has deep roots and suits your soil well. "
        "Sow at start of monsoon. Drought-tolerant — survives dry spells. "
        "Fixes nitrogen in soil — good to grow before a cereal crop. "
        "Apply only 20 kg Urea per acre; too much nitrogen reduces pod count.",
    ),
    "Mustard": (
        "Rabi (Oct–Nov sowing)",
        110,
        "Sarson (mustard) is a good oilseed crop for your soil. Sow in October. "
        "Needs 2–3 waterings only. Ready in about 3.5 months. "
        "Apply 40 kg Urea and 20 kg DAP per acre. Harvest when pods turn golden-yellow.",
    ),
}

# Fertilizer metadata: (type, farmer_friendly_reason)
FERT_META = {
    "Balanced NPK": (
        "inorganic",
        "Your soil needs all three nutrients — Nitrogen (N), Phosphorus (P), and Potassium (K). "
        "Buy NPK 10:26:26 or NPK 12:32:16 bag from your nearest input shop. "
        "Apply 1 bag (50 kg) per acre at sowing time, mixed into the soil before planting. "
        "Also add 1 bag of Urea (45 kg) in two splits: half at sowing, half 30 days later.",
    ),
    "Nitrogen source": (
        "inorganic",
        "Your soil is low in Nitrogen — plants will look pale yellow without it. "
        "Buy Urea (46% N) from the cooperative or input shop — costs about ₹250–300 per bag. "
        "Apply 1 bag (45 kg) per acre: half at sowing, half when crop is 30 days old. "
        "Do not apply all at once or rain will wash it away.",
    ),
    "Phosphorus source": (
        "inorganic",
        "Your soil is low in Phosphorus — roots will be weak without it. "
        "Buy DAP (Di-Ammonium Phosphate, 18:46:0) — costs about ₹1,300 per bag. "
        "Apply half a bag (25 kg) per acre at sowing time, mixed into the soil. "
        "DAP also provides some Nitrogen, so reduce Urea dose slightly.",
    ),
    "Potassium source": (
        "inorganic",
        "Your soil is low in Potassium — crops will be weak and prone to disease. "
        "Buy MOP (Muriate of Potash, 60% K2O) — costs about ₹800 per bag. "
        "Apply 25–30 kg per acre at sowing time. "
        "Potassium also helps the crop resist drought and pests.",
    ),
    "Nitrogen + Phosphorus": (
        "inorganic",
        "Your soil is low in both Nitrogen and Phosphorus. "
        "Buy 1 bag of DAP (18:46:0) per acre — apply at sowing time mixed into soil. "
        "DAP gives both N and P together. Then add half a bag of Urea 30 days after sowing. "
        "This combination is used by most farmers for cereals and pulses.",
    ),
    "Nitrogen + Potassium": (
        "inorganic",
        "Your soil needs more Nitrogen and Potassium. "
        "Apply 1 bag of Urea (45 kg/acre) in two splits, and 25 kg of MOP at sowing. "
        "MOP improves fruit and grain quality. Urea makes the plant green and strong. "
        "Do not mix Urea and MOP together before applying — add them separately.",
    ),
    "Phosphorus + Potassium": (
        "inorganic",
        "Your soil is low in Phosphorus and Potassium. "
        "Apply half a bag of DAP (25 kg/acre) and 25 kg of MOP at sowing time. "
        "Mix both into the soil before planting. "
        "Your Nitrogen seems okay — you may not need extra Urea if soil organic matter is good.",
    ),
    "Organic compost": (
        "organic",
        "Your soil will benefit most from organic matter (gobar khad / compost). "
        "Apply 2–3 trolley-loads (about 4–5 tonnes) of well-rotted farmyard manure per acre. "
        "Spread evenly and plough into the field 2–3 weeks before sowing. "
        "Compost improves soil structure, holds water better, and slowly releases all nutrients. "
        "You can also add Neem Khali (neem cake) — 50 kg per acre — alongside manure.",
    ),
}

def _model_path(name: str) -> Path:
    p=Path(settings.model_dir)
    if not p.is_absolute(): p=Path(__file__).resolve().parents[2]/p
    return p/name

def _load(name: str):
    try: return joblib.load(_model_path(name))
    except Exception: return None

def _prepare(params: dict, features: list[str], defaults: dict | None = None):
    missing=[f for f in features if params.get(f) is None]
    defaults=defaults or {}
    row={f: float(params[f]) if params.get(f) is not None else float(defaults.get(f,0)) for f in features}
    return pd.DataFrame([row]), missing

def predict_crops(params: dict, top_k: int=5) -> list[dict]:
    bundle=_load("crop_model.joblib")
    if not bundle: return []
    model=bundle["model"]; features=bundle["features"]
    row,missing=_prepare(params,features,bundle.get("defaults"))
    probs=model.predict_proba(row)[0]; classes=model.classes_; ranked=np.argsort(probs)[::-1][:top_k]
    out=[]
    for i in ranked:
        crop=str(classes[i]); season,days,reason=CROP_META.get(crop,("—",None,"Matched against the trained soil profile model."))
        out.append({"crop":crop,"suitability":round(float(probs[i])*100,1),"reason":reason,"season":season,"expected_duration_days":days,"model":"RandomForest soil-profile model","missing_inputs":missing})
    return out

def predict_fertilizer(params: dict) -> list[dict]:
    bundle=_load("fertilizer_model.joblib")
    if not bundle: return []
    model=bundle["model"]; features=bundle["features"]
    row,missing=_prepare(params,features,bundle.get("defaults"))
    label=str(model.predict(row)[0]); confidence=float(max(model.predict_proba(row)[0])) if hasattr(model,"predict_proba") else 0.0
    typ,reason=FERT_META.get(label,("inorganic","Apply well-rotted farmyard manure (gobar khad) — 4 to 5 tonnes per acre — before sowing."))
    lows=[]
    low_names={"nitrogen":"Nitrogen (Nai-tro-gen)","phosphorus":"Phosphorus (Fos-fo-rus)","potassium":"Potassium (Pota-shi-um)"}
    for key,threshold in (("nitrogen",40),("phosphorus",25),("potassium",40)):
        if params.get(key) is not None and float(params[key])<threshold: lows.append(low_names[key])
    if lows: reason += " Your soil test shows low levels of: " + ", ".join(lows) + ". Pay extra attention to these."
    return [{"name":label,"type":typ,"quantity":"See dose details in the description below","frequency":"Apply at sowing; repeat as described","reason":reason,"confidence":round(confidence*100,1),"missing_inputs":missing,"precautions":["Always water the field after applying fertilizer.","Do not apply more than the recommended dose — it wastes money and harms soil.","Store fertilizer bags in a dry, shaded place."]}]
