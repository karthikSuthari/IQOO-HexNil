"""Unit tests for Mobile OS Update Differential Experiment Mode (Case B)."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from hexnil.baseline.models import (
    EnvironmentSnapshot,
    QualityReport,
    StabilizationPolicy,
    StabilizationResult,
    V0SoftwareIdentity,
)
from hexnil.device.models import AdbStatus, DeviceMetadata, ExperimentRecord
from hexnil.diff.models import InstallOutcome, PairStatus
from hexnil.diff.orchestrator import DifferentialExperimentOrchestrator
from hexnil.diff.store import ComparisonStore
from hexnil.exceptions import HexnilError
from hexnil.experiments.store import ExperimentStore
from hexnil.workloads.models import RunStatus, StepAction, WorkloadDefinition, WorkloadRun, WorkloadStep
from hexnil.workloads.registry import WorkloadRegistry


@pytest.fixture
def mock_adb():
    client = MagicMock()
    # OS build updated to BP1A.250305.020 (Android 16)
    client.get_all_props.return_value = {
        "ro.build.version.release": "16",
        "ro.build.id": "BP1A.250305.020",
        "ro.build.fingerprint": "vivo/I2302/I2302:16/BP1A.250305.020/test:user/release-keys",
    }
    client.run_serial_cmd.return_value = "package:/data/app/test/base.apk\n"
    return client


def _setup_v0_baseline(exp_store: ExperimentStore, v0_id: str, is_clean: bool = True):
    dev = DeviceMetadata(
        serial="test-serial",
        manufacturer="vivo",
        model="vivo I2302",
        brand="vivo",
        board="taro",
        android_version="15",
        sdk=35,
        build_fingerprint="vivo/I2302/I2302:15/BP1A.250101.010/test:user/release-keys",
    )
    rec = ExperimentRecord(
        experiment_id=v0_id,
        created_at="2026-09-13T10:00:00Z",
        device=dev,
        adb=AdbStatus(state="device", connected=True),
        phase="04_v0_baseline",
        status="completed",
    )
    exp_store.save(rec)

    software = V0SoftwareIdentity(
        package="com.example.iqoo_hexnil",
        version_name="1.0",
        version_code=1,
        apk_path="/data/app/test/base.apk",
        apk_sha256="a" * 64,
        android_os_version="15",
        build_id="BP1A.250101.010",
        build_fingerprint=dev.build_fingerprint,
        captured_at="2026-09-13T10:00:00Z",
    )
    exp_dir = exp_store.get_experiment_dir(v0_id)
    (exp_dir / "software.json").write_text(software.model_dump_json(indent=2), encoding="utf-8")

    env = EnvironmentSnapshot(
        timestamp="2026-09-13T10:00:00Z",
        battery_level_percent=85.0,
        battery_charging_state="discharging",
        battery_temperature_c=29.0,
        thermal_status="none",
    )
    (exp_dir / "environment.json").write_text(env.model_dump_json(indent=2), encoding="utf-8")
    (exp_dir / "baseline").mkdir(parents=True, exist_ok=True)

    qual = QualityReport(
        experiment_id=v0_id,
        device_serial="test-serial",
        device_model="vivo I2302",
        software_version="1.0",
        apk_sha256="a" * 64,
        workloads_requested=["scroll_01"],
        iterations_requested=1,
        total_runs_executed=1,
        valid_runs_count=1 if is_clean else 0,
        failed_runs_count=0 if is_clean else 1,
        is_clean_baseline=is_clean,
        summary_verdict="TRUSTED_BASELINE" if is_clean else "CONTAMINATED_BASELINE",
    )
    (exp_dir / "baseline" / "quality.json").write_text(qual.model_dump_json(indent=2), encoding="utf-8")

    workload = WorkloadDefinition(
        workload_id="scroll_01",
        version="1.0.0",
        description="Test scroll workload",
        preconditions={},
        steps=[WorkloadStep(step_id="step1", action=StepAction.LAUNCH_APP)],
    )
    (exp_dir / "workloads.json").write_text(
        json.dumps(
            [
                {
                    "workload_id": workload.workload_id,
                    "version": workload.version,
                    "configuration_hash": workload.compute_hash(),
                    "description": workload.description,
                    "preconditions": workload.preconditions,
                }
            ]
        ),
        encoding="utf-8",
    )

    run = WorkloadRun(
        experiment_id=v0_id,
        run_id="run-v0-001",
        workload_id="scroll_01",
        workload_version="1.0.0",
        iteration=1,
        started_at="2026-09-13T10:05:00Z",
        ended_at="2026-09-13T10:05:01Z",
        status=RunStatus.SUCCESS,
        duration_ms=100.0,
        configuration_hash=workload.compute_hash(),
    )
    exp_store.save_workload_run(v0_id, run)


def test_os_update_differential_orchestration_success(tmp_path, mock_adb):
    """Test differential experiment execution in OS update mode without APK install."""
    exp_store = ExperimentStore(tmp_path / "experiments")
    comp_store = ComparisonStore(tmp_path / "comparisons")

    v0_id = exp_store.generate_experiment_id()
    _setup_v0_baseline(exp_store, v0_id, is_clean=True)

    registry = WorkloadRegistry()
    test_workload = WorkloadDefinition(
        workload_id="scroll_01",
        version="1.0.0",
        description="Test scroll workload",
        preconditions={},
        steps=[WorkloadStep(step_id="step1", action=StepAction.LAUNCH_APP)],
    )
    registry.register(test_workload)

    mock_engine = MagicMock()
    v1_run = WorkloadRun(
        experiment_id="EXP-V1",
        run_id="run-v1-001",
        workload_id="scroll_01",
        workload_version="1.0.0",
        iteration=1,
        started_at="2026-09-14T10:05:00Z",
        ended_at="2026-09-14T10:05:01Z",
        status=RunStatus.SUCCESS,
        duration_ms=95.0,
        configuration_hash=test_workload.compute_hash(),
    )
    mock_engine.execute.return_value = [v1_run]

    mock_bridge = MagicMock()

    orchestrator = DifferentialExperimentOrchestrator(
        adb=mock_adb,
        exp_store=exp_store,
        comp_store=comp_store,
        registry=registry,
        engine=mock_engine,
        bridge=mock_bridge,
    )

    with patch.object(
        orchestrator.stabilizer,
        "stabilize",
        return_value=StabilizationResult(success=True, pre_battery_percent=84.0, post_battery_percent=84.0),
    ):
        quality = orchestrator.run_differential_experiment(
            v0_experiment_id=v0_id,
            serial="test-serial",
            iterations=1,
            is_os_update=True,
        )

    assert quality.is_clean_comparison is True
    assert quality.summary_verdict == "TRUSTED_DIFFERENTIAL_EVIDENCE"
    assert quality.update_type == "os_update"
    assert quality.v0_build_id == "BP1A.250101.010"
    assert quality.v1_build_id == "BP1A.250305.020"
    assert quality.v0_os_version == "15"
    assert quality.v1_os_version == "16"

    # Verify comparison record
    comp_record = comp_store.load_comparison(quality.comparison_id)
    assert comp_record.update_type == "os_update"
    assert comp_record.install_result.outcome == InstallOutcome.SUCCESS_OS_UPDATE
    assert comp_record.install_result.update_type == "os_update"
    assert len(comp_record.run_pairs) == 1
    assert comp_record.run_pairs[0].pair_status == PairStatus.MATCHED


def test_os_update_missing_probe_fails(tmp_path, mock_adb):
    """Test that OS update differential fails gracefully if probe app is not installed."""
    exp_store = ExperimentStore(tmp_path / "experiments")
    comp_store = ComparisonStore(tmp_path / "comparisons")

    v0_id = exp_store.generate_experiment_id()
    _setup_v0_baseline(exp_store, v0_id, is_clean=True)

    mock_adb.run_serial_cmd.return_value = ""  # Probe package not found

    orchestrator = DifferentialExperimentOrchestrator(
        adb=mock_adb,
        exp_store=exp_store,
        comp_store=comp_store,
    )

    with pytest.raises(HexnilError) as exc_info:
        orchestrator.run_differential_experiment(
            v0_experiment_id=v0_id,
            serial="test-serial",
            is_os_update=True,
        )
    assert "not installed on device" in str(exc_info.value)


def test_diff_cli_requires_either_apk_or_os_update(tmp_path):
    """Test CLI raises error if neither --apk nor --os-update is given."""
    from hexnil.cli import handle_diff_run
    from hexnil.config import HexnilConfig
    import argparse

    config = HexnilConfig(data_dir=tmp_path / "data", adb_path="adb")
    args = argparse.Namespace(
        v0_experiment_id="EXP-123",
        apk=None,
        os_update=False,
        serial="test-serial",
    )
    with pytest.raises(HexnilError) as exc_info:
        handle_diff_run(args, config)
    assert "Either --os-update or --apk" in str(exc_info.value)
