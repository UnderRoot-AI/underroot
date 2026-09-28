import re

# Accept common laboratory/soil-card formats: "pH: 6.8", "pH 6.8", "N = 42", etc.
PARAM_PATTERNS = {
    "ph": [r"\bpH\s*[:=\-]?\s*([0-9]+(?:\.[0-9]+)?)"],
    "nitrogen": [r"(?:nitrogen|available\s*N|\bN\b)\s*[:=\-]?\s*([0-9]+(?:\.[0-9]+)?)"],
    "phosphorus": [r"(?:phosphorus|available\s*P|\bP\b)\s*[:=\-]?\s*([0-9]+(?:\.[0-9]+)?)"],
    "potassium": [r"(?:potassium|available\s*K|\bK\b)\s*[:=\-]?\s*([0-9]+(?:\.[0-9]+)?)"],
    "ec": [r"(?:EC|electrical\s+conductivity)\s*[:=\-]?\s*([0-9]+(?:\.[0-9]+)?)"],
    "moisture": [r"(?:moisture|water\s+content)\s*[:=\-]?\s*([0-9]+(?:\.[0-9]+)?)"],
    "temperature": [r"(?:temperature|temp|soil\s+temperature)\s*[:=\-]?\s*(-?[0-9]+(?:\.[0-9]+)?)"],
    "organic_carbon": [r"(?:organic\s+carbon|organic\s+C|\bOC\b)\s*[:=\-]?\s*([0-9]+(?:\.[0-9]+)?)"],
}

def extract_parameters(text: str) -> dict[str, float]:
    values: dict[str, float] = {}
    normalized = text.replace("–", "-").replace("—", "-")
    for key, patterns in PARAM_PATTERNS.items():
        for pattern in patterns:
            match = re.search(pattern, normalized, flags=re.I)
            if match:
                try:
                    values[key] = float(match.group(1))
                    break
                except ValueError:
                    pass
    return values
