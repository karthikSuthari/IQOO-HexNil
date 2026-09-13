"""Unit tests for safe ADB client subprocess runner and serial validation."""

import subprocess
from unittest.mock import MagicMock, patch
import pytest

from hexnil.device.adb import AdbClient, validate_serial
from hexnil.exceptions import (
    AdbCommandTimeoutError,
    AdbExecutionError,
    AdbNotFoundError,
)


def test_validate_serial_valid_inputs():
    valid_serials = [
        "1234567890ABCDEF",
        "emulator-5554",
        "192.168.1.50:5555",
        "device_01",
        "a.b-c_d:1234",
    ]
    for s in valid_serials:
        assert validate_serial(s) == s


def test_validate_serial_invalid_inputs():
    invalid_serials = [
        "",
        "   ",
        "serial with spaces",
        "serial; rm -rf /",
        "device && echo pwned",
        "dev|cat",
        "dev`whoami`",
        "dev$(id)",
    ]
    for s in invalid_serials:
        with pytest.raises(ValueError) as exc_info:
            validate_serial(s)
        assert "Invalid ADB serial" in str(exc_info.value)


def test_adb_client_missing_binary():
    with patch("hexnil.device.adb.find_adb_executable", return_value=None):
        client = AdbClient(adb_path=None)
        with pytest.raises(AdbNotFoundError):
            client.ensure_executable()


def test_adb_client_run_cmd_success():
    client = AdbClient(adb_path="/mock/adb")
    mock_res = MagicMock(returncode=0, stdout="device attached\n", stderr="")

    with patch("subprocess.run", return_value=mock_res) as mock_run:
        out = client.run_cmd(["devices"])
        assert out == "device attached\n"
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert cmd == ["/mock/adb", "devices"]


def test_adb_client_run_cmd_timeout():
    client = AdbClient(adb_path="/mock/adb", default_timeout=5.0)

    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd=["/mock/adb"], timeout=5.0)):
        with pytest.raises(AdbCommandTimeoutError) as exc_info:
            client.run_cmd(["shell", "sleep", "10"])
        assert "timed out after 5.0s" in str(exc_info.value)


def test_adb_client_run_cmd_failure():
    client = AdbClient(adb_path="/mock/adb")
    mock_res = MagicMock(returncode=1, stdout="", stderr="error: device not found")

    with patch("subprocess.run", return_value=mock_res):
        with pytest.raises(AdbExecutionError) as exc_info:
            client.run_cmd(["get-state"], check=True)
        assert "ADB command failed" in str(exc_info.value)
        assert exc_info.value.returncode == 1


def test_adb_client_run_serial_cmd():
    client = AdbClient(adb_path="/mock/adb")
    mock_res = MagicMock(returncode=0, stdout="device\n", stderr="")

    with patch("subprocess.run", return_value=mock_res) as mock_run:
        out = client.run_serial_cmd("SERIAL_01", ["get-state"])
        assert out == "device\n"
        cmd = mock_run.call_args[0][0]
        assert cmd == ["/mock/adb", "-s", "SERIAL_01", "get-state"]


def test_adb_client_get_all_props_parsing():
    client = AdbClient(adb_path="/mock/adb")
    sample_getprop = """
[ro.product.model]: [Pixel 8]
[ro.build.version.release]: [14]
[ro.product.manufacturer]: [Google]
"""
    with patch.object(client, "run_serial_cmd", return_value=sample_getprop):
        props = client.get_all_props("SERIAL_01")
        assert props["ro.product.model"] == "Pixel 8"
        assert props["ro.build.version.release"] == "14"
        assert props["ro.product.manufacturer"] == "Google"
