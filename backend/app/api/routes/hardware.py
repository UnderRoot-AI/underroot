from fastapi import APIRouter, HTTPException, Query
from app.core.config import settings
from app.integrations.hardware.client import list_serial_ports, read_once

router=APIRouter(prefix="/hardware", tags=["Hardware"])

@router.get("/ports")
def ports():
    return {"ports":list_serial_ports(),"baudrate":settings.hardware_baudrate}

@router.get("/read")
def read_sensor(port: str = Query(..., min_length=2)):
    try:
        return {"parameters":read_once(port, settings.hardware_baudrate)}
    except Exception as exc:
        raise HTTPException(422, f"Hardware read failed: {exc}")
