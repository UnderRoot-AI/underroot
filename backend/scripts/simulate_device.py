#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
UnderRoot Hardware Simulator
DEVELOPMENT / DEMO USE ONLY — NOT FOR PRODUCTION
═══════════════════════════════════════════════════════════════════════════════

Simulates a soil-sensing device (e.g. a device similar to REVE SoilX) sending
realistic measurements to the UnderRoot ingestion API.

This script is provided ONLY to demonstrate the complete end-to-end hardware
flow without a physical device.  It requires:

  1. A running UnderRoot backend  (uvicorn app.main:app --port 8001)
  2. A registered user account
  3. A registered device in that account

Usage
─────
  cd backend
  python scripts/simulate_device.py \\
      --email farmer@example.com \\
      --password YourPassword \\
      --device-pk 1 \\
      --count 1

Arguments
─────────
  --email      : Registered user email
  --password   : User password
  --device-pk  : Device primary key (integer id from GET /api/devices)
  --count      : Number of readings to send (default: 1)
  --interval   : Seconds between readings when count > 1 (default: 5)
  --base-url   : API base URL (default: http://127.0.0.1:8001/api)
  --vary       : Add small random variation to values (recommended for demo)

Example output
──────────────
  [SIM] Logging in as farmer@example.com ...
  [SIM] Authenticated. Token acquired.
  [SIM] Sending reading 1/1 to device pk=1 ...
  [SIM] ✓ Reading stored  | id=3
  [SIM] ✓ SoilTest created | id=5 | score=74.3 | status=Good
  [SIM] Done.

═══════════════════════════════════════════════════════════════════════════════
⚠  DEVELOPMENT ONLY — This script uses real credentials and real API calls.
   Do NOT expose an unauthenticated version of this.
   Do NOT hardcode production credentials in this file.
═══════════════════════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone


# ── Base measurements (realistic Indian agricultural soil values) ──────────────
_BASE_MEASUREMENTS = {
    "ph":             {"value": 6.8,  "unit": "pH"},
    "ec":             {"value": 0.42, "unit": "dS/m"},
    "nitrogen":       {"value": 185,  "unit": "kg/ha"},
    "phosphorus":     {"value": 32,   "unit": "kg/ha"},
    "potassium":      {"value": 210,  "unit": "kg/ha"},
    "moisture":       {"value": 38.5, "unit": "%"},
    "temperature":    {"value": 27.4, "unit": "°C"},
    "organic_carbon": {"value": 0.72, "unit": "%"},
    # Extended parameters (SoilX-class devices can provide these)
    "sulphur":        {"value": 18.0, "unit": "mg/kg"},
    "zinc":           {"value": 1.2,  "unit": "mg/kg"},
    "iron":           {"value": 8.5,  "unit": "mg/kg"},
    "manganese":      {"value": 6.3,  "unit": "mg/kg"},
    "copper":         {"value": 0.9,  "unit": "mg/kg"},
    "boron":          {"value": 0.6,  "unit": "mg/kg"},
}

# Variation ranges (as ± percentage of base value)
_VARIATION = {
    "ph":             0.03,
    "ec":             0.10,
    "nitrogen":       0.08,
    "phosphorus":     0.10,
    "potassium":      0.08,
    "moisture":       0.12,
    "temperature":    0.05,
    "organic_carbon": 0.08,
    "sulphur":        0.15,
    "zinc":           0.20,
    "iron":           0.15,
    "manganese":      0.18,
    "copper":         0.20,
    "boron":          0.20,
}

# Bounds to keep within realistic range
_BOUNDS = {
    "ph":             (4.0, 9.0),
    "ec":             (0.05, 10.0),
    "nitrogen":       (10.0, 600.0),
    "phosphorus":     (1.0, 200.0),
    "potassium":      (50.0, 800.0),
    "moisture":       (1.0, 95.0),
    "temperature":    (5.0, 45.0),
    "organic_carbon": (0.1, 8.0),
    "sulphur":        (1.0, 100.0),
    "zinc":           (0.1, 20.0),
    "iron":           (1.0, 50.0),
    "manganese":      (0.5, 40.0),
    "copper":         (0.1, 10.0),
    "boron":          (0.1, 5.0),
}


def _varied(key: str, base: float, vary: bool) -> float:
    if not vary:
        return round(base, 4)
    pct = _VARIATION.get(key, 0.10)
    delta = base * pct * (random.random() * 2 - 1)
    lo, hi = _BOUNDS.get(key, (-1e9, 1e9))
    return round(max(lo, min(hi, base + delta)), 4)


def build_payload(vary: bool = True) -> dict:
    measurements = {}
    for key, entry in _BASE_MEASUREMENTS.items():
        measurements[key] = {
            "value": _varied(key, entry["value"], vary),
            "unit": entry["unit"],
        }
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "measurements": measurements,
    }


def _api_call(url: str, method: str = "GET", body: dict | None = None, token: str | None = None) -> dict:
    data = json.dumps(body).encode() if body else None
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body_txt = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code} {e.reason}: {body_txt}") from e


def login(base_url: str, email: str, password: str) -> str:
    print(f"[SIM] Logging in as {email} ...")
    resp = _api_call(f"{base_url}/auth/login", "POST", {"email": email, "password": password})
    token = resp.get("access_token") or resp.get("token")
    if not token:
        raise RuntimeError(f"Login failed — no access_token in response: {resp}")
    print("[SIM] Authenticated. Token acquired.")
    return token


def send_reading(base_url: str, token: str, device_pk: int, payload: dict, index: int, total: int) -> None:
    print(f"[SIM] Sending reading {index}/{total} to device pk={device_pk} ...")
    resp = _api_call(f"{base_url}/devices/{device_pk}/readings", "POST", payload, token)
    reading = resp.get("reading", {})
    soil_test = resp.get("soil_test", {})
    r_id = reading.get("id", "?")
    st_id = soil_test.get("id", "?")
    st_score = soil_test.get("health_score", "?")
    st_status = soil_test.get("health_status", "?")
    print(f"[SIM] ✓ Reading stored  | id={r_id}")
    print(f"[SIM] ✓ SoilTest created | id={st_id} | score={st_score} | status={st_status}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="UnderRoot hardware simulator — DEVELOPMENT/DEMO ONLY",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--email",      required=True,  help="User email")
    parser.add_argument("--password",   required=True,  help="User password")
    parser.add_argument("--device-pk",  required=True, type=int, help="Device primary key (integer id)")
    parser.add_argument("--count",      default=1,     type=int, help="Number of readings to send")
    parser.add_argument("--interval",   default=5,     type=float, help="Seconds between readings")
    parser.add_argument("--base-url",   default="http://127.0.0.1:8001/api", help="API base URL")
    parser.add_argument("--vary",       action="store_true", default=True,
                        help="Add small random variation to measurements (default: on)")
    parser.add_argument("--no-vary",    dest="vary", action="store_false")
    args = parser.parse_args()

    print("═" * 65)
    print("  UnderRoot Hardware Simulator — DEVELOPMENT / DEMO ONLY")
    print("═" * 65)

    token = login(args.base_url, args.email, args.password)

    for i in range(1, args.count + 1):
        payload = build_payload(vary=args.vary)
        try:
            send_reading(args.base_url, token, args.device_pk, payload, i, args.count)
        except RuntimeError as e:
            print(f"[SIM] ✗ ERROR on reading {i}: {e}", file=sys.stderr)
            sys.exit(1)
        if i < args.count:
            print(f"[SIM] Waiting {args.interval}s ...")
            time.sleep(args.interval)

    print("[SIM] Done.")
    print("═" * 65)
    print("  Demo flow complete. Check the UnderRoot dashboard to see")
    print("  the hardware-generated soil test and health score.")
    print("═" * 65)


if __name__ == "__main__":
    main()
