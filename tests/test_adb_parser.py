"""Unit tests for ADB devices output parsing."""

import pytest
from hexnil.device.discovery import parse_adb_devices_output
from hexnil.device.models import DeviceState


def test_parse_empty_devices():
    raw = """List of devices attached\n\n"""
    devices = parse_adb_devices_output(raw)
    assert len(devices) == 0


def test_parse_with_daemon_messages():
    raw = """* daemon not running; starting now at tcp:5037
* daemon started successfully
List of devices attached
1234567890ABCDEF\tdevice product:raven model:Pixel_6_Pro device:raven transport_id:1
"""
    devices = parse_adb_devices_output(raw)
    assert len(devices) == 1
    d = devices[0]
    assert d.serial == "1234567890ABCDEF"
    assert d.state == DeviceState.DEVICE
    assert d.product == "raven"
    assert d.model == "Pixel_6_Pro"
    assert d.device == "raven"
    assert d.transport_id == "1"
    assert d.is_usable is True


def test_parse_multiple_devices_and_states():
    raw = """List of devices attached
emulator-5554          device product:sdk_gphone64_arm64 model:sdk_gphone64_arm64 device:emu64a transport_id:1
RF8M10XXXXX            unauthorized transport_id:2
192.168.1.15:5555      offline transport_id:3
TEST_RECOVERY_01       recovery transport_id:4
"""
    devices = parse_adb_devices_output(raw)
    assert len(devices) == 4

    assert devices[0].serial == "emulator-5554"
    assert devices[0].state == DeviceState.DEVICE
    assert devices[0].is_usable is True

    assert devices[1].serial == "RF8M10XXXXX"
    assert devices[1].state == DeviceState.UNAUTHORIZED
    assert devices[1].is_usable is False

    assert devices[2].serial == "192.168.1.15:5555"
    assert devices[2].state == DeviceState.OFFLINE
    assert devices[2].is_usable is False

    assert devices[3].serial == "TEST_RECOVERY_01"
    assert devices[3].state == DeviceState.RECOVERY
    assert devices[3].is_usable is False


def test_parse_standard_non_verbose_output():
    raw = """List of devices attached
R5CN30XXXXX\tdevice
"""
    devices = parse_adb_devices_output(raw)
    assert len(devices) == 1
    assert devices[0].serial == "R5CN30XXXXX"
    assert devices[0].state == DeviceState.DEVICE
    assert devices[0].model is None
    assert devices[0].product is None


def test_parse_malformed_and_unknown_states():
    raw = """List of devices attached
some_weird_line_without_state
VALID_SERIAL_001  custom_state_foo
"""
    devices = parse_adb_devices_output(raw)
    assert len(devices) == 1
    assert devices[0].serial == "VALID_SERIAL_001"
    assert devices[0].state == DeviceState.UNKNOWN
