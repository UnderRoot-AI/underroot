def validate_latitude(value: float | None) -> bool: return value is None or -90 <= value <= 90
def validate_longitude(value: float | None) -> bool: return value is None or -180 <= value <= 180
def validate_ph(value: float | None) -> bool: return value is None or 0 <= value <= 14
