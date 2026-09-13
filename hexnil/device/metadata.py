"""Device health check and metadata collection module."""

import logging
from typing import Dict, List, Optional, Tuple

from hexnil.device.adb import AdbClient
from hexnil.device.models import AdbStatus, DeviceMetadata
from hexnil.exceptions import DeviceOfflineError

logger = logging.getLogger("hexnil.metadata")

# Standard Android properties mapped to DeviceMetadata fields
PROPERTY_MAPPING = {
    "manufacturer": ["ro.product.manufacturer", "ro.product.brand"],
    "model": ["ro.product.model"],
    "codename": ["ro.product.device", "ro.build.product"],
    "android_version": ["ro.build.version.release"],
    "sdk": ["ro.build.version.sdk"],
    "build_id": ["ro.build.id", "ro.build.display.id"],
    "build_fingerprint": ["ro.build.fingerprint"],
    "abi": ["ro.product.cpu.abi"],
}


def parse_properties_map(
    props: Dict[str, str], serial: str
) -> Tuple[DeviceMetadata, List[str]]:
    """Convert raw Android getprop key-value map into a structured DeviceMetadata.

    Handles missing optional fields gracefully and records descriptive warnings.
    """
    warnings: List[str] = []
    extracted: Dict[str, Optional[object]] = {"serial": serial}

    for field_name, candidate_keys in PROPERTY_MAPPING.items():
        val: Optional[str] = None
        for key in candidate_keys:
            raw_val = props.get(key)
            if raw_val is not None and raw_val.strip():
                val = raw_val.strip()
                break

        if val is None:
            warnings.append(
                f"Missing property for '{field_name}' (checked keys: {', '.join(candidate_keys)})"
            )
            extracted[field_name] = None
        else:
            if field_name == "sdk":
                try:
                    extracted[field_name] = int(val)
                except ValueError:
                    warnings.append(f"Invalid integer for SDK property '{val}'")
                    extracted[field_name] = None
            else:
                extracted[field_name] = val

    metadata = DeviceMetadata(**extracted)
    return metadata, warnings


class MetadataCollector:
    """Collects hardware and OS build metadata from an Android device via ADB."""

    def __init__(self, adb_client: Optional[AdbClient] = None):
        self.adb = adb_client or AdbClient()

    def check_health(self, serial: str) -> AdbStatus:
        """Run serial-targeted health check 'adb -s <serial> get-state'.

        Raises DeviceOfflineError if device state is not 'device'.
        """
        state = self.adb.get_state(serial)
        if state != "device":
            raise DeviceOfflineError(
                serial,
                suggestion=f"Health check failed. Device reported state '{state}'. Expected 'device'.",
            )
        return AdbStatus(state=state, connected=True)

    def collect(
        self, serial: str
    ) -> Tuple[DeviceMetadata, AdbStatus, List[str]]:
        """Collect verified device metadata, running a health check first."""
        # Step 1: Health check
        status = self.check_health(serial)

        # Step 2: Fetch properties (batch getprop with fallback to individual keys)
        all_props = self.adb.get_all_props(serial)

        # If batch returned nothing (rare custom ROM/emulators), query individual keys
        if not all_props:
            logger.debug("Batch getprop returned empty. Querying keys individually.")
            for candidate_keys in PROPERTY_MAPPING.values():
                for key in candidate_keys:
                    val = self.adb.get_prop(serial, key)
                    if val:
                        all_props[key] = val

        # Step 3: Parse and generate warnings
        metadata, warnings = parse_properties_map(all_props, serial)

        if warnings:
            logger.info(
                "Device %s metadata collected with %d warning(s): %s",
                serial,
                len(warnings),
                "; ".join(warnings),
            )
        else:
            logger.info("Device %s metadata collected successfully with no warnings.", serial)

        return metadata, status, warnings
