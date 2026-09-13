"""Unit tests for metadata parsing, property fallback, and health check."""

from unittest.mock import MagicMock
import pytest

from hexnil.device.metadata import MetadataCollector, parse_properties_map
from hexnil.exceptions import DeviceOfflineError


def test_parse_complete_properties():
    props = {
        "ro.product.manufacturer": "Google",
        "ro.product.model": "Pixel 8 Pro",
        "ro.product.device": "husky",
        "ro.build.version.release": "15",
        "ro.build.version.sdk": "35",
        "ro.build.id": "AP2A.240805.005",
        "ro.build.fingerprint": "google/husky/husky:15/AP2A.240805.005/12034873:user/release-keys",
        "ro.product.cpu.abi": "arm64-v8a",
    }
    metadata, warnings = parse_properties_map(props, "SERIAL_PIXEL8")

    assert metadata.serial == "SERIAL_PIXEL8"
    assert metadata.manufacturer == "Google"
    assert metadata.model == "Pixel 8 Pro"
    assert metadata.codename == "husky"
    assert metadata.android_version == "15"
    assert metadata.sdk == 35
    assert metadata.build_id == "AP2A.240805.005"
    assert metadata.build_fingerprint == props["ro.build.fingerprint"]
    assert metadata.abi == "arm64-v8a"
    assert len(warnings) == 0


def test_parse_missing_optional_properties_graceful():
    # Only minimal properties provided
    props = {
        "ro.product.model": "Basic Device",
        "ro.build.version.release": "14",
    }
    metadata, warnings = parse_properties_map(props, "MINIMAL_01")

    assert metadata.serial == "MINIMAL_01"
    assert metadata.model == "Basic Device"
    assert metadata.android_version == "14"
    assert metadata.manufacturer is None
    assert metadata.sdk is None
    assert metadata.build_fingerprint is None
    assert metadata.abi is None

    # Should not raise; warnings should note missing fields
    assert len(warnings) > 0
    assert any("manufacturer" in w for w in warnings)
    assert any("sdk" in w for w in warnings)
    assert any("build_fingerprint" in w for w in warnings)


def test_parse_invalid_sdk_type_handling():
    props = {
        "ro.product.model": "Test",
        "ro.build.version.sdk": "NOT_AN_INT",
    }
    metadata, warnings = parse_properties_map(props, "SERIAL_002")

    assert metadata.sdk is None
    assert any("Invalid integer for SDK" in w for w in warnings)


def test_health_check_success():
    adb_client = MagicMock()
    adb_client.get_state.return_value = "device"

    collector = MetadataCollector(adb_client)
    status = collector.check_health("SERIAL_OK")

    assert status.connected is True
    assert status.state == "device"
    adb_client.get_state.assert_called_once_with("SERIAL_OK")


def test_health_check_failure():
    adb_client = MagicMock()
    adb_client.get_state.return_value = "offline"

    collector = MetadataCollector(adb_client)
    with pytest.raises(DeviceOfflineError) as exc_info:
        collector.check_health("SERIAL_DEAD")

    assert "SERIAL_DEAD" in str(exc_info.value)
    assert "Health check failed" in exc_info.value.suggestion
