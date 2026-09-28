import base64, hashlib, os

def make_hash(password: str) -> str:
    salt = b"smart-soil-developer-salt-v1"
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
    return "pbkdf2_sha256$310000$" + base64.b64encode(salt).decode() + "$" + base64.b64encode(digest).decode()
