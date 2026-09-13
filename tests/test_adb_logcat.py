"""Unit tests for ADB bounded logcat collection."""

from pathlib import Path
from unittest.mock import MagicMock
import pytest
from hexnil.device.models import DeviceMetadata
from hexnil.telemetry.adb_collectors import AdbLogcatCollector
from hexnil.telemetry.models import CapabilityStatus, SoftwareIdentity, WorkloadIdentity


def test_logcat_collector_success(tmp_path: Path):
    mock_adb = MagicMock()
    mock_adb.run_serial_cmd.return_value = "line 1\nline 2\nline 3\n"

    collector = AdbLogcatCollector(mock_adb)
    dev = DeviceMetadata(serial="SERIAL_01")
    sw = SoftwareIdentity()
    wl = WorkloadIdentity()

    records = collector.collect(
        serial="SERIAL_01",
        experiment_id="EXP-20260913-001",
        device=dev,
        software=sw,
        workload=wl,
        artifacts_dir=tmp_path,
        max_lines=100,
    )

    assert len(records) == 1
    rec = records[0]
    assert rec.metric.name == "adb_logcat_lines"
    assert rec.metric.value == 3
    assert rec.capability == CapabilityStatus.UNIVERSAL

    # Verify logcat.txt artifact was written
    log_artifact = tmp_path / "logcat.txt"
    assert log_artifact.exists()
    assert "line 1" in log_artifact.read_text(encoding="utf-8")


def test_logcat_collector_failure_handles_gracefully(tmp_path: Path):
    mock_adb = MagicMock()
    mock_adb.run_serial_cmd.side_effect = RuntimeError("ADB daemon died")

    collector = AdbLogcatCollector(mock_adb)
    dev = DeviceMetadata(serial="SERIAL_01")
    sw = SoftwareIdentity()
    wl = WorkloadIdentity()

    records = collector.collect(
        serial="SERIAL_01",
        experiment_id="EXP-20260913-001",
        device=dev,
        software=sw,
        workload=wl,
        artifacts_dir=tmp_path,
    )

    assert len(records) == 1
    rec = records[0]
    assert rec.metric.value is None
    assert rec.capability == CapabilityStatus.UNSUPPORTED
    assert "ADB daemon died" in rec.reason
