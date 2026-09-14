"""Device OS state tracking and update detection gate."""

import datetime
import logging
from typing import Dict, List, Optional, Tuple

from hexnil.device.adb import AdbClient
from hexnil.monitor.models import (
    DeviceOsState,
    TransitionType,
    UpdateTransition,
)

logger = logging.getLogger("hexnil.monitor.state_tracker")

# Android system properties that define OS identity
OS_IDENTITY_PROPERTIES = {
    "build_fingerprint": "ro.build.fingerprint",
    "build_id": "ro.build.id",
    "android_version": "ro.build.version.release",
    "security_patch_level": "ro.build.version.security_patch",
    "incremental_build": "ro.build.version.incremental",
    "display_build_id": "ro.build.display.id",
}

EXTENDED_PROPERTIES = {
    "kernel_version": "ro.kernel.version",
    "baseband_version": "gsm.version.baseband",
}


class DeviceStateTracker:
    """Captures and compares device OS state to detect real system updates."""

    def __init__(self, adb: AdbClient):
        self.adb = adb

    def capture_os_state(self, serial: str) -> DeviceOsState:
        """Capture the current OS/software identity of the device."""
        props = self.adb.get_all_props(serial)
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Extract core identity properties
        build_fingerprint = props.get("ro.build.fingerprint", "unknown")
        build_id = props.get("ro.build.id") or props.get("ro.build.display.id") or "unknown"
        android_version = props.get("ro.build.version.release", "unknown")
        security_patch = props.get("ro.build.version.security_patch")
        incremental = props.get("ro.build.version.incremental")
        display_id = props.get("ro.build.display.id")

        # Extended properties (best-effort)
        kernel_version = props.get("ro.kernel.version")
        baseband_version = props.get("gsm.version.baseband")

        return DeviceOsState(
            build_fingerprint=build_fingerprint,
            build_id=build_id,
            android_version=android_version,
            security_patch_level=security_patch,
            incremental_build=incremental,
            display_build_id=display_id,
            kernel_version=kernel_version,
            baseband_version=baseband_version,
            captured_at=now_iso,
        )

    def has_update_occurred(
        self, v0_state: DeviceOsState, current_state: DeviceOsState
    ) -> bool:
        """Check if the OS has changed by comparing identity tuples."""
        return v0_state.identity_tuple() != current_state.identity_tuple()

    def classify_transition(
        self, v0_state: DeviceOsState, v1_state: DeviceOsState
    ) -> TransitionType:
        """Classify the type of OS transition that occurred."""
        # Major version change (e.g., Android 15 → 16)
        if v0_state.android_version != v1_state.android_version:
            try:
                v0_major = int(v0_state.android_version.split(".")[0])
                v1_major = int(v1_state.android_version.split(".")[0])
                if v1_major > v0_major:
                    return TransitionType.OS_MAJOR_UPDATE
            except (ValueError, IndexError):
                pass
            return TransitionType.OS_MINOR_UPDATE

        # Security patch level change only
        if (
            v0_state.security_patch_level != v1_state.security_patch_level
            and v0_state.build_id == v1_state.build_id
        ):
            return TransitionType.SECURITY_PATCH

        # Build ID changed (vendor/OEM update)
        if v0_state.build_id != v1_state.build_id:
            return TransitionType.VENDOR_UPDATE

        # Fingerprint changed but nothing else obvious
        if v0_state.build_fingerprint != v1_state.build_fingerprint:
            return TransitionType.BUILD_CHANGE

        return TransitionType.UNKNOWN

    def detect_changes(
        self, v0_state: DeviceOsState, v1_state: DeviceOsState
    ) -> List[str]:
        """Enumerate specific field-level changes between V0 and V1 OS states."""
        changes: List[str] = []

        if v0_state.build_fingerprint != v1_state.build_fingerprint:
            changes.append(
                f"Build fingerprint: {v0_state.build_fingerprint} → {v1_state.build_fingerprint}"
            )
        if v0_state.build_id != v1_state.build_id:
            changes.append(f"Build ID: {v0_state.build_id} → {v1_state.build_id}")
        if v0_state.android_version != v1_state.android_version:
            changes.append(
                f"Android version: {v0_state.android_version} → {v1_state.android_version}"
            )
        if v0_state.security_patch_level != v1_state.security_patch_level:
            changes.append(
                f"Security patch: {v0_state.security_patch_level} → {v1_state.security_patch_level}"
            )
        if v0_state.incremental_build != v1_state.incremental_build:
            changes.append(
                f"Incremental build: {v0_state.incremental_build} → {v1_state.incremental_build}"
            )
        if v0_state.kernel_version != v1_state.kernel_version:
            changes.append(
                f"Kernel: {v0_state.kernel_version} → {v1_state.kernel_version}"
            )
        if v0_state.baseband_version != v1_state.baseband_version:
            changes.append(
                f"Baseband: {v0_state.baseband_version} → {v1_state.baseband_version}"
            )

        return changes

    def create_transition_record(
        self, v0_state: DeviceOsState, v1_state: DeviceOsState
    ) -> UpdateTransition:
        """Create a complete transition record from V0 to V1."""
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        transition_type = self.classify_transition(v0_state, v1_state)
        changes = self.detect_changes(v0_state, v1_state)

        logger.info(
            "OS transition detected: %s — %d change(s): %s",
            transition_type.value,
            len(changes),
            "; ".join(changes[:3]),
        )

        return UpdateTransition(
            v0_state=v0_state,
            v1_state=v1_state,
            transition_type=transition_type,
            transition_detected_at=now_iso,
            v0_fingerprint=v0_state.build_fingerprint,
            v1_fingerprint=v1_state.build_fingerprint,
            changes=changes,
        )
