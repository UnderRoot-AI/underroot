from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "datasets"
MODELS = ROOT / "ml_models"
DATA.mkdir(parents=True, exist_ok=True)
MODELS.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(42)

# Prototype ranges are a compact development/training dataset for the application.
# They are intentionally not presented as field-specific agronomic truth.
crop_profiles = {
    "Wheat": (70, 35, 45, 6.8, 1.0, 45, 20, 0.8),
    "Maize": (90, 45, 50, 6.5, 1.0, 55, 24, 0.7),
    "Rice": (85, 35, 35, 6.2, 1.0, 70, 27, 0.8),
    "Groundnut": (45, 30, 45, 6.3, 0.8, 45, 25, 0.7),
    "Cotton": (55, 30, 55, 7.0, 1.1, 40, 27, 0.7),
    "Potato": (60, 40, 50, 5.8, 0.9, 55, 18, 0.9),
    "Barley": (55, 30, 35, 7.4, 1.0, 40, 18, 0.8),
    "Chickpea": (35, 45, 35, 6.8, 0.8, 35, 20, 0.7),
    "Pigeonpea": (40, 30, 40, 6.8, 0.8, 35, 25, 0.7),
    "Mustard": (45, 30, 35, 7.0, 0.9, 40, 20, 0.7),
}
features = ["nitrogen", "phosphorus", "potassium", "ph", "ec", "moisture", "temperature", "organic_carbon"]
rows = []
for crop, center in crop_profiles.items():
    for _ in range(300):
        n,p,k,ph,ec,moist,temp,oc = center
        rows.append({
            "nitrogen": max(5, rng.normal(n, 10)),
            "phosphorus": max(5, rng.normal(p, 7)),
            "potassium": max(5, rng.normal(k, 9)),
            "ph": np.clip(rng.normal(ph, .28), 4.5, 9.5),
            "ec": max(.1, rng.normal(ec, .20)),
            "moisture": np.clip(rng.normal(moist, 8), 5, 90),
            "temperature": rng.normal(temp, 2.5),
            "organic_carbon": max(.1, rng.normal(oc, .15)),
            "crop": crop,
        })
crop_df = pd.DataFrame(rows)
crop_csv = DATA / "crop_recommendation_training.csv"
crop_df.to_csv(crop_csv, index=False)
X = crop_df[features]; y = crop_df["crop"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=.2, random_state=42, stratify=y)
crop_model = RandomForestClassifier(n_estimators=120, random_state=42, class_weight="balanced_subsample", min_samples_leaf=2)
crop_model.fit(X_train, y_train)
accuracy = accuracy_score(y_test, crop_model.predict(X_test))
joblib.dump({"model": crop_model, "features": features, "defaults": {k: float(crop_df[k].median()) for k in features}, "accuracy": float(accuracy)}, MODELS / "crop_model.joblib")

fertilizer_classes = [
    "Balanced NPK", "Nitrogen source", "Phosphorus source", "Potassium source",
    "Nitrogen + Phosphorus", "Nitrogen + Potassium", "Phosphorus + Potassium", "Organic compost"
]
fert_rows = []
for _ in range(6000):
    n,p,k = rng.uniform(10,120), rng.uniform(5,80), rng.uniform(10,120)
    ph = rng.uniform(5,8.5); moisture = rng.uniform(10,80); oc = rng.uniform(.2,1.5)
    lows = [n < 40, p < 25, k < 40]
    if sum(lows) == 0:
        label = "Balanced NPK" if oc >= .5 else "Organic compost"
    elif lows == [True, False, False]: label = "Nitrogen source"
    elif lows == [False, True, False]: label = "Phosphorus source"
    elif lows == [False, False, True]: label = "Potassium source"
    elif lows == [True, True, False]: label = "Nitrogen + Phosphorus"
    elif lows == [True, False, True]: label = "Nitrogen + Potassium"
    else: label = "Phosphorus + Potassium"
    fert_rows.append({"nitrogen":n,"phosphorus":p,"potassium":k,"ph":ph,"moisture":moisture,"organic_carbon":oc,"fertilizer":label})
fert_df = pd.DataFrame(fert_rows)
fert_csv = DATA / "fertilizer_recommendation_training.csv"
fert_df.to_csv(fert_csv, index=False)
fert_features = ["nitrogen","phosphorus","potassium","ph","moisture","organic_carbon"]
FX_train, FX_test, Fy_train, Fy_test = train_test_split(fert_df[fert_features], fert_df["fertilizer"], test_size=.2, random_state=42, stratify=fert_df["fertilizer"])
fert_model = RandomForestClassifier(n_estimators=120, random_state=42, class_weight="balanced", min_samples_leaf=2)
fert_model.fit(FX_train, Fy_train)
fert_accuracy = accuracy_score(Fy_test, fert_model.predict(FX_test))
joblib.dump({"model": fert_model, "features": fert_features, "defaults": {k: float(fert_df[k].median()) for k in fert_features}, "accuracy": float(fert_accuracy)}, MODELS / "fertilizer_model.joblib")

(MODELS / "training_metrics.json").write_text(json.dumps({"crop_accuracy": float(accuracy), "fertilizer_accuracy": float(fert_accuracy)}, indent=2))
print(json.dumps({"crop_accuracy": accuracy, "fertilizer_accuracy": fert_accuracy, "crop_rows": len(crop_df), "fertilizer_rows": len(fert_df)}, indent=2))
