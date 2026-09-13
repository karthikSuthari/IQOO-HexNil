"""Environment snapshot capture for baseline experiments."""

import datetime
import logging
from typing import Dict, Optional

from hexnil.baseline.models import EnvironmentConditionStatus, EnvironmentSnapshot
from hexnil.device.adb import AdbClient

logger = logging.getLogger("hexnil.baseline.environment")


def capture_environment_snapshot(
    adb: AdbClient,
    serial: str,
    package_name: str = "com.example.iqoo_hexnil",
) -> EnvironmentSnapshot:
    """Capture comprehensive environmental conditions influencing measurements."""
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    status_map: Dict[str, EnvironmentConditionStatus] = {}

    # 1. Battery state
    battery_level: Optional[float] = None
    charging_state: Optional[str] = None
    battery_temp_c: Optional[float] = None

    bat_out = adb.run_serial_cmd(serial, ["shell", "dumpsys", "battery"], check=False)
    if bat_out:
        for line in bat_out.splitlines():
            line_s = line.strip()
            if line_s.startswith("level:"):
                try:
                    battery_level = float(line_s.split(":", 1)[1].strip())
                except ValueError:
                    pass
            elif line_s.startswith("temperature:"):
                try:
                    raw_temp = float(line_s.split(":", 1)[1].strip())
                    battery_temp_c = round(raw_temp / 10.0, 1)
                except ValueError:
                    pass

        usb_powered = "USB powered: true" in bat_out
        ac_powered = "AC powered: true" in bat_out
        wireless_powered = "Wireless powered: true" in bat_out
        charging_state = "charging" if (usb_powered or ac_powered or wireless_powered) else "discharging"

        status_map["battery_level_percent"] = EnvironmentConditionStatus.MEASURED
        status_map["battery_charging_state"] = EnvironmentConditionStatus.MEASURED
        if battery_temp_c is not None:
            status_map["battery_temperature_c"] = EnvironmentConditionStatus.MEASURED
        else:
            status_map["battery_temperature_c"] = EnvironmentConditionStatus.UNSUPPORTED
    else:
        status_map["battery_level_percent"] = EnvironmentConditionStatus.UNSUPPORTED
        status_map["battery_charging_state"] = EnvironmentConditionStatus.UNSUPPORTED
        status_map["battery_temperature_c"] = EnvironmentConditionStatus.UNSUPPORTED

    # 2. Screen state
    screen_on: Optional[bool] = None
    power_out = adb.run_serial_cmd(serial, ["shell", "dumpsys", "power"], check=False)
    if power_out:
        screen_on = "Display Power: state=ON" in power_out or "mWakefulness=Awake" in power_out
        status_map["screen_on"] = EnvironmentConditionStatus.VERIFIED
    else:
        status_map["screen_on"] = EnvironmentConditionStatus.UNSUPPORTED

    # Screen brightness
    screen_brightness: Optional[int] = None
    bright_out = adb.run_serial_cmd(serial, ["shell", "settings", "get", "system", "screen_brightness"], check=False).strip()
    try:
        screen_brightness = int(bright_out)
        status_map["screen_brightness"] = EnvironmentConditionStatus.MEASURED
    except ValueError:
        status_map["screen_brightness"] = EnvironmentConditionStatus.UNSUPPORTED

    # 3. Thermal status
    thermal_status: Optional[str] = None
    thermal_out = adb.run_serial_cmd(serial, ["shell", "dumpsys", "thermalservice"], check=False)
    if thermal_out:
        thermal_map = {
            "0": "NONE",
            "1": "LIGHT",
            "2": "MODERATE",
            "3": "SEVERE",
            "4": "CRITICAL",
            "5": "EMERGENCY",
            "6": "SHUTDOWN",
        }
        for line in thermal_out.splitlines():
            line_s = line.strip()
            if "current thermal status" in line_s.lower():
                try:
                    code_str = line_s.split(":", 1)[1].strip().split()[0]
                    thermal_status = thermal_map.get(code_str, f"CODE_{code_str}")
                    break
                except Exception:
                    pass
        if thermal_status is not None:
            status_map["thermal_status"] = EnvironmentConditionStatus.MEASURED
        else:
            status_map["thermal_status"] = EnvironmentConditionStatus.UNSUPPORTED
    else:
        status_map["thermal_status"] = EnvironmentConditionStatus.UNSUPPORTED

    # 4. Network / Wi-Fi
    wifi_enabled: Optional[bool] = None
    wifi_connected: Optional[bool] = None
    wifi_out = adb.run_serial_cmd(serial, ["shell", "dumpsys", "wifi"], check=False)
    if wifi_out:
        wifi_enabled = "Wi-Fi is enabled" in wifi_out
        wifi_connected = "Supplicant state: COMPLETED" in wifi_out
        status_map["wifi_enabled"] = EnvironmentConditionStatus.MEASURED
        status_map["wifi_connected"] = EnvironmentConditionStatus.MEASURED
    else:
        status_map["wifi_enabled"] = EnvironmentConditionStatus.UNSUPPORTED
        status_map["wifi_connected"] = EnvironmentConditionStatus.UNSUPPORTED

    # 5. Device idle state (Doze)
    device_idle_state: Optional[str] = None
    idle_out = adb.run_serial_cmd(serial, ["shell", "dumpsys", "deviceidle"], check=False)
    if idle_out:
        for line in idle_out.splitlines():
            line_s = line.strip()
            if "mState=" in line_s:
                device_idle_state = line_s
                break
        if device_idle_state:
            status_map["device_idle_state"] = EnvironmentConditionStatus.MEASURED
        else:
            status_map["device_idle_state"] = EnvironmentConditionStatus.UNSUPPORTED
    else:
        status_map["device_idle_state"] = EnvironmentConditionStatus.UNSUPPORTED

    # 6. Orientation
    orientation: Optional[str] = None
    window_out = adb.run_serial_cmd(serial, ["shell", "dumpsys", "window", "displays"], check=False)
    if window_out:
        for line in window_out.splitlines():
            line_s = line.strip()
            if "mCurrentOrientation=" in line_s or "init=" in line_s and "cur=" in line_s:
                orientation = line_s
                break
        status_map["orientation"] = EnvironmentConditionStatus.MEASURED if orientation else EnvironmentConditionStatus.UNSUPPORTED
    else:
        status_map["orientation"] = EnvironmentConditionStatus.UNSUPPORTED

    # 7. App process running
    app_running: Optional[bool] = None
    pid_out = adb.run_serial_cmd(serial, ["shell", "pidof", package_name], check=False).strip()
    app_running = bool(pid_out and pid_out.isdigit())
    status_map["app_running"] = EnvironmentConditionStatus.VERIFIED

    return EnvironmentSnapshot(
        timestamp=now_iso,
        battery_level_percent=battery_level,
        battery_charging_state=charging_state,
        battery_temperature_c=battery_temp_c,
        screen_on=screen_on,
        screen_brightness=screen_brightness,
        thermal_status=thermal_status,
        wifi_enabled=wifi_enabled,
        wifi_connected=wifi_connected,
        device_idle_state=device_idle_state,
        orientation=orientation,
        app_running=app_running,
        condition_status=status_map,
    )
