from __future__ import annotations
import json
import re
from typing import Any

PARAM_KEYS={"ph":"ph","pH":"ph","N":"nitrogen","nitrogen":"nitrogen","P":"phosphorus","phosphorus":"phosphorus","K":"potassium","potassium":"potassium","EC":"ec","ec":"ec","moisture":"moisture","temperature":"temperature","temp":"temperature","organic_carbon":"organic_carbon","OC":"organic_carbon"}

def parse_sensor_line(line: str) -> dict[str,float]:
    line=line.strip()
    if not line: return {}
    try:
        data=json.loads(line)
        return {PARAM_KEYS[k]:float(v) for k,v in data.items() if k in PARAM_KEYS and v not in (None,"")}
    except Exception:
        out={}
        for key,val in re.findall(r"([A-Za-z_]+)\s*[:=]\s*(-?\d+(?:\.\d+)?)",line):
            if key in PARAM_KEYS: out[PARAM_KEYS[key]]=float(val)
        return out

def list_serial_ports():
    try:
        from serial.tools import list_ports
        return [{"device":p.device,"description":p.description,"manufacturer":p.manufacturer} for p in list_ports.comports()]
    except Exception:
        return []

def read_once(port: str, baudrate: int, timeout: float = 8.0):
    import serial
    with serial.Serial(port, baudrate=baudrate, timeout=timeout) as ser:
        line=ser.readline().decode("utf-8",errors="ignore")
    values=parse_sensor_line(line)
    if not values: raise ValueError("No supported soil values were received from the serial device")
    return values
