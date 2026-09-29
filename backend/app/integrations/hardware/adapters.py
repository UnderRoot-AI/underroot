"""
Hardware adapter framework for UnderRoot.

Architecture
────────────
Hardware device
    → Hardware-specific adapter (implements HardwareAdapter)
    → normalize()  — converts raw payload to a normalized dict
    → validate()   — raises ValueError on bad data
    → get_supported_parameters()  — introspection
    → UnderRoot ingestion API
    → Validation + storage
    → Existing SoilTest workflow

Supported adapter classes
─────────────────────────
- GenericAdapter   : accepts the UnderRoot JSON ingestion format directly
                     (any device that can POST JSON)

Planned (not yet implemented — stub interface provided):
- SoilXAdapter     : REVE Nano-Science SoilX (requires official BLE/API interface)
- ModbusAdapter    : Modbus RTU/TCP devices
- MQTTAdapter      : MQTT broker-connected devices
- LoRaWANAdapter   : LoRaWAN gateway devices

To add a new adapter:
  1. Subclass HardwareAdapter.
  2. Implement normalize(), validate(), get_supported_parameters().
  3. Register it in AdapterRegistry with a unique key.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any


# ── Parameter key aliases ─────────────────────────────────────────────────────
# Maps common hardware field names → UnderRoot canonical names.
_ALIASES: dict[str, str] = {
    "pH": "ph",
    "PH": "ph",
    "N": "nitrogen",
    "P": "phosphorus",
    "K": "potassium",
    "EC": "ec",
    "temp": "temperature",
    "OC": "organic_carbon",
    "oc": "organic_carbon",
}


def canonical(key: str) -> str:
    """Return the UnderRoot canonical parameter name for a raw hardware key."""
    return _ALIASES.get(key, key.lower())


# ── Base interface ────────────────────────────────────────────────────────────
class HardwareAdapter(ABC):
    """
    Abstract base class for all hardware adapters.

    Subclasses translate hardware-specific payloads into the UnderRoot
    normalized measurement format:

      {
        "<parameter_key>": {"value": <float>, "unit": "<unit_string>"}
      }

    where <parameter_key> is a canonical UnderRoot parameter name (lowercase).
    """

    @abstractmethod
    def normalize(self, payload: Any) -> dict[str, dict]:
        """
        Convert a raw hardware payload to the UnderRoot normalized measurement dict.

        Returns
        -------
        dict mapping parameter key → {"value": float, "unit": str}
        Never raises — return an empty dict on unrecognised input.
        """

    @abstractmethod
    def validate(self, payload: Any) -> None:
        """
        Validate a raw hardware payload.

        Raises
        ------
        ValueError with a descriptive message if the payload is invalid.
        Does nothing if valid.
        """

    @abstractmethod
    def get_supported_parameters(self) -> list[str]:
        """Return a list of parameter keys this adapter can produce."""


# ── Generic adapter ───────────────────────────────────────────────────────────
class GenericAdapter(HardwareAdapter):
    """
    Accepts the UnderRoot JSON ingestion format directly.

    Expected payload shape (mirrors ReadingIngest schema):
      {
        "measurements": {
          "ph":  {"value": 6.8, "unit": "pH"},
          "ec":  {"value": 0.42, "unit": "dS/m"},
          ...
        }
      }

    Any device that can HTTP POST a JSON body in this format works out of the box.
    This is the recommended interface for custom hardware integrations.
    """

    # Parameters this adapter recognises by default.
    # It is intentionally open-ended; any key is forwarded as-is.
    _KNOWN = [
        "ph", "ec", "nitrogen", "phosphorus", "potassium",
        "moisture", "temperature", "organic_carbon",
        "sulphur", "boron", "copper", "iron", "manganese", "zinc",
    ]

    def normalize(self, payload: Any) -> dict[str, dict]:
        if not isinstance(payload, dict):
            return {}
        measurements = payload.get("measurements", payload)
        result: dict[str, dict] = {}
        for raw_key, val in measurements.items():
            key = canonical(raw_key)
            if isinstance(val, dict) and "value" in val:
                result[key] = {"value": float(val["value"]), "unit": val.get("unit", "")}
            elif isinstance(val, (int, float)):
                result[key] = {"value": float(val), "unit": ""}
        return result

    def validate(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            raise ValueError("Payload must be a JSON object")
        measurements = payload.get("measurements", payload)
        if not measurements:
            raise ValueError("Payload must contain at least one measurement")

    def get_supported_parameters(self) -> list[str]:
        return list(self._KNOWN)


# ── SoilX adapter stub ────────────────────────────────────────────────────────
class SoilXAdapterStub(HardwareAdapter):
    """
    Placeholder for the REVE Nano-Science SoilX adapter.

    STATUS: NOT IMPLEMENTED — no official BLE/API interface is publicly available.

    Once REVE Nano-Science publishes an official SDK, API, or BLE GATT profile,
    this stub can be replaced with a real implementation.

    DO NOT:
    - Invent BLE UUIDs
    - Reverse-engineer the SoilX Bluetooth protocol
    - Create fake endpoints claiming to be REVE

    DO:
    - Use this class to register SoilX as a recognised device profile
    - Allow manufacturer="REVE Nano-Science" / model="SoilX" in device registration
    - Accept SoilX readings through the GenericAdapter HTTP endpoint when
      a third-party integration bridge (e.g., mobile app → REST) is available
    """

    MANUFACTURER = "REVE Nano-Science"
    MODEL = "SoilX"

    # Extended parameter set that SoilX is known to measure.
    # Values are mapped to UnderRoot canonical names where possible.
    EXTENDED_PARAMS = [
        "ph", "ec", "nitrogen", "phosphorus", "potassium",
        "organic_carbon", "moisture", "temperature",
        "sulphur", "boron", "copper", "iron", "manganese", "zinc",
    ]

    def normalize(self, payload: Any) -> dict[str, dict]:
        raise NotImplementedError(
            "SoilX BLE/API interface is not publicly available. "
            "Use GenericAdapter with an HTTP bridge for now."
        )

    def validate(self, payload: Any) -> None:
        raise NotImplementedError("SoilX adapter is not yet implemented.")

    def get_supported_parameters(self) -> list[str]:
        return list(self.EXTENDED_PARAMS)


# ── Registry ──────────────────────────────────────────────────────────────────
class AdapterRegistry:
    """
    Central registry of hardware adapters.

    Usage
    -----
    registry = AdapterRegistry()
    adapter  = registry.get("generic")
    result   = adapter.normalize(raw_payload)
    """

    _registry: dict[str, HardwareAdapter] = {}

    def __init__(self) -> None:
        self._registry = {
            "generic": GenericAdapter(),
            "http":    GenericAdapter(),  # HTTP devices use the same format
            # SoilX is registered as a profile but uses GenericAdapter for data
            "soilx":   GenericAdapter(),
        }

    def get(self, key: str) -> HardwareAdapter:
        """Return the adapter for the given key, falling back to GenericAdapter."""
        return self._registry.get(key.lower(), self._registry["generic"])

    def registered_keys(self) -> list[str]:
        return list(self._registry.keys())


# Module-level singleton
_registry = AdapterRegistry()


def get_adapter(key: str = "generic") -> HardwareAdapter:
    """Return the adapter for the given key (module-level convenience function)."""
    return _registry.get(key)
