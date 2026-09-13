"""Pre-run device stabilization policy orchestrator."""

import logging
import time
from typing import Dict, List

from hexnil.baseline.models import StabilizationPolicy, StabilizationResult
from hexnil.device.adb import AdbClient

logger = logging.getLogger("hexnil.baseline.stabilizer")


class DeviceStabilizer:
    """Applies pre-run stabilization policies to achieve controlled measurement conditions."""

    def __init__(self, adb: AdbClient):
        self.adb = adb

    def stabilize(
        self,
        serial: str,
        policy: StabilizationPolicy,
        package_name: str = "com.example.iqoo_hexnil",
    ) -> StabilizationResult:
        """Execute stabilization steps according to declared policy."""
        attempted_actions: List[str] = []
        verified_conditions: Dict[str, bool] = {}
        limitations: List[str] = [
            "Device background services cannot be completely halted without root privileges",
            "Thermal dissipation is passive and dependent on ambient environmental temperature",
        ]
        overall_success = True

        # 1. Wake screen if requested
        if policy.wake_screen:
            attempted_actions.append("wake_screen")
            power_out = self.adb.run_serial_cmd(serial, ["shell", "dumpsys", "power"], check=False)
            is_awake = "Display Power: state=ON" in power_out or "mWakefulness=Awake" in power_out
            if not is_awake:
                self.adb.run_serial_cmd(serial, ["shell", "input", "keyevent", "KEYCODE_WAKEUP"], check=False)
                power_out_after = self.adb.run_serial_cmd(serial, ["shell", "dumpsys", "power"], check=False)
                is_awake = "Display Power: state=ON" in power_out_after or "mWakefulness=Awake" in power_out_after

            verified_conditions["screen_awake"] = is_awake
            if not is_awake:
                overall_success = False

        # 2. Enforce clean app state (force-stop)
        if policy.force_stop_app_before:
            attempted_actions.append(f"force_stop_{package_name}")
            self.adb.run_serial_cmd(serial, ["shell", "am", "force-stop", package_name], check=False)
            pid_out = self.adb.run_serial_cmd(serial, ["shell", "pidof", package_name], check=False).strip()
            is_stopped = not pid_out
            verified_conditions["app_stopped"] = is_stopped
            if not is_stopped:
                limitations.append(f"Application {package_name} still had running processes after force-stop")

        # 3. Check battery minimum
        attempted_actions.append(f"check_battery_min_{policy.enforce_battery_min}%")
        bat_out = self.adb.run_serial_cmd(serial, ["shell", "dumpsys", "battery"], check=False)
        battery_level = 0
        for line in bat_out.splitlines():
            line_s = line.strip()
            if line_s.startswith("level:"):
                try:
                    battery_level = int(line_s.split(":", 1)[1].strip())
                    break
                except ValueError:
                    pass

        battery_ok = battery_level >= policy.enforce_battery_min
        verified_conditions["battery_sufficient"] = battery_ok
        if not battery_ok:
            overall_success = False
            limitations.append(
                f"Battery level ({battery_level}%) is below minimum threshold ({policy.enforce_battery_min}%)"
            )

        # 4. Check charging state expectation
        if policy.enforce_charging_state != "any":
            attempted_actions.append(f"enforce_charging_{policy.enforce_charging_state}")
            usb_powered = "USB powered: true" in bat_out
            ac_powered = "AC powered: true" in bat_out
            is_charging = usb_powered or ac_powered
            actual_state = "charging" if is_charging else "discharging"
            charging_ok = (actual_state == policy.enforce_charging_state)
            verified_conditions["charging_state_match"] = charging_ok
            if not charging_ok:
                limitations.append(
                    f"Charging state was '{actual_state}' but policy expected '{policy.enforce_charging_state}'"
                )

        # 5. Check thermal headroom
        attempted_actions.append(f"check_thermal_max_{policy.max_thermal_level}")
        thermal_map = {"none": 0, "light": 1, "moderate": 2, "severe": 3, "critical": 4}
        max_allowed_level = thermal_map.get(policy.max_thermal_level.lower(), 2)

        thermal_out = self.adb.run_serial_cmd(serial, ["shell", "dumpsys", "thermalservice"], check=False)
        current_level = 0
        for line in thermal_out.splitlines():
            line_s = line.strip()
            if "current thermal status" in line_s.lower():
                try:
                    val_str = line_s.split(":", 1)[1].strip().split()[0]
                    current_level = int(val_str)
                    break
                except Exception:
                    pass

        thermal_ok = current_level <= max_allowed_level
        verified_conditions["thermal_headroom_ok"] = thermal_ok
        if not thermal_ok:
            overall_success = False
            limitations.append(
                f"Thermal level ({current_level}) exceeded maximum allowed ({max_allowed_level})"
            )

        # 6. Stabilization cooldown pause
        if policy.stabilization_cooldown_seconds > 0:
            attempted_actions.append(f"cooldown_pause_{policy.stabilization_cooldown_seconds}s")
            time.sleep(policy.stabilization_cooldown_seconds)

        return StabilizationResult(
            attempted_actions=attempted_actions,
            verified_conditions=verified_conditions,
            limitations=limitations,
            success=overall_success,
        )
