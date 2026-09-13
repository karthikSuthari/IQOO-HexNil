"""ADB discovery and device selection module."""

import logging
from typing import List, Optional

from hexnil.device.adb import AdbClient
from hexnil.device.models import DeviceState, DiscoveredDevice
from hexnil.exceptions import (
    DeviceNotFoundError,
    DeviceOfflineError,
    DeviceUnauthorizedError,
    MalformedAdbOutputError,
    MultipleDevicesError,
    NoDevicesConnectedError,
)

logger = logging.getLogger("hexnil.discovery")


def parse_adb_devices_output(raw_output: str) -> List[DiscoveredDevice]:
    """Parse output of 'adb devices -l' or 'adb devices'.

    Handles daemon startup notices, extra whitespace, state tokens,
    and optional property annotations (product, model, device, transport_id).
    """
    devices: List[DiscoveredDevice] = []
    lines = raw_output.strip().splitlines()

    for line in lines:
        cleaned = line.strip()
        # Skip empty lines, daemon messages, and header line
        if not cleaned:
            continue
        if cleaned.startswith("*") or cleaned.startswith("List of devices attached"):
            continue

        parts = cleaned.split()
        if len(parts) < 2:
            # Not a device line, skip or warn
            continue

        serial = parts[0]
        state_str = parts[1]
        state = DeviceState.from_str(state_str)

        device_info = {
            "serial": serial,
            "state": state,
            "product": None,
            "model": None,
            "device": None,
            "transport_id": None,
        }

        # Parse key:value tokens if present (e.g. from 'adb devices -l')
        for token in parts[2:]:
            if ":" in token:
                key, val = token.split(":", 1)
                if key in device_info:
                    device_info[key] = val

        devices.append(DiscoveredDevice(**device_info))

    return devices


class DeviceDiscovery:
    """Discovers and selects target Android devices via ADB."""

    def __init__(self, adb_client: Optional[AdbClient] = None):
        self.adb = adb_client or AdbClient()

    def list_devices(self) -> List[DiscoveredDevice]:
        """Query ADB for all connected devices."""
        raw_output = self.adb.run_cmd(["devices", "-l"])
        return parse_adb_devices_output(raw_output)

    def select_device(
        self,
        target_serial: Optional[str] = None,
    ) -> DiscoveredDevice:
        """Select a single usable Android device according to Phase 1 policy.

        Rules:
        - If an explicit serial is passed:
            - Verifies it is present in 'adb devices'.
            - Ensures state is 'device' (usable).
        - If no serial is passed:
            - If no devices at all: raise NoDevicesConnectedError.
            - If 0 usable devices but unauthorized/offline devices exist:
              raise specific actionable error.
            - If exactly 1 usable device: select and return it.
            - If multiple usable devices: raise MultipleDevicesError.
        """
        all_devices = self.list_devices()
        available_serials = [d.serial for d in all_devices]

        # Case 1: Explicit target serial provided
        if target_serial:
            target_cleaned = target_serial.strip()
            match = next((d for d in all_devices if d.serial == target_cleaned), None)
            if not match:
                raise DeviceNotFoundError(target_cleaned, available_serials)

            if match.state == DeviceState.UNAUTHORIZED:
                raise DeviceUnauthorizedError(match.serial)
            elif match.state == DeviceState.OFFLINE:
                raise DeviceOfflineError(match.serial)
            elif not match.is_usable:
                raise DeviceOfflineError(
                    match.serial,
                    suggestion=f"Device is in '{match.state.value}' state. Ensure it is booted and authorized.",
                )

            return match

        # Case 2: No serial provided - auto-selection rules
        if not all_devices:
            raise NoDevicesConnectedError()

        usable_devices = [d for d in all_devices if d.is_usable]

        if len(usable_devices) == 1:
            selected = usable_devices[0]
            logger.info("Automatically selected single active device: %s", selected.serial)
            return selected

        if len(usable_devices) > 1:
            raise MultipleDevicesError([d.serial for d in usable_devices])

        # If we reach here, devices are connected but none are in 'device' state
        unauthorized = [d for d in all_devices if d.state == DeviceState.UNAUTHORIZED]
        if unauthorized:
            raise DeviceUnauthorizedError(unauthorized[0].serial)

        offline = [d for d in all_devices if d.state == DeviceState.OFFLINE]
        if offline:
            raise DeviceOfflineError(offline[0].serial)

        # Other non-usable states (bootloader, recovery, etc.)
        first = all_devices[0]
        raise DeviceOfflineError(
            first.serial,
            suggestion=f"Device is in '{first.state.value}' state. Hexnil requires a running Android system with USB debugging.",
        )
