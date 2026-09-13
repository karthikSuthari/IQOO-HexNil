"""Unit tests for DifferentialExperimentOrchestrator."""

import json
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch

from hexnil.baseline.models import (
    EnvironmentSnapshot,
    QualityReport,
    StabilizationPolicy,
    StabilizationResult,
    V0SoftwareIdentity,
)
from hexnil.device.models import AdbStatus, DeviceMetadata, ExperimentRecord
from hexnil.diff.models import (
    ComparisonQualityReport,
    InstallOutcome,
    InstallResult,
    V1SoftwareIdentity,
)
from hexnil.diff.orchestrator import DifferentialExperimentOrchestrator
from hexnil.diff.store import ComparisonStore
from hexnil.exceptions import HexnilError
from hexnil.experiments.store import ExperimentStore
from hexnil.workloads.models import RunStatus, WorkloadDefinition, WorkloadRun, StepAction, WorkloadStep
from hexnil.workloads.registry import WorkloadRegistry


@pytest.fixture
def mock_adb():
    client = MagicMock()
    client.get_all_props.return_value = {
        "ro.build.version.release": "16",
        "ro.build.id": "BP1A.250305.019",
        "ro.build.fingerprint": "vivo/I2302/I2302:16/BP1A.250305.019/test:user/release-keys",
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
        android_version="16",
        sdk=36,
        build_fingerprint="vivo/I2302/I2302:16/BP1A.250305.019/test:user/release-keys",
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

    exp_dir = exp_store.get_experiment_dir(v0_id)
    (exp_dir / "baseline").mkdir(parents=True, exist_ok=True)

    qual = QualityReport(
        experiment_id=v0_id,
        device_serial="test-serial",
        device_model="vivo I2302",
        is_clean_baseline=is_clean,
        summary_verdict="[TRUSTED_V0_BASELINE]" if is_clean else "[CONTAMINATED_BASELINE]",
    )
    (exp_dir / "baseline" / "quality.json").write_text(qual.model_dump_json(indent=2), encoding="utf-8")

    soft = V0SoftwareIdentity(
        package="com.example.iqoo_hexnil",
        version_name="1.0",
        version_code=1,
        apk_sha256="sha000",
        captured_at="2026-09-13T10:00:00Z",
    )
    (exp_dir / "software.json").write_text(soft.model_dump_json(indent=2), encoding="utf-8")

    env = EnvironmentSnapshot(
        timestamp="2026-09-13T10:00:00Z",
        battery_level_percent=80.0,
        battery_charging_state="DISCHARGING",
    )
    (exp_dir / "environment.json").write_text(env.model_dump_json(indent=2), encoding="utf-8")

    # Workload definition
    w_def = WorkloadDefinition(
        workload_id="startup_01",
        version="1.0",
        description="Startup workload",
        steps=[WorkloadStep(step_id="step1", action=StepAction.LAUNCH_APP)],
        configuration={"timeout_ms": 5000},
    )
    w_hash = w_def.compute_hash()

    (exp_dir / "workloads.json").write_text(
        json.dumps(
            [
                {
                    "workload_id": "startup_01",
                    "version": "1.0",
                    "configuration_hash": w_hash,
                }
            ]
        ),
        encoding="utf-8",
    )

    # Workload run
    v0_run = WorkloadRun(
        experiment_id=v0_id,
        run_id=f"RUN-{v0_id}-01",
        workload_id="startup_01",
        workload_version="1.0",
        configuration_hash=w_hash,
        iteration=1,
        started_at="2026-09-13T10:05:00Z",
        ended_at="2026-09-13T10:05:01Z",
        duration_ms=450.0,
        status=RunStatus.SUCCESS,
    )
    exp_store.save_workload_run(v0_id, v0_run)
    return w_def


def test_inspect_v0_baseline(tmp_path: Path, mock_adb):
    exp_store = ExperimentStore(tmp_path / "experiments")
    comp_store = ComparisonStore(tmp_path / "comparisons")
    orchestrator = DifferentialExperimentOrchestrator(mock_adb, exp_store, comp_store)

    v0_id = "EXP-20260913-001"
    _setup_v0_baseline(exp_store, v0_id, is_clean=True)

    info = orchestrator.inspect_v0_baseline(v0_id)
    assert info["experiment_id"] == v0_id
    assert info["is_clean_v0_baseline"] is True
    assert info["package"] == "com.example.iqoo_hexnil"
    assert info["version"] == "1.0"
    assert info["workloads_count"] == 1
    assert info["valid_runs_count"] == 1


def test_run_differential_unclean_baseline_fails(tmp_path: Path, mock_adb):
    exp_store = ExperimentStore(tmp_path / "experiments")
    comp_store = ComparisonStore(tmp_path / "comparisons")
    orchestrator = DifferentialExperimentOrchestrator(mock_adb, exp_store, comp_store)

    v0_id = "EXP-20260913-002"
    _setup_v0_baseline(exp_store, v0_id, is_clean=False)

    fake_apk = tmp_path / "v1.apk"
    fake_apk.write_bytes(b"dummy")

    with pytest.raises(HexnilError) as exc_info:
        orchestrator.run_differential_experiment(v0_id, fake_apk, "test-serial", iterations=1)
    assert "not a trusted baseline" in exc_info.value.message


def test_run_differential_install_failure(tmp_path: Path, mock_adb):
    exp_store = ExperimentStore(tmp_path / "experiments")
    comp_store = ComparisonStore(tmp_path / "comparisons")
    orchestrator = DifferentialExperimentOrchestrator(mock_adb, exp_store, comp_store)

    v0_id = "EXP-20260913-003"
    _setup_v0_baseline(exp_store, v0_id, is_clean=True)

    fake_apk = tmp_path / "v1.apk"
    fake_apk.write_bytes(b"dummy")

    with patch.object(orchestrator.installer, "install_v1_update") as mock_install:
        mock_install.return_value = InstallResult(
            apk_path=str(fake_apk),
            apk_sha256="sha1",
            outcome=InstallOutcome.INSTALL_FAILED_VERSION_DOWNGRADE,
            raw_output="Downgrade error",
            duration_ms=100.0,
            success=False,
            error_message="Downgrade not allowed",
        )

        with pytest.raises(HexnilError) as exc_info:
            orchestrator.run_differential_experiment(v0_id, fake_apk, "test-serial", iterations=1)
        assert "Failed to install V1 update APK" in exc_info.value.message


def test_run_differential_success(tmp_path: Path, mock_adb):
    exp_store = ExperimentStore(tmp_path / "experiments")
    comp_store = ComparisonStore(tmp_path / "comparisons")

    registry = WorkloadRegistry()
    orchestrator = DifferentialExperimentOrchestrator(mock_adb, exp_store, comp_store, registry=registry)

    v0_id = "EXP-20260913-004"
    w_def = _setup_v0_baseline(exp_store, v0_id, is_clean=True)
    registry.register(w_def)

    fake_apk = tmp_path / "v1.apk"
    fake_apk.write_bytes(b"dummy_v1_apk_data")

    with patch.object(orchestrator.installer, "install_v1_update") as mock_install, \
         patch("hexnil.diff.orchestrator.capture_v1_software_identity") as mock_cap, \
         patch.object(orchestrator.stabilizer, "stabilize") as mock_stab, \
         patch("hexnil.diff.orchestrator.capture_environment_snapshot") as mock_env, \
         patch.object(orchestrator.engine, "execute") as mock_exec:

        mock_install.return_value = InstallResult(
            apk_path=str(fake_apk),
            apk_sha256="sha_v1_host",
            outcome=InstallOutcome.SUCCESS,
            raw_output="Success",
            duration_ms=1200.0,
            success=True,
        )
        mock_cap.return_value = V1SoftwareIdentity(
            package="com.example.iqoo_hexnil",
            version_name="1.1",
            version_code=2,
            apk_sha256="sha_v1_host",
            installed_at="2026-09-13T11:00:00Z",
        )
        mock_stab.return_value = StabilizationResult(success=True)
        mock_env.return_value = EnvironmentSnapshot(
            timestamp="2026-09-13T11:00:00Z",
            battery_level_percent=79.0,
        )

        v1_run = WorkloadRun(
            experiment_id="EXP-V1",
            run_id="RUN-V1-01",
            workload_id="startup_01",
            workload_version="1.0",
            configuration_hash=w_def.compute_hash(),
            iteration=1,
            started_at="2026-09-13T11:05:00Z",
            ended_at="2026-09-13T11:05:01Z",
            duration_ms=440.0,
            status=RunStatus.SUCCESS,
        )
        mock_exec.return_value = [v1_run]

        quality = orchestrator.run_differential_experiment(v0_id, fake_apk, "test-serial", iterations=1)

        assert quality.is_clean_comparison is True
        assert quality.summary_verdict == "TRUSTED_DIFFERENTIAL_EVIDENCE"
        assert quality.matched_pairs_count == 1
        assert quality.workloads_matched == ["startup_01"]

        # Check saved comparison in store
        comp = comp_store.load_comparison(quality.comparison_id)
        assert comp.v0_experiment_id == v0_id
        assert comp.v1_software.version_name == "1.1"
        assert len(comp.run_pairs) == 1
        assert comp.run_pairs[0].pair_status.value == "MATCHED"
