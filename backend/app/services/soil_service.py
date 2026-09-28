def calculate_health(params: dict) -> tuple[float, str]:
    score = 65.0
    checks = 0
    ph = params.get("ph")
    moisture = params.get("moisture")
    organic = params.get("organic_carbon")
    n,p,k = params.get("nitrogen"),params.get("phosphorus"),params.get("potassium")
    if ph is not None:
        checks += 1; score += 10 if 6.0 <= ph <= 7.5 else (3 if 5.5 <= ph <= 8.0 else -8)
    if moisture is not None:
        checks += 1; score += 7 if 20 <= moisture <= 60 else -4
    if organic is not None:
        checks += 1; score += 7 if organic >= 0.5 else -5
    for value, low, high in ((n,40,100),(p,25,70),(k,40,100)):
        if value is not None:
            checks += 1; score += 3 if low <= value <= high else -2
    if checks == 0: score = 0
    score=max(0,min(100,round(score,1)))
    status="Excellent" if score>=85 else "Good" if score>=70 else "Needs Attention" if score>0 else "Awaiting Data"
    return score,status
