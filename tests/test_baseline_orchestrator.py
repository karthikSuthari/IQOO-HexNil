"""Unit tests for Phase 4 baseline orchestration, environment, and quality auditing."""

from pathlib import Path
from unittest.mock import MagicMock
import pytest

from hexnil.baseline.environment import capture_environment_snapshot
from hexnil.baseline.identity import capture_v0_software_identity
from hexnil.baseline.models import StabilizationPolicy, V0SoftwareIdentity
from hexnil.baseline.orchestrator import BaselineExperimentOrchestrator
from hexnil.baseline.quality import evaluate_baseline_quality
from hexnil.baseline.stabilizer import DeviceStabilizer
from hexnil.experiments.store import ExperimentStore
from hexnil.workloads.models import RunStatus, WorkloadDefinition, WorkloadRun


def test_capture_v0_software_identity_mocked():
    """Verify parsing of package version, APK path, sha256, and OS build."""
    mock_adb = MagicMock()
    mock_adb.get_all_props.return_value = {
        "ro.build.version.release": "16",
        "ro.build.id": "BP1A.250305.019",
        "ro.build.fingerprint": "vivo/I2302/I2302:16/BP1A/release-keys",
    }
    mock_adb.run_serial_cmd.side_effect = [
        # pm path output
        "package:/data/app/~~xyz/com.example.iqoo_hexnil/base.apk\n",
        # sha256sum output
        "c02a0430aa40552bf313cb04ffa1d33bacd063a96b98aee7ff5f773922f27fc8  /data/app/base.apk\n",
        # dumpsys package output
        "  versionCode=42 minSdk=24 targetSdk=36\n  versionName=2.1.0\n",
    ]

    ident = capture_v0_software_identity(mock_adb, "serial_1", "com.example.iqoo_hexnil")
    assert ident.package == "com.example.iqoo_hexnil"
    assert ident.version_name == "2.1.0"
    assert ident.version_code == 42
    assert ident.apk_sha256 == "c02a0430aa40552bf313cb04ffa1d33bacd063a96b98aee7ff5f773922f27fc8"
    assert ident.android_os_version == "16"
    assert ident.software_type == "V0_ORIGINAL"


def test_capture_environment_snapshot_mocked():
    """Verify environment snapshot accurately parses battery, power, wifi, and thermals."""
    mock_adb = MagicMock()
    mock_adb.run_serial_cmd.side_effect = [
        # dumpsys battery
        "level: 88\ntemperature: 295\nUSB powered: false\nAC powered: false\n",
        # dumpsys power
        "Display Power: state=ON\nmWakefulness=Awake\n",
        # settings get screen_brightness
        "150\n",
        # dumpsys thermalservice
        "Current Thermal Status: 0 (NONE)\n",
        # dumpsys wifi
        "Wi-Fi is enabled\nSupplicant state: COMPLETED\n",
        # dumpsys deviceidle
        "mState=ACTIVE\n",
        # dumpsys window
        "mCurrentOrientation=ROTATION_0\n",
        # pidof package
        "12345\n",
    ]

    env = capture_environment_snapshot(mock_adb, "serial_1", "com.example.iqoo_hexnil")
    assert env.battery_level_percent == 88.0
    assert env.battery_temperature_c == 29.5
    assert env.battery_charging_state == "discharging"
    assert env.screen_on is True
    assert env.screen_brightness == 150
    assert env.thermal_status == "NONE"
    assert env.wifi_enabled is True
    assert env.wifi_connected is True
    assert env.app_running is True


def test_device_stabilizer_wake_and_clean_state():
    """Verify stabilizer wakes screen, stops app, and checks thresholds."""
    mock_adb = MagicMock()
    mock_adb.run_serial_cmd.side_effect = [
        # screen power check -> asleep
        "mWakefulness=Asleep\n",
        # keyevent KEYCODE_WAKEUP
        "",
        # screen power check after -> awake
        "mWakefulness=Awake\n",
        # am force-stop
        "",
        # pidof check -> empty (stopped)
        "",
        # dumpsys battery
        "level: 90\n",
        # dumpsys thermalservice
        "Current Thermal Status: 1\n",
    ]

    policy = StabilizationPolicy(
        wake_screen=True,
        enforce_battery_min=20,
        max_thermal_level="moderate",
        force_stop_app_before=True,
        stabilization_cooldown_seconds=0.0,
    )
    stabilizer = DeviceStabilizer(mock_adb)
    res = stabilizer.stabilize("serial_1", policy, "com.example.iqoo_hexnil")

    assert res.success is True
    assert res.verified_conditions["screen_awake"] is True
    assert res.verified_conditions["app_stopped"] is True
    assert res.verified_conditions["battery_sufficient"] is True
    assert res.verified_conditions["thermal_headroom_ok"] is True


def test_evaluate_baseline_quality_verdicts():
    """Verify trusted, contaminated, and insufficient data verdicts."""
    v0_soft = V0SoftwareIdentity(
        package="com.test",
        version_name="1.0",
        version_code=1,
        captured_at="2026-09-13T12:00:00Z",
    )

    # 1. Trusted V0 baseline
    runs_clean = [
        WorkloadRun(
            experiment_id="EXP-1",
            run_id=f"RUN-{i}",
            workload_id="startup_01",
            workload_version="1.0",
            configuration_hash="hash",
            iteration=i,
            started_at="",
            ended_at="",
            duration_ms=100.0,
            status=RunStatus.SUCCESS,
        )
        for i in range(1, 4)
    ]
    qr_clean = evaluate_baseline_quality(
        experiment_id="EXP-1",
        device_serial="s1",
        device_model="M1",
        v0_software=v0_soft,
        workloads_requested=["startup_01"],
        iterations_requested_per_workload=3,
        runs=runs_clean,
        telemetry_records=[],
        artifacts=["art1"],
        contamination_flags=[],
    )
    assert qr_clean.is_clean_baseline is True
    assert qr_clean.summary_verdict == "TRUSTED_V0_BASELINE"

    # 2. Contaminated baseline (e.g. build fingerprint changed)
    qr_contam = evaluate_baseline_quality(
        experiment_id="EXP-2",
        device_serial="s1",
        device_model="M1",
        v0_software=v0_soft,
        workloads_requested=["startup_01"],
        iterations_requested_per_workload=3,
        runs=runs_clean,
        telemetry_records=[],
        artifacts=[],
        contamination_flags=["Build fingerprint mismatch detected during suite"],
    )
    assert qr_contam.is_clean_baseline is False
    assert qr_contam.summary_verdict == "CONTAMINATED_BASELINE"


def test_orchestrator_end_to_end_mocked(tmp_path: Path):
    """Test full baseline orchestrator execution flow with mocked dependencies."""
    mock_adb = MagicMock()
    mock_adb.get_all_props.return_value = {
        "ro.product.manufacturer": "vivo",
        "ro.product.model": "I2302",
        "ro.product.device": "I2302",
        "ro.build.version.release": "16",
        "ro.build.version.sdk": "36",
        "ro.build.id": "BP1A.250305.019",
        "ro.build.fingerprint": "vivo/I2302/fp_clean",
        "ro.product.cpu.abi": "arm64-v8a",
    }
    mock_adb.run_serial_cmd.return_value = "mWakefulness=Awake\nlevel: 80\n"

    store = ExperimentStore(tmp_path)
    mock_registry = MagicMock()
    w_def = WorkloadDefinition(
        workload_id="startup_01",
        version="1.0.0",
        description="Startup workload",
        configuration={"action": "launch"},
    )
    mock_registry.get.return_value = w_def

    mock_engine = MagicMock()
    mock_run = WorkloadRun(
        experiment_id="EXP-MOCK",
        run_id="RUN-MOCK-1",
        workload_id="startup_01",
        workload_version="1.0.0",
        configuration_hash=w_def.compute_hash(),
        iteration=1,
        started_at="2026-09-13T12:00:00Z",
        ended_at="2026-09-13T12:00:01Z",
        duration_ms=500.0,
        status=RunStatus.SUCCESS,
    )
    mock_engine.execute.return_value = [mock_run]

    mock_bridge = MagicMock()

    orchestrator = BaselineExperimentOrchestrator(
        adb=mock_adb,
        store=store,
        registry=mock_registry,
        engine=mock_engine,
        bridge=mock_bridge,
    )

    policy = StabilizationPolicy(stabilization_cooldown_seconds=0.0)
    report = orchestrator.run_baseline_experiment(
        serial="mock_serial_001",
        iterations=1,
        workload_ids=["startup_01"],
        stabilization_policy=policy,
    )

    assert report.experiment_id.startswith("EXP-")
    assert report.is_clean_baseline is True
    assert report.summary_verdict == "TRUSTED_V0_BASELINE"

    # Verify baseline directory outputs
    exp_dir = store.get_experiment_dir(report.experiment_id)
    assert (exp_dir / "software.json").exists()
    assert (exp_dir / "environment.json").exists()
    assert (exp_dir / "workloads.json").exists()
    assert (exp_dir / "baseline" / "metrics.json").exists()
    assert (exp_dir / "baseline" / "quality.json").exists()
    assert (exp_dir / "baseline" / "provenance.json").exists()

    # Verify ExperimentStore loader methods
    loaded_metrics = store.load_baseline_metrics(report.experiment_id)
    assert loaded_metrics is not None
    assert "workloads" in loaded_metrics

    loaded_quality = store.load_baseline_quality(report.experiment_id)
    assert loaded_quality is not None
    assert loaded_quality.summary_verdict == "TRUSTED_V0_BASELINE"

    loaded_prov = store.load_baseline_provenance(report.experiment_id)
    assert loaded_prov is not None
    assert loaded_prov.analysis_version == "1.0.0"
