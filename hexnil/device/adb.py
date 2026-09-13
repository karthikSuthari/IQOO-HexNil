"""Safe ADB subprocess wrapper and command runner."""

import logging
import re
import subprocess
from typing import Dict, List, Optional

from hexnil.config import HexnilConfig, find_adb_executable
from hexnil.exceptions import (
    AdbCommandTimeoutError,
    AdbExecutionError,
    AdbNotFoundError,
)

logger = logging.getLogger("hexnil.adb")

# Standard serial pattern (USB serials or IP:PORT network serials)
SERIAL_PATTERN = re.compile(r"^[a-zA-Z0-9_\.\-:]+$")


def validate_serial(serial: str) -> str:
    """Validate that the device serial string contains only safe characters."""
    cleaned = serial.strip()
    if not cleaned or not SERIAL_PATTERN.match(cleaned):
        raise ValueError(
            f"Invalid ADB serial '{serial}'. Serial numbers must be alphanumeric with optional "
            "periods, hyphens, underscores, or colons (e.g. 192.168.1.10:5555)."
        )
    return cleaned


class AdbClient:
    """Encapsulates safe communication with the host's ADB binary."""

    def __init__(
        self,
        adb_path: Optional[str] = None,
        default_timeout: float = 10.0,
    ):
        self.adb_path = adb_path or find_adb_executable()
        self.default_timeout = default_timeout

    def ensure_executable(self) -> str:
        """Verify that the ADB binary is located and executable."""
        if not self.adb_path:
            self.adb_path = find_adb_executable()
        if not self.adb_path:
            raise AdbNotFoundError()
        return self.adb_path

    def run_cmd(
        self,
        args: List[str],
        timeout: Optional[float] = None,
        check: bool = True,
    ) -> str:
        """Run an ADB command with argument array (never shell=True).

        Args:
            args: Command arguments after 'adb', e.g. ['devices', '-l']
            timeout: Maximum execution time in seconds
            check: Whether to raise AdbExecutionError on non-zero exit code
        """
        adb_bin = self.ensure_executable()
        cmd = [adb_bin, *args]
        eff_timeout = timeout if timeout is not None else self.default_timeout

        logger.debug("Executing ADB command: %s", " ".join(cmd))

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=eff_timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise AdbCommandTimeoutError(cmd, eff_timeout) from exc
        except FileNotFoundError as exc:
            raise AdbNotFoundError(suggestion=str(exc)) from exc

        if check and result.returncode != 0:
            raise AdbExecutionError(
                command=cmd,
                returncode=result.returncode,
                stderr=result.stderr,
                stdout=result.stdout,
            )

        return result.stdout

    def run_serial_cmd(
        self,
        serial: str,
        args: List[str],
        timeout: Optional[float] = None,
        check: bool = True,
    ) -> str:
        """Run an ADB command strictly targeted to a specific serial (-s <serial>)."""
        valid_serial = validate_serial(serial)
        serial_args = ["-s", valid_serial, *args]
        return self.run_cmd(serial_args, timeout=timeout, check=check)

    def get_state(self, serial: str) -> str:
        """Run 'adb -s <serial> get-state' to verify device communication."""
        output = self.run_serial_cmd(serial, ["get-state"])
        return output.strip()

    def get_prop(self, serial: str, prop_name: str) -> Optional[str]:
        """Fetch a single system property using 'adb -s <serial> shell getprop <prop>'."""
        output = self.run_serial_cmd(serial, ["shell", "getprop", prop_name], check=False)
        val = output.strip()
        return val if val else None

    def get_all_props(self, serial: str) -> Dict[str, str]:
        """Fetch all system properties in a single batch call to minimize latency.

        Parses lines formatted as: [key]: [value]
        """
        props: Dict[str, str] = {}
        try:
            output = self.run_serial_cmd(serial, ["shell", "getprop"], timeout=15.0)
            pattern = re.compile(r"^\[([^\]]+)\]:\s*\[([^\]]*)\]$")
            for line in output.splitlines():
                match = pattern.match(line.strip())
                if match:
                    props[match.group(1)] = match.group(2)
        except Exception as exc:
            logger.warning("Batch getprop failed for device %s: %s", serial, exc)
        return props
