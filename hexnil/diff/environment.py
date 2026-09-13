"""Environment snapshot comparison and environmental drift tracking."""

import logging
from typing import Dict, List, Optional

from hexnil.baseline.models import EnvironmentSnapshot
from hexnil.diff.models import EnvironmentComparison, EnvironmentMatchStatus

logger = logging.getLogger("hexnil.diff.environment")


def compare_environment_snapshots(
    v0_snapshot: EnvironmentSnapshot,
    v1_snapshot: EnvironmentSnapshot,
) -> EnvironmentComparison:
    """Compare environmental states between V0 baseline and V1 update experiments."""
    match_statuses: Dict[str, EnvironmentMatchStatus] = {}
    drift_summary: List[str] = []

    # 1. Battery Level
    bat_delta: Optional[float] = None
    if v0_snapshot.battery_level_percent is not None and v1_snapshot.battery_level_percent is not None:
        bat_delta = round(v0_snapshot.battery_level_percent - v1_snapshot.battery_level_percent, 2)
        if abs(bat_delta) > 5.0:
            drift_summary.append(
                f"Battery level drifted by {abs(bat_delta):.1f}% (V0: {v0_snapshot.battery_level_percent}%, V1: {v1_snapshot.battery_level_percent}%)"
            )
            match_statuses["battery_level"] = EnvironmentMatchStatus.CHANGED
        else:
            match_statuses["battery_level"] = EnvironmentMatchStatus.MATCHED
    else:
        match_statuses["battery_level"] = EnvironmentMatchStatus.UNSUPPORTED

    # 2. Battery Charging State
    if v0_snapshot.battery_charging_state and v1_snapshot.battery_charging_state:
        if v0_snapshot.battery_charging_state == v1_snapshot.battery_charging_state:
            match_statuses["charging_state"] = EnvironmentMatchStatus.MATCHED
        else:
            match_statuses["charging_state"] = EnvironmentMatchStatus.CHANGED
            drift_summary.append(
                f"Charging state changed: V0 '{v0_snapshot.battery_charging_state}' -> V1 '{v1_snapshot.battery_charging_state}'"
            )
    else:
        match_statuses["charging_state"] = EnvironmentMatchStatus.UNKNOWN

    # 3. Screen State
    if v0_snapshot.screen_on is not None and v1_snapshot.screen_on is not None:
        if v0_snapshot.screen_on == v1_snapshot.screen_on:
            match_statuses["screen_state"] = EnvironmentMatchStatus.MATCHED
        else:
            match_statuses["screen_state"] = EnvironmentMatchStatus.CHANGED
            drift_summary.append(
                f"Screen power state changed: V0 {v0_snapshot.screen_on} -> V1 {v1_snapshot.screen_on}"
            )
    else:
        match_statuses["screen_state"] = EnvironmentMatchStatus.UNSUPPORTED

    # 4. Thermal Status
    v0_thermal = v0_snapshot.thermal_status or "UNKNOWN"
    v1_thermal = v1_snapshot.thermal_status or "UNKNOWN"
    thermal_transition = f"{v0_thermal} -> {v1_thermal}"
    if v0_thermal != "UNKNOWN" and v1_thermal != "UNKNOWN":
        if v0_thermal == v1_thermal:
            match_statuses["thermal_status"] = EnvironmentMatchStatus.MATCHED
        else:
            match_statuses["thermal_status"] = EnvironmentMatchStatus.CHANGED
            drift_summary.append(f"Thermal status shifted: {thermal_transition}")
    else:
        match_statuses["thermal_status"] = EnvironmentMatchStatus.UNSUPPORTED

    # 5. Network / Wi-Fi
    if v0_snapshot.wifi_enabled is not None and v1_snapshot.wifi_enabled is not None:
        if v0_snapshot.wifi_enabled == v1_snapshot.wifi_enabled:
            match_statuses["wifi_enabled"] = EnvironmentMatchStatus.MATCHED
        else:
            match_statuses["wifi_enabled"] = EnvironmentMatchStatus.CHANGED
            drift_summary.append("Wi-Fi enabled state differs between V0 and V1")
    else:
        match_statuses["wifi_enabled"] = EnvironmentMatchStatus.UNSUPPORTED

    # 6. Device Idle / Doze State
    if v0_snapshot.device_idle_state and v1_snapshot.device_idle_state:
        if v0_snapshot.device_idle_state == v1_snapshot.device_idle_state:
            match_statuses["device_idle_state"] = EnvironmentMatchStatus.MATCHED
        else:
            match_statuses["device_idle_state"] = EnvironmentMatchStatus.CHANGED
    else:
        match_statuses["device_idle_state"] = EnvironmentMatchStatus.UNSUPPORTED

    return EnvironmentComparison(
        v0_snapshot=v0_snapshot,
        v1_snapshot=v1_snapshot,
        battery_level_delta_percent=bat_delta,
        thermal_status_transition=thermal_transition,
        condition_match_statuses=match_statuses,
        drift_summary=drift_summary,
    )
