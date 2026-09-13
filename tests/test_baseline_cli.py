"""Unit tests for Phase 4 baseline CLI commands."""

import json
from unittest.mock import MagicMock, patch
import pytest

from hexnil.baseline.models import QualityReport, V0SoftwareIdentity
from hexnil.cli import create_parser, main
from hexnil.config import HexnilConfig
from hexnil.device.models import AdbStatus, DeviceMetadata, DiscoveredDevice, ExperimentRecord


def test_baseline_parser_arguments():
    """Verify baseline CLI argument parsing."""
    parser = create_parser()

    # baseline run
    args = parser.parse_args(["baseline", "run", "--serial", "test_ser", "--iterations", "3", "--suite", "startup_01,cpu_01", "--json"])
    assert args.command == "baseline"
    assert args.subcommand == "run"
    assert args.serial == "test_ser"
    assert args.iterations == 3
    assert args.suite == "startup_01,cpu_01"
    assert args.json is True

    # baseline show
    args_show = parser.parse_args(["baseline", "show", "EXP-20260913-001"])
    assert args_show.command == "baseline"
    assert args_show.subcommand == "show"
    assert args_show.experiment_id == "EXP-20260913-001"

    # baseline quality
    args_qual = parser.parse_args(["baseline", "quality", "EXP-20260913-001", "--json"])
    assert args_qual.command == "baseline"
    assert args_qual.subcommand == "quality"
    assert args_qual.experiment_id == "EXP-20260913-001"
    assert args_qual.json is True

    # baseline summary
    args_sum = parser.parse_args(["baseline", "summary", "EXP-20260913-001"])
    assert args_sum.command == "baseline"
    assert args_sum.subcommand == "summary"
    assert args_sum.experiment_id == "EXP-20260913-001"


def test_baseline_run_cli_mocked(capsys):
    """Test CLI dispatch of 'hexnil baseline run' with mocked dependencies."""
    mock_quality = QualityReport(
        experiment_id="EXP-20260913-001",
        baseline_type="V0",
        device_serial="test_serial_1",
        device_model="vivo I2302",
        v0_software={"package": "com.example.iqoo_hexnil"},
        workloads_requested=["startup_01"],
        iterations_requested_per_workload=1,
        total_iterations_requested=1,
        total_runs_completed=1,
        valid_runs_count=1,
        evidence_coverage="1/1 workloads validated with evidence",
        is_clean_baseline=True,
        summary_verdict="TRUSTED_V0_BASELINE",
    )

    with patch("hexnil.cli.AdbClient") as mock_adb, \
         patch("hexnil.cli.DeviceDiscovery") as mock_disc, \
         patch("hexnil.cli.BaselineExperimentOrchestrator") as mock_orch_cls:

        mock_disc.return_value.select_device.return_value = DiscoveredDevice(
            serial="test_serial_1",
            state="device",
        )
        mock_orch = MagicMock()
        mock_orch.run_baseline_experiment.return_value = mock_quality
        mock_orch_cls.return_value = mock_orch

        exit_code = main(["baseline", "run", "--serial", "test_serial_1", "--iterations", "1"])
        assert exit_code == 0

        captured = capsys.readouterr().out
        assert "Hexnil V0 Baseline Experiment Quality Audit" in captured
        assert "EXP-20260913-001" in captured
        assert "[TRUSTED_V0_BASELINE]" in captured


def test_baseline_quality_cli_json(capsys):
    """Test CLI dispatch of 'hexnil baseline quality' with --json."""
    mock_quality = QualityReport(
        experiment_id="EXP-20260913-001",
        baseline_type="V0",
        device_serial="test_serial_1",
        device_model="vivo I2302",
        v0_software={"package": "com.example.iqoo_hexnil"},
        workloads_requested=["startup_01"],
        iterations_requested_per_workload=2,
        total_iterations_requested=2,
        total_runs_completed=2,
        valid_runs_count=2,
        is_clean_baseline=True,
        summary_verdict="TRUSTED_V0_BASELINE",
    )

    with patch("hexnil.cli.ExperimentStore") as mock_store_cls:
        mock_store = MagicMock()
        mock_store.load_baseline_quality.return_value = mock_quality
        mock_store_cls.return_value = mock_store

        exit_code = main(["baseline", "quality", "EXP-20260913-001", "--json"])
        assert exit_code == 0

        captured = capsys.readouterr().out
        data = json.loads(captured)
        assert data["experiment_id"] == "EXP-20260913-001"
        assert data["summary_verdict"] == "TRUSTED_V0_BASELINE"
