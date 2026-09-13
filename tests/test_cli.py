"""Unit and integration tests for Hexnil CLI interface."""

import json
from unittest.mock import MagicMock, patch
from pathlib import Path
import pytest

from hexnil.cli import create_parser, format_human_status, main
from hexnil.device.models import AdbStatus, DeviceMetadata, DiscoveredDevice, DeviceState, ExperimentRecord
from hexnil.exceptions import NoDevicesConnectedError, MultipleDevicesError
from hexnil.experiments.store import ExperimentStore


def test_format_human_status():
    metadata = DeviceMetadata(
        serial="R5CN30XXXXX",
        manufacturer="Samsung",
        model="Galaxy S21",
        android_version="15",
        sdk=35,
        build_id="UP1A.231005.007",
        build_fingerprint="samsung/o1s/o1s:15/UP1A.231005.007/G991BXXU9FWK4:user/release-keys",
    )
    record = ExperimentRecord(
        experiment_id="EXP-20260913-001",
        created_at="2026-09-13T12:00:00Z",
        device=metadata,
        adb=AdbStatus(state="device", connected=True),
        warnings=["Optional warning"],
    )

    output = format_human_status(record)
    assert "Hexnil Device Foundation" in output
    assert "Status: CONNECTED" in output
    assert "Device: Samsung Galaxy S21" in output
    assert "Android: 15" in output
    assert "SDK: 35" in output
    assert "ADB serial: R5CN30XXXXX" in output
    assert "Experiment ID: EXP-20260913-001" in output
    assert "Warnings:" in output
    assert "- Optional warning" in output


def test_cli_parser_defaults():
    parser = create_parser()
    args = parser.parse_args(["device", "status"])
    assert args.command == "device"
    assert args.subcommand == "status"
    assert args.serial is None
    assert args.json is False


def test_cli_device_status_flow(tmp_path: Path, capsys):
    mock_dev = DiscoveredDevice(serial="MOCK_001", state=DeviceState.DEVICE)
    mock_meta = DeviceMetadata(
        serial="MOCK_001",
        manufacturer="Google",
        model="Pixel 8",
        android_version="14",
        sdk=34,
        build_id="UQ1A.240205.004",
        build_fingerprint="google/shiba/shiba:14/UQ1A.240205.004/11265147:user/release-keys",
    )
    mock_status = AdbStatus(state="device", connected=True)

    with patch("hexnil.cli.DeviceDiscovery.select_device", return_value=mock_dev), \
         patch("hexnil.cli.MetadataCollector.collect", return_value=(mock_meta, mock_status, [])):

        ret = main(["--data-dir", str(tmp_path), "device", "status"])
        assert ret == 0

        captured = capsys.readouterr()
        assert "Hexnil Device Foundation" in captured.out
        assert "Device: Google Pixel 8" in captured.out
        assert "EXP-" in captured.out

        # Verify record was written to tmp_path
        json_files = list(tmp_path.glob("EXP-*.json"))
        assert len(json_files) == 1


def test_cli_device_status_json_flag(tmp_path: Path, capsys):
    mock_dev = DiscoveredDevice(serial="MOCK_001", state=DeviceState.DEVICE)
    mock_meta = DeviceMetadata(
        serial="MOCK_001",
        manufacturer="Google",
        model="Pixel 8",
        android_version="14",
        sdk=34,
        build_id="UQ1A.240205.004",
        build_fingerprint="fingerprint_test",
    )
    mock_status = AdbStatus(state="device", connected=True)

    with patch("hexnil.cli.DeviceDiscovery.select_device", return_value=mock_dev), \
         patch("hexnil.cli.MetadataCollector.collect", return_value=(mock_meta, mock_status, [])):

        ret = main(["--data-dir", str(tmp_path), "device", "status", "--json"])
        assert ret == 0

        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert parsed["device"]["serial"] == "MOCK_001"
        assert parsed["device"]["manufacturer"] == "Google"
        assert parsed["device"]["sdk"] == 34
        assert parsed["adb"]["connected"] is True
        assert parsed["phase"] == "01_android_device_foundation"


def test_cli_error_handling_no_devices(capsys):
    with patch("hexnil.cli.DeviceDiscovery.select_device", side_effect=NoDevicesConnectedError()):
        ret = main(["device", "status"])
        assert ret == 1

        captured = capsys.readouterr()
        assert "[ERROR] No Android devices connected" in captured.err
        assert "Action required:" in captured.err
        assert "USB Debugging" in captured.err


def test_cli_error_handling_json(capsys):
    with patch("hexnil.cli.DeviceDiscovery.select_device", side_effect=NoDevicesConnectedError()):
        ret = main(["device", "status", "--json"])
        assert ret == 1

        captured = capsys.readouterr()
        err_json = json.loads(captured.err)
        assert err_json["error"] is True
        assert err_json["type"] == "NoDevicesConnectedError"
        assert "USB Debugging" in err_json["suggestion"]


def test_cli_device_list(capsys):
    devices = [
        DiscoveredDevice(serial="DEV_1", state=DeviceState.DEVICE, model="Pixel_7"),
        DiscoveredDevice(serial="DEV_2", state=DeviceState.UNAUTHORIZED),
    ]
    with patch("hexnil.cli.DeviceDiscovery.list_devices", return_value=devices):
        ret = main(["device", "list"])
        assert ret == 0

        captured = capsys.readouterr()
        assert "DEV_1" in captured.out
        assert "[USABLE]" in captured.out
        assert "DEV_2" in captured.out
        assert "[UNAUTHORIZED]" in captured.out


def test_cli_device_list_json(capsys):
    devices = [
        DiscoveredDevice(serial="DEV_1", state=DeviceState.DEVICE, model="Pixel_7"),
    ]
    with patch("hexnil.cli.DeviceDiscovery.list_devices", return_value=devices):
        ret = main(["device", "list", "--json"])
        assert ret == 0

        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert len(parsed) == 1
        assert parsed[0]["serial"] == "DEV_1"


def test_cli_experiment_list_and_show(tmp_path: Path, capsys):
    store = ExperimentStore(tmp_path)
    rec = ExperimentRecord(
        experiment_id="EXP-20260913-001",
        created_at="2026-09-13T12:00:00Z",
        device=DeviceMetadata(serial="DEV_1", manufacturer="Google", model="Pixel 7"),
        adb=AdbStatus(state="device", connected=True),
    )
    store.save(rec)

    # Test experiment list
    ret = main(["--data-dir", str(tmp_path), "experiment", "list"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "EXP-20260913-001" in captured.out

    # Test experiment show
    ret = main(["--data-dir", str(tmp_path), "experiment", "show", "EXP-20260913-001"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "Hexnil Device Foundation" in captured.out
    assert "EXP-20260913-001" in captured.out

    # Test experiment show --json
    ret = main(["--data-dir", str(tmp_path), "experiment", "show", "EXP-20260913-001", "--json"])
    assert ret == 0
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert parsed["experiment_id"] == "EXP-20260913-001"
