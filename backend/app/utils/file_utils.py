from pathlib import Path

def safe_filename(filename: str, default: str = "upload") -> str:
    return Path(filename or default).name

def is_allowed(filename: str, extensions: set[str]) -> bool:
    return Path(filename).suffix.lower() in {x.lower() for x in extensions}
