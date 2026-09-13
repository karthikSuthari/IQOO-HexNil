"""Hexnil domain exceptions with actionable developer guidance."""

from typing import Optional, List


class HexnilError(Exception):
    """Base exception for all Hexnil errors with actionable suggestions."""

    def __init__(self, message: str, suggestion: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.suggestion = suggestion

    def __str__(self) -> str:
        if self.suggestion:
            return f"{self.message}\nAction required: {self.suggestion}"
        return self.message


class AdbNotFoundError(HexnilError):
    """Raised when the adb executable cannot be found on host machine."""

    def __init__(
        self,
        searched_paths: Optional[List[str]] = None,
        suggestion: Optional[str] = None,
    ):
        paths_str = (
            f" (searched: {', '.join(searched_paths)})" if searched_paths else ""
        )
        msg = f"ADB executable not found{paths_str}."
        default_suggestion = (
            "Install Android SDK Platform-Tools and add 'adb' to your system PATH, "
            "or set the ANDROID_HOME / HEXNIL_ADB_PATH environment variable, "
            "or ensure local.properties specifies sdk.dir."
        )
        super().__init__(msg, suggestion or default_suggestion)


class NoDevicesConnectedError(HexnilError):
    """Raised when no Android devices are detected via ADB."""

    def __init__(self, suggestion: Optional[str] = None):
        msg = "No Android devices connected or detected via ADB."
        default_suggestion = (
            "Connect an Android device via USB, ensure USB cable supports data transfer, "
            "enable Developer Options on the device, and turn on 'USB Debugging'. "
            "Run 'adb devices' to confirm detection."
        )
        super().__init__(msg, suggestion or default_suggestion)


class DeviceUnauthorizedError(HexnilError):
    """Raised when the connected Android device is in 'unauthorized' state."""

    def __init__(self, serial: str, suggestion: Optional[str] = None):
        msg = f"Device '{serial}' is unauthorized."
        default_suggestion = (
            f"Check the screen of device '{serial}'. Unlock the device and tap "
            "'Allow USB debugging' (select 'Always allow from this computer'). "
            "If the prompt does not appear, try: adb reconnect or revoking USB authorizations in Developer Options."
        )
        super().__init__(msg, suggestion or default_suggestion)


class DeviceOfflineError(HexnilError):
    """Raised when the connected Android device is in 'offline' state."""

    def __init__(self, serial: str, suggestion: Optional[str] = None):
        msg = f"Device '{serial}' is offline."
        default_suggestion = (
            f"Device '{serial}' is not communicating. Try unplugging and replugging the USB cable, "
            "or run: adb reconnect offline, or toggle USB Debugging off and on in Developer Options."
        )
        super().__init__(msg, suggestion or default_suggestion)


class MultipleDevicesError(HexnilError):
    """Raised when multiple devices exist and no explicit serial was specified."""

    def __init__(self, available_serials: List[str], suggestion: Optional[str] = None):
        msg = (
            f"Multiple devices connected ({len(available_serials)} found: {', '.join(available_serials)}). "
            "Hexnil requires an explicit target serial to avoid accidental operations."
        )
        default_suggestion = (
            f"Select a device explicitly by running:\n"
            f"  python -m hexnil device status --serial <SERIAL>\n"
            f"Available serials: {', '.join(available_serials)}"
        )
        super().__init__(msg, suggestion or default_suggestion)
        self.available_serials = available_serials


class DeviceNotFoundError(HexnilError):
    """Raised when a specified serial is not found in adb devices."""

    def __init__(
        self,
        serial: str,
        available_serials: List[str],
        suggestion: Optional[str] = None,
    ):
        msg = f"Target device with serial '{serial}' was not found."
        serials_str = (
            ", ".join(available_serials) if available_serials else "None connected"
        )
        default_suggestion = (
            f"Verify the serial number. Currently detected devices: [{serials_str}]. "
            "Run 'python -m hexnil device list' to see all active devices."
        )
        super().__init__(msg, suggestion or default_suggestion)
        self.serial = serial
        self.available_serials = available_serials


class AdbCommandTimeoutError(HexnilError):
    """Raised when an ADB command times out."""

    def __init__(
        self,
        command: List[str],
        timeout_seconds: float,
        suggestion: Optional[str] = None,
    ):
        msg = f"ADB command timed out after {timeout_seconds}s: {' '.join(command)}"
        default_suggestion = (
            "The device might be unresponsive or USB connection unstable. "
            "Check cable, restart ADB server ('adb kill-server && adb start-server'), "
            "or reconnect the device."
        )
        super().__init__(msg, suggestion or default_suggestion)


class AdbExecutionError(HexnilError):
    """Raised when an ADB command fails with non-zero exit code or stderr."""

    def __init__(
        self,
        command: List[str],
        returncode: int,
        stderr: str,
        stdout: str = "",
        suggestion: Optional[str] = None,
    ):
        cmd_str = " ".join(command)
        msg = f"ADB command failed (exit code {returncode}): {cmd_str}\nError output: {stderr.strip()}"
        default_suggestion = (
            "Ensure ADB server is running and the device is authorized and accessible."
        )
        super().__init__(msg, suggestion or default_suggestion)
        self.command = command
        self.returncode = returncode
        self.stderr = stderr
        self.stdout = stdout


class MalformedAdbOutputError(HexnilError):
    """Raised when ADB returns unparseable or corrupted output."""

    def __init__(self, raw_output: str, suggestion: Optional[str] = None):
        msg = f"Failed to parse ADB output: {raw_output[:200]!r}"
        default_suggestion = (
            "Verify your Android Platform-Tools version. Try running 'adb devices -l' manually "
            "to check if ADB output conforms to standard format."
        )
        super().__init__(msg, suggestion or default_suggestion)


class ExperimentPersistenceError(HexnilError):
    """Raised when local experiment metadata cannot be written or read."""

    def __init__(self, path: str, reason: str, suggestion: Optional[str] = None):
        msg = f"Failed to persist or load experiment record at '{path}': {reason}"
        default_suggestion = (
            f"Check disk write permissions and ensure directory '{path}' is accessible."
        )
        super().__init__(msg, suggestion or default_suggestion)
