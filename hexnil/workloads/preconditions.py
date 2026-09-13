"""Precondition evaluator for controlled workload execution."""

import logging
from typing import Any, Dict
from hexnil.device.adb import AdbClient
from hexnil.workloads.models import PreconditionResult, PreconditionStatus

logger = logging.getLogger("hexnil.workloads.preconditions")


class PreconditionEvaluator:
    """Evaluates and optionally enforces device and application preconditions."""

    def __init__(self, adb: AdbClient):
        self.adb = adb

    def evaluate_all(
        self,
        serial: str,
        preconditions: Dict[str, Any],
        package_name: str = "com.example.iqoo_hexnil",
    ) -> Dict[str, PreconditionResult]:
        """Evaluate all declared preconditions for a workload run."""
        results: Dict[str, PreconditionResult] = {}

        for key, expected in preconditions.items():
            handler = getattr(self, f"_check_{key}", None)
            if handler:
                try:
                    res = handler(serial, expected, package_name=package_name)
                    results[key] = res
                except Exception as exc:
                    logger.warning("Error evaluating precondition %s: %s", key, exc)
                    results[key] = PreconditionResult(
                        name=key,
                        status=PreconditionStatus.ERROR,
                        expected_value=expected,
                        actual_value=None,
                        message=f"Evaluation failed: {exc}",
                    )
            else:
                # Unsupported precondition type
                results[key] = PreconditionResult(
                    name=key,
                    status=PreconditionStatus.NOT_SUPPORTED,
                    expected_value=expected,
                    actual_value=None,
                    message=f"Precondition '{key}' is not supported by current evaluator",
                )

        return results

    def _check_screen_on(
        self, serial: str, expected: bool, **_kwargs
    ) -> PreconditionResult:
        """Verify screen is awake and display is on."""
        out = self.adb.run_serial_cmd(serial, ["shell", "dumpsys", "power"], check=False)
        is_on = "Display Power: state=ON" in out or "mHoldingDisplaySuspendBlocker=true" in out or "mWakefulness=Awake" in out

        if expected and not is_on:
            # Attempt safe wake-up
            self.adb.run_serial_cmd(serial, ["shell", "input", "keyevent", "KEYCODE_WAKEUP"], check=False)
            out_after = self.adb.run_serial_cmd(serial, ["shell", "dumpsys", "power"], check=False)
            is_on = "Display Power: state=ON" in out_after or "mWakefulness=Awake" in out_after

        status = PreconditionStatus.SATISFIED if (is_on == expected) else PreconditionStatus.NOT_SATISFIED
        return PreconditionResult(
            name="screen_on",
            status=status,
            expected_value=expected,
            actual_value=is_on,
            message="Screen is awake" if is_on else "Screen is off or asleep",
        )

    def _check_battery_min_percent(
        self, serial: str, expected_min: int, **_kwargs
    ) -> PreconditionResult:
        """Verify battery level is at or above minimum threshold."""
        out = self.adb.run_serial_cmd(serial, ["shell", "dumpsys", "battery"], check=False)
        level: Optional[int] = None
        for line in out.splitlines():
            line_str = line.strip()
            if line_str.startswith("level:"):
                try:
                    level = int(line_str.split(":", 1)[1].strip())
                    break
                except ValueError:
                    pass

        if level is None:
            return PreconditionResult(
                name="battery_min_percent",
                status=PreconditionStatus.ERROR,
                expected_value=expected_min,
                actual_value=None,
                message="Could not read battery level from dumpsys battery",
            )

        satisfied = level >= expected_min
        return PreconditionResult(
            name="battery_min_percent",
            status=PreconditionStatus.SATISFIED if satisfied else PreconditionStatus.NOT_SATISFIED,
            expected_value=expected_min,
            actual_value=level,
            message=f"Current battery level is {level}% (min required: {expected_min}%)",
        )

    def _check_charging_state(
        self, serial: str, expected: str, **_kwargs
    ) -> PreconditionResult:
        """Verify charging state ('discharging', 'charging', 'any')."""
        expected_clean = expected.strip().lower()
        if expected_clean == "any":
            return PreconditionResult(
                name="charging_state",
                status=PreconditionStatus.SATISFIED,
                expected_value="any",
                actual_value="any",
                message="Any charging state allowed",
            )

        out = self.adb.run_serial_cmd(serial, ["shell", "dumpsys", "battery"], check=False)
        usb_powered = "USB powered: true" in out
        ac_powered = "AC powered: true" in out
        wireless_powered = "Wireless powered: true" in out
        is_charging = usb_powered or ac_powered or wireless_powered

        actual = "charging" if is_charging else "discharging"
        satisfied = (actual == expected_clean)

        return PreconditionResult(
            name="charging_state",
            status=PreconditionStatus.SATISFIED if satisfied else PreconditionStatus.NOT_SATISFIED,
            expected_value=expected_clean,
            actual_value=actual,
            message=f"Device is {actual} (expected: {expected_clean})",
        )

    def _check_thermal_state_max(
        self, serial: str, expected_max: str, **_kwargs
    ) -> PreconditionResult:
        """Verify device thermal state does not exceed maximum acceptable level."""
        # Levels: NONE (0), LIGHT (1), MODERATE (2), SEVERE (3), CRITICAL (4), EMERGENCY (5), SHUTDOWN (6)
        thermal_map = {
            "none": 0,
            "light": 1,
            "moderate": 2,
            "severe": 3,
            "critical": 4,
        }
        max_level = thermal_map.get(expected_max.lower(), 1)

        out = self.adb.run_serial_cmd(serial, ["shell", "dumpsys", "thermalservice"], check=False)
        current_status = 0
        status_name = "NONE"

        for line in out.splitlines():
            line_str = line.strip()
            if "Current Thermal Status:" in line_str or "current thermal status" in line_str.lower():
                try:
                    val_str = line_str.split(":", 1)[1].strip().split()[0]
                    current_status = int(val_str)
                    break
                except Exception:
                    pass

        satisfied = current_status <= max_level
        return PreconditionResult(
            name="thermal_state_max",
            status=PreconditionStatus.SATISFIED if satisfied else PreconditionStatus.NOT_SATISFIED,
            expected_value=expected_max,
            actual_value=current_status,
            message=f"Thermal level is {current_status} (max allowed: {max_level})",
        )

    def _check_app_clean_state(
        self, serial: str, expected: bool, package_name: str = "com.example.iqoo_hexnil", **_kwargs
    ) -> PreconditionResult:
        """Enforce clean app state prior to execution (e.g. force-stop)."""
        if expected:
            self.adb.run_serial_cmd(serial, ["shell", "am", "force-stop", package_name], check=False)

        return PreconditionResult(
            name="app_clean_state",
            status=PreconditionStatus.SATISFIED,
            expected_value=expected,
            actual_value=True,
            message=f"Enforced clean state: force-stopped {package_name}" if expected else "No force-stop requested",
        )
