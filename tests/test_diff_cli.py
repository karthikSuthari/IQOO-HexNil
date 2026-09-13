"""Unit tests for Phase 5 CLI commands."""

import json
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch

from hexnil.cli import main
from hexnil.diff.models import (
    ComparisonQualityReport,
    ComparisonRecord,
    ComparisonRunPair,
    InstallOutcome,
    InstallResult,
    PairStatus,
    V1SoftwareIdentity,
    EnvironmentComparison,
    EnvironmentMatchStatus,
)
from hexnil.baseline.models import EnvironmentSnapshot, V0SoftwareIdentity
from hexnil.device.models import DeviceMetadata
from hexnil.diff.store import ComparisonStore


from hexnil.cli import create_parser, main


def test_diff_parser_arguments():
    parser = create_parser()

    # diff inspect
    args = parser.parse_args(["diff", "inspect", "EXP-001", "--json"])
    assert args.command == "diff"
    assert args.subcommand == "inspect"
    assert args.v0_experiment_id == "EXP-001"
    assert args.json is True

    # diff run
    args_run = parser.parse_args(["diff", "run", "EXP-001", "--apk", "v1.apk", "--iterations", "3", "--json"])
    assert args_run.command == "diff"
    assert args_run.subcommand == "run"
    assert args_run.v0_experiment_id == "EXP-001"
    assert args_run.apk == "v1.apk"
    assert args_run.iterations == 3
    assert args_run.json is True

    # diff show
    args_show = parser.parse_args(["diff", "show", "CMP-001"])
    assert args_show.command == "diff"
    assert args_show.subcommand == "show"
    assert args_show.comparison_id == "CMP-001"

    # diff pairs
    args_pairs = parser.parse_args(["diff", "pairs", "CMP-001", "--json"])
    assert args_pairs.command == "diff"
    assert args_pairs.subcommand == "pairs"
    assert args_pairs.comparison_id == "CMP-001"
    assert args_pairs.json is True

    # diff quality
    args_qual = parser.parse_args(["diff", "quality", "CMP-001"])
    assert args_qual.command == "diff"
    assert args_qual.subcommand == "quality"
    assert args_qual.comparison_id == "CMP-001"


def test_diff_inspect_cli(tmp_path: Path):
    with patch("hexnil.cli.DifferentialExperimentOrchestrator.inspect_v0_baseline") as mock_insp:
        mock_insp.return_value = {
            "experiment_id": "EXP-20260913-010",
            "device_serial": "serial-1",
            "device_model": "vivo I2302",
            "package": "com.example.iqoo_hexnil",
            "version": "1.0",
            "apk_sha256": "sha123",
            "workloads_count": 5,
            "valid_runs_count": 15,
            "is_clean_v0_baseline": True,
            "verdict": "TRUSTED_V0_BASELINE",
        }

        ret = main(["--data-dir", str(tmp_path), "diff", "inspect", "EXP-20260913-010"])
        assert ret == 0
        mock_insp.assert_called_once_with("EXP-20260913-010")


def test_diff_show_and_pairs_and_quality_cli(tmp_path: Path):
    comp_store = ComparisonStore(tmp_path / "comparisons")
    cmp_id = "CMP-20260913-001"

    dev = DeviceMetadata(
        serial="serial-1",
        manufacturer="vivo",
        model="vivo I2302",
        brand="vivo",
        board="taro",
        android_version="16",
        sdk=36,
    )
    v0_soft = V0SoftwareIdentity(
        package="com.example.iqoo_hexnil",
        version_name="1.0",
        version_code=1,
        captured_at="2026-09-13T10:00:00Z",
    )
    v1_soft = V1SoftwareIdentity(
        package="com.example.iqoo_hexnil",
        version_name="1.1",
        version_code=2,
        installed_at="2026-09-13T11:00:00Z",
    )
    snap0 = EnvironmentSnapshot(timestamp="2026-09-13T10:00:00Z", battery_level_percent=80.0)
    snap1 = EnvironmentSnapshot(timestamp="2026-09-13T11:00:00Z", battery_level_percent=78.0)
    env = EnvironmentComparison(
        v0_snapshot=snap0,
        v1_snapshot=snap1,
        battery_level_delta_percent=2.0,
        condition_match_statuses={"battery": EnvironmentMatchStatus.MATCHED},
    )
    pair = ComparisonRunPair(
        comparison_id=cmp_id,
        workload_id="startup_01",
        iteration=1,
        v0_run_id="V0-1",
        v1_run_id="V1-1",
        v0_duration_ms=400.0,
        v1_duration_ms=390.0,
        v0_configuration_hash="hash1",
        v1_configuration_hash="hash1",
        pair_status=PairStatus.MATCHED,
    )
    inst = InstallResult(
        apk_path="/tmp/v1.apk",
        apk_sha256="sha123",
        outcome=InstallOutcome.SUCCESS,
        raw_output="Success",
        duration_ms=1200.0,
        success=True,
    )

    record = ComparisonRecord(
        comparison_id=cmp_id,
        created_at="2026-09-13T11:30:00Z",
        v0_experiment_id="EXP-V0",
        v1_experiment_id="EXP-V1",
        device=dev,
        v0_software=v0_soft,
        v1_software=v1_soft,
        workload_suite=["startup_01"],
        environment_comparison=env,
        run_pairs=[pair],
        install_result=inst,
    )
    comp_store.save_comparison(record)

    # Also save quality.json
    qual = ComparisonQualityReport(
        comparison_id=cmp_id,
        v0_experiment_id="EXP-V0",
        v1_experiment_id="EXP-V1",
        device_serial="serial-1",
        device_model="vivo I2302",
        workloads_requested=["startup_01"],
        workloads_matched=["startup_01"],
        workloads_mismatched=[],
        iterations_requested=1,
        v0_valid_runs_count=1,
        v1_valid_runs_count=1,
        matched_pairs_count=1,
        unmatched_pairs_count=0,
        evidence_coverage="1/1 workloads have matched V0/V1 evidence",
        is_clean_comparison=True,
        summary_verdict="[TRUSTED_DIFFERENTIAL_EVIDENCE]",
    )
    cmp_dir = comp_store.get_comparison_dir(cmp_id)
    (cmp_dir / "quality.json").write_text(qual.model_dump_json(indent=2), encoding="utf-8")

    # Test diff show
    ret_show = main(["--data-dir", str(tmp_path), "diff", "show", cmp_id])
    assert ret_show == 0

    # Test diff pairs
    ret_pairs = main(["--data-dir", str(tmp_path), "diff", "pairs", cmp_id])
    assert ret_pairs == 0

    # Test diff quality
    ret_qual = main(["--data-dir", str(tmp_path), "diff", "quality", cmp_id])
    assert ret_qual == 0
