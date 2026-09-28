import json

def parse_json_object(value: str) -> dict:
    try:
        obj=json.loads(value); return obj if isinstance(obj,dict) else {}
    except Exception: return {}
