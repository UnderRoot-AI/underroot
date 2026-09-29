"""
Device ingestion service.

Responsibilities
────────────────
1. Accept a validated hardware reading payload.
2. Store the raw/normalized measurements in HardwareReading.
3. Map core parameters to the existing SoilTest workflow.
4. Run the existing soil analyzer + health score.
5. Return both the stored reading and the created SoilTest.

This service is the only bridge between hardware readings and the existing
intelligence layer.  The soil analyzer, health score, and recommendation
engine are NOT duplicated — they are called as-is.
"""
from __future__ import annotations
import json
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.device import Device
from app.models.hardware_reading import HardwareReading
from app.models.soil_test import SoilTest
from app.models.report import Report
from app.repositories.device_repository import create_reading, touch_device
from app.services.soil_service import calculate_health
from app.schemas.hardware import CORE_PARAMS

# Columns that are core SoilTest parameters (must match SoilTest ORM attributes)
_SOIL_TEST_COLUMNS = CORE_PARAMS


def ingest_reading(
    db: Session,
    device: Device,
    measurements: dict[str, dict],  # {key: {"value": float, "unit": str}}
    reading_timestamp: datetime | None = None,
    raw_payload: str | None = None,
    report_db: Session | None = None,
) -> tuple[HardwareReading, SoilTest]:
    """
    Ingest a hardware measurement and automatically create a SoilTest.

    Parameters
    ----------
    db               : Main database session
    device           : ORM Device object (ownership already verified by caller)
    measurements     : Normalized measurement dict (from adapter or directly from schema)
    reading_timestamp: Timestamp claimed by the device
    raw_payload      : Original request body as string (for traceability)
    report_db        : Report database session (optional — skipped when not provided)

    Returns
    -------
    (HardwareReading, SoilTest)
    """

    # Capture device attributes before any commit (commits expire ORM attributes)
    _device_pk   = device.id
    _user_id     = device.user_id
    _device_name = device.name
    _device_eid  = device.device_id
    _source      = _source_for(device)
    _manufacturer = device.manufacturer
    _model       = device.model

    # 1. Persist the raw/normalized reading (all parameters including extended ones)
    reading = create_reading(
        db,
        device_id=_device_pk,
        user_id=_user_id,
        reading_timestamp=reading_timestamp,
        source=_source,
        manufacturer=_manufacturer,
        model=_model,
        measurements={k: v for k, v in measurements.items()},
        raw_payload=raw_payload,
    )

    # 2. Extract only core SoilTest-compatible parameters
    soil_params: dict[str, float | None] = {}
    for key in _SOIL_TEST_COLUMNS:
        entry = measurements.get(key)
        if entry is not None and isinstance(entry, dict):
            soil_params[key] = entry.get("value")
        else:
            soil_params[key] = None

    # 3. Calculate health score using the existing algorithm
    score, status = calculate_health({k: v for k, v in soil_params.items() if v is not None})

    # 4. Create the SoilTest — source is "hardware", "soilx", etc. based on device profile
    soil_test = SoilTest(
        user_id=_user_id,
        source=_source,
        device_id=_device_eid,
        health_score=score,
        health_status=status,
        notes=f"Auto-created from device {_device_name} ({_device_eid})",
        **{k: v for k, v in soil_params.items()},
    )
    db.add(soil_test)
    db.flush()  # get soil_test.id before commit

    # 5. Link reading → soil_test
    reading.soil_test_id = soil_test.id

    # 6. Optionally create a Report record (mirrors the manual soil test flow)
    if report_db is not None:
        try:
            from app.services.report_store_service import upsert_report_record  # noqa
            params_json = {k: v for k, v in soil_params.items() if v is not None}
            report = Report(
                user_id=_user_id,
                soil_test_id=soil_test.id,
                status="generated",
                extracted_parameters=json.dumps(params_json),
                extracted_text=(
                    f"Auto-generated from hardware device: {_device_name} "
                    f"({_manufacturer or ''} {_model or ''} / {_device_eid})"
                ),
            )
            db.add(report)
            db.flush()
            upsert_report_record(
                report_db,
                app_report_id=report.id,
                user_id=_user_id,
                soil_test_id=soil_test.id,
                status="generated",
                extracted_text=report.extracted_text,
                extracted_parameters=params_json,
            )
        except Exception:
            # Report creation is non-critical — ingest still succeeds
            pass

    # 7. Update device heartbeat
    touch_device(db, device)

    db.commit()
    db.refresh(reading)
    db.refresh(soil_test)

    return reading, soil_test


def _source_for(device: Device) -> str:
    """Derive a source label from the device profile."""
    if device.manufacturer and "reve" in device.manufacturer.lower():
        return "soilx"
    if device.model and "soilx" in device.model.lower():
        return "soilx"
    return "hardware"
