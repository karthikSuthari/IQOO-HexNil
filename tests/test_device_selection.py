"""Unit tests for device selection logic and multi-device policies."""

from unittest.mock import MagicMock
import pytest

from hexnil.device.discovery import DeviceDiscovery
from hexnil.device.models import DeviceState, DiscoveredDevice
from hexnil.exceptions import (
    DeviceNotFoundError,
    DeviceOfflineError,
    DeviceUnauthorizedError,
    MultipleDevicesError,
    NoDevicesConnectedError,
)


def make_mock_discovery(devices):
    client = MagicMock()
    discovery = DeviceDiscovery(adb_client=client)
    discovery.list_devices = MagicMock(return_value=devices)
    return discovery


def test_select_single_device_auto():
    device = DiscoveredDevice(
        serial="SERIAL_001",
        state=DeviceState.DEVICE,
        model="Pixel_8",
    )
    discovery = make_mock_discovery([device])

    selected = discovery.select_device()
    assert selected.serial == "SERIAL_001"
    assert selected.is_usable is True


def test_select_no_devices_raises():
    discovery = make_mock_discovery([])
    with pytest.raises(NoDevicesConnectedError) as exc_info:
        discovery.select_device()
    assert "No Android devices connected" in str(exc_info.value)
    assert exc_info.value.suggestion is not None


def test_select_multiple_devices_without_serial_raises():
    dev1 = DiscoveredDevice(serial="DEV_001", state=DeviceState.DEVICE)
    dev2 = DiscoveredDevice(serial="DEV_002", state=DeviceState.DEVICE)
    discovery = make_mock_discovery([dev1, dev2])

    with pytest.raises(MultipleDevicesError) as exc_info:
        discovery.select_device()

    assert "Multiple devices connected" in str(exc_info.value)
    assert "DEV_001" in exc_info.value.available_serials
    assert "DEV_002" in exc_info.value.available_serials
    assert "--serial <SERIAL>" in exc_info.value.suggestion


def test_select_explicit_target_serial():
    dev1 = DiscoveredDevice(serial="DEV_001", state=DeviceState.DEVICE)
    dev2 = DiscoveredDevice(serial="DEV_002", state=DeviceState.DEVICE)
    discovery = make_mock_discovery([dev1, dev2])

    selected = discovery.select_device(target_serial="DEV_002")
    assert selected.serial == "DEV_002"


def test_select_explicit_serial_not_found():
    dev1 = DiscoveredDevice(serial="DEV_001", state=DeviceState.DEVICE)
    discovery = make_mock_discovery([dev1])

    with pytest.raises(DeviceNotFoundError) as exc_info:
        discovery.select_device(target_serial="NON_EXISTENT")

    assert "NON_EXISTENT" in str(exc_info.value)
    assert "DEV_001" in exc_info.value.available_serials


def test_select_unauthorized_device_explicit():
    dev = DiscoveredDevice(serial="DEV_UNAUTH", state=DeviceState.UNAUTHORIZED)
    discovery = make_mock_discovery([dev])

    with pytest.raises(DeviceUnauthorizedError) as exc_info:
        discovery.select_device(target_serial="DEV_UNAUTH")

    assert "DEV_UNAUTH" in str(exc_info.value)
    assert "Allow USB debugging" in exc_info.value.suggestion


def test_select_unauthorized_device_implicit():
    dev = DiscoveredDevice(serial="DEV_UNAUTH", state=DeviceState.UNAUTHORIZED)
    discovery = make_mock_discovery([dev])

    with pytest.raises(DeviceUnauthorizedError) as exc_info:
        discovery.select_device()

    assert "DEV_UNAUTH" in str(exc_info.value)


def test_select_offline_device():
    dev = DiscoveredDevice(serial="DEV_OFFLINE", state=DeviceState.OFFLINE)
    discovery = make_mock_discovery([dev])

    with pytest.raises(DeviceOfflineError) as exc_info:
        discovery.select_device(target_serial="DEV_OFFLINE")

    assert "DEV_OFFLINE" in str(exc_info.value)
    assert "offline" in exc_info.value.suggestion.lower()
