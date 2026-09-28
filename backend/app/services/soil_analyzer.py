from __future__ import annotations
from app.services.recommendation_service import crop_recommendations, fertilizer_recommendations

PARAM_RULES = {
    "ph": {"label":"pH","unit":"","good":(6.0,7.5),"low":"Soil is acidic.","high":"Soil is alkaline."},
    "nitrogen": {"label":"Nitrogen","unit":"mg/kg","good":(40,100),"low":"Nitrogen is relatively low.","high":"Nitrogen is relatively high."},
    "phosphorus": {"label":"Phosphorus","unit":"mg/kg","good":(25,70),"low":"Phosphorus is relatively low.","high":"Phosphorus is relatively high."},
    "potassium": {"label":"Potassium","unit":"mg/kg","good":(40,100),"low":"Potassium is relatively low.","high":"Potassium is relatively high."},
    "ec": {"label":"Electrical Conductivity","unit":"dS/m","good":(0.2,1.5),"low":"EC is low; interpret with soil texture and test method.","high":"EC is elevated and may indicate salinity risk."},
    "moisture": {"label":"Moisture","unit":"%","good":(20,60),"low":"Moisture is low at measurement time.","high":"Moisture is high at measurement time."},
    "temperature": {"label":"Temperature","unit":"°C","good":(15,35),"low":"Soil temperature is relatively low.","high":"Soil temperature is relatively high."},
    "organic_carbon": {"label":"Organic Carbon","unit":"%","good":(0.5,1.5),"low":"Organic carbon is relatively low.","high":"Organic carbon is relatively high."},
}
REQUIRED = list(PARAM_RULES)

def analyze_parameters(params: dict) -> dict:
    results=[]; missing=[]
    for key, rule in PARAM_RULES.items():
        value=params.get(key)
        if value is None:
            missing.append(key)
            results.append({"key":key,"label":rule["label"],"value":None,"unit":rule["unit"],"status":"Missing","message":"Value is required for complete analysis."})
            continue
        lo,hi=rule["good"]
        if lo <= float(value) <= hi:
            status="Good"; message="Within the screening range used by this analyzer."
        elif float(value) < lo:
            status="Low"; message=rule["low"]
        else:
            status="High"; message=rule["high"]
        results.append({"key":key,"label":rule["label"],"value":float(value),"unit":rule["unit"],"status":status,"message":message})
    score = round(sum(1 for x in results if x["status"]=="Good") / len(REQUIRED) * 100, 1)
    return {"completeness":round((len(REQUIRED)-len(missing))/len(REQUIRED)*100,1),"missing_parameters":missing,"parameter_analysis":results,"screening_score":score}

def analyze_soil(params: dict) -> dict:
    analysis=analyze_parameters(params)
    crops=crop_recommendations(params)
    fertilizers=fertilizer_recommendations(params)
    return {**analysis,"crop_recommendations":crops,"fertilizer_recommendations":fertilizers}
