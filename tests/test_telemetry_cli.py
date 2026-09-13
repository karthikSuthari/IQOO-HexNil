"""Tests for Hexnil Telemetry CLI subcommands and formatting."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from hexnil.cli import create_parser, main
from hexnil.device.models import AdbStatus, DeviceMetadata, DiscoveredDevice, DeviceState, ExperimentRecord
from hexnil.experiments.store import ExperimentStore
from hexnil.telemetry.models import CapabilityStatus, MetricValue, TelemetryRecord, WorkloadIdentity


def test_telemetry_parser_args():
    parser = create_parser()
    
    # test 'telemetry collect'
    args = parser.parse_args(["telemetry", "collect", "--serial", "DEVICE_123", "--workload", "startup_basic"])
    assert args.command == "telemetry"
    assert args.subcommand == "collect"
    assert args.serial == "DEVICE_123"
    assert args.workload_id == "startup_basic"

    # test 'telemetry show'
    args = parser.parse_args(["telemetry", "show", "EXP-20260913-001", "--json"])
    assert args.command == "telemetry"
    assert args.subcommand == "show"
    assert args.experiment_id == "EXP-20260913-001"
    assert args.json is True


def test_telemetry_show_command_output(tmp_path: Path, capsys):
    store = ExperimentStore(tmp_path)
    exp_id = "EXP-20260913-001"
    
    device_meta = DeviceMetadata(
        serial="SERIAL_123",
        manufacturer="vivo",
        model="vivo I2302",
        android_version="16",
        sdk=36,
    )
    rec = ExperimentRecord(
        experiment_id=exp_id,
        created_at="2026-09-13T12:00:00Z",
        device=device_meta,
        adb=AdbStatus(state="device", connected=True),
    )
    store.save(rec)

    records = [
        TelemetryRecord(
            experiment_id=exp_id,
            timestamp="2026-09-13T12:00:01Z",
            device=device_meta,
            source="android_app",
            capability=CapabilityStatus.UNIVERSAL,
            metric=MetricValue(name="battery_level", value=82.0, unit="percent"),
        ),
        TelemetryRecord(
            experiment_id=exp_id,
            timestamp="2026-09-13T12:00:02Z",
            device=device_meta,
            source="android_app",
            capability=CapabilityStatus.UNSUPPORTED,
            metric=MetricValue(name="thermal_headroom", value=None, unit=None),
            reason="Thermal headroom unsupported on this API",
        ),
    ]
    store.append_telemetry(exp_id, records, filename="android.jsonl")

    # Call with --data-dir
    ret = main(["--data-dir", str(tmp_path), "telemetry", "show", exp_id])
    assert ret == 0

    captured = capsys.readouterr().out
    assert exp_id in captured
    assert "battery_level" in captured
    assert "82.0" in captured
    assert "thermal_headroom" in captured
    assert "UNSUPPORTED" in captured

    # Also test JSON output
    ret_json = main(["--data-dir", str(tmp_path), "telemetry", "show", exp_id, "--json"])
    assert ret_json == 0
    captured_json = capsys.readouterr().out
    data = json.loads(captured_json)
    assert len(data) == 2
    assert data[0]["metric"]["name"] == "battery_level"


def test_telemetry_collect_mocked(tmp_path: Path, capsys):
    mock_dev = DiscoveredDevice(serial="SERIAL_123", state=DeviceState.DEVICE)
    mock_meta = DeviceMetadata(
        serial="SERIAL_123",
        manufacturer="vivo",
        model="vivo I2302",
        android_version="16",
        sdk=36,
    )
    mock_status = AdbStatus(state="device", connected=True)

    from hexnil.telemetry.bridge import TelemetrySummary
    summary_obj = TelemetrySummary(
        experiment_id="EXP-20260913-099",
        device_model="vivo vivo I2302",
        device_serial="SERIAL_123",
        android_version="16",
        total_records=13,
        universal_count=10,
        conditional_count=2,
        unsupported_count=1,
        artifacts=["logcat.txt", "dumpsys_meminfo.txt"],
    )

    rec_mock = TelemetryRecord(
        experiment_id="EXP-20260913-099",
        timestamp="2026-09-13T12:00:01Z",
        device=mock_meta,
        source="android_app",
        capability=CapabilityStatus.UNIVERSAL,
        metric=MetricValue(name="battery_level", value=80.0, unit="percent"),
    )

    with patch("hexnil.cli.DeviceDiscovery.select_device", return_value=mock_dev), \
         patch("hexnil.cli.MetadataCollector.collect", return_value=(mock_meta, mock_status, [])), \
         patch("hexnil.cli.TelemetryBridge.collect_all", return_value=([rec_mock], [rec_mock], summary_obj)):

        ret = main(["--data-dir", str(tmp_path), "telemetry", "collect", "--serial", "SERIAL_123"])
        assert ret == 0
        captured = capsys.readouterr().out
        assert "Hexnil Telemetry Collection" in captured
        assert "Device: vivo vivo I2302" in captured
        assert "Telemetry records: 13" in captured
        assert "Unsupported: 1" in captured
