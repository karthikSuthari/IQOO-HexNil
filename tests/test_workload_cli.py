"""Unit tests for Workload CLI subcommands."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from hexnil.cli import create_parser, main
from hexnil.device.models import AdbStatus, DeviceMetadata, DiscoveredDevice, DeviceState
from hexnil.workloads.models import RunStatus, WorkloadRun


def test_workload_parser_arguments():
    parser = create_parser()

    args_list = parser.parse_args(["workload", "list"])
    assert args_list.command == "workload"
    assert args_list.subcommand == "list"

    args_show = parser.parse_args(["workload", "show", "startup_01", "--json"])
    assert args_show.command == "workload"
    assert args_show.subcommand == "show"
    assert args_show.workload_id == "startup_01"
    assert args_show.json is True

    args_val = parser.parse_args(["workload", "validate", "cpu_01"])
    assert args_val.command == "workload"
    assert args_val.subcommand == "validate"
    assert args_val.workload_id == "cpu_01"

    args_run = parser.parse_args([
        "workload", "run", "cpu_01", "-s", "DEVICE_123", "-i", "3", "--json"
    ])
    assert args_run.command == "workload"
    assert args_run.subcommand == "run"
    assert args_run.workload_id == "cpu_01"
    assert args_run.serial == "DEVICE_123"
    assert args_run.iterations == 3
    assert args_run.json is True


def test_cli_workload_list_and_show(capsys):
    ret_list = main(["workload", "list"])
    assert ret_list == 0
    captured_list = capsys.readouterr().out
    assert "cpu_01" in captured_list
    assert "startup_01" in captured_list

    ret_show = main(["workload", "show", "cpu_01"])
    assert ret_show == 0
    captured_show = capsys.readouterr().out
    assert "cpu_01" in captured_show
    assert "Configuration Hash:" in captured_show

    ret_show_json = main(["workload", "show", "cpu_01", "--json"])
    assert ret_show_json == 0
    data = json.loads(capsys.readouterr().out)
    assert data["workload_id"] == "cpu_01"
    assert "configuration_hash" in data


def test_cli_workload_validate(capsys):
    ret = main(["workload", "validate", "startup_01"])
    assert ret == 0
    captured = capsys.readouterr().out
    assert "is VALID" in captured


def test_cli_workload_run_mocked(tmp_path: Path, capsys):
    mock_dev = DiscoveredDevice(serial="SERIAL_123", state=DeviceState.DEVICE)
    mock_meta = DeviceMetadata(serial="SERIAL_123", manufacturer="vivo", model="I2302")
    mock_status = AdbStatus(state="device", connected=True)

    mock_run = WorkloadRun(
        experiment_id="EXP-20260913-099",
        run_id="RUN-20260913-120000-001-A1B2",
        workload_id="cpu_01",
        workload_version="1.0.0",
        configuration_hash="hash_123",
        iteration=1,
        started_at="2026-09-13T12:00:00Z",
        ended_at="2026-09-13T12:00:01Z",
        duration_ms=150.0,
        status=RunStatus.SUCCESS,
    )

    with patch("hexnil.cli.DeviceDiscovery.select_device", return_value=mock_dev), \
         patch("hexnil.cli.MetadataCollector.collect", return_value=(mock_meta, mock_status, [])), \
         patch("hexnil.cli.WorkloadExecutionEngine.execute", return_value=[mock_run]):

        ret = main(["--data-dir", str(tmp_path), "workload", "run", "cpu_01", "-s", "SERIAL_123"])
        assert ret == 0
        captured = capsys.readouterr().out
        assert "Hexnil Workload Execution Summary" in captured
        assert "cpu_01" in captured
        assert "Total Iterations:   1" in captured
        assert "RUN-20260913-120000-001-A1B2" in captured
