"""Unit tests for Phase 4 baseline domain models."""

import pytest
from hexnil.baseline.models import (
    BaselineMetricSummary,
    EnvironmentConditionStatus,
    EnvironmentSnapshot,
    ProvenanceRecord,
    QualityReport,
    StabilizationPolicy,
    StabilizationResult,
    UncertaintyEstimate,
    V0SoftwareIdentity,
    WorkloadProvenance,
)


def test_v0_software_identity_serialization():
    """Verify V0SoftwareIdentity captures required fields and serializes cleanly."""
    ident = V0SoftwareIdentity(
        package="com.example.iqoo_hexnil",
        version_name="1.0.0",
        version_code=100,
        apk_path="/data/app/base.apk",
        apk_sha256="c02a0430aa40552bf313cb04ffa1d33bacd063a96b98aee7ff5f773922f27fc8",
        android_os_version="16",
        build_id="BP1A.250305.019",
        build_fingerprint="vivo/I2302/I2302:16/BP1A.250305.019/1741160492:user/release-keys",
        captured_at="2026-09-13T12:00:00Z",
        software_type="V0_ORIGINAL",
    )
    dumped = ident.model_dump()
    assert dumped["package"] == "com.example.iqoo_hexnil"
    assert dumped["software_type"] == "V0_ORIGINAL"
    assert dumped["apk_sha256"] == "c02a0430aa40552bf313cb04ffa1d33bacd063a96b98aee7ff5f773922f27fc8"

    roundtrip = V0SoftwareIdentity.model_validate_json(ident.model_dump_json())
    assert roundtrip.apk_sha256 == ident.apk_sha256
    assert roundtrip.build_id == "BP1A.250305.019"


def test_environment_snapshot_conditions():
    """Verify EnvironmentSnapshot tracks measured/controlled/unsupported statuses."""
    env = EnvironmentSnapshot(
        timestamp="2026-09-13T12:00:00Z",
        battery_level_percent=85.0,
        battery_charging_state="discharging",
        battery_temperature_c=29.5,
        screen_on=True,
        screen_brightness=128,
        thermal_status="NONE",
        wifi_enabled=True,
        wifi_connected=True,
        device_idle_state="mState=ACTIVE",
        orientation="ROTATION_0",
        app_running=True,
        condition_status={
            "battery_level_percent": EnvironmentConditionStatus.MEASURED,
            "battery_charging_state": EnvironmentConditionStatus.MEASURED,
            "screen_on": EnvironmentConditionStatus.VERIFIED,
            "thermal_status": EnvironmentConditionStatus.MEASURED,
        },
    )
    assert env.battery_level_percent == 85.0
    assert env.condition_status["screen_on"] == EnvironmentConditionStatus.VERIFIED
    assert env.condition_status["battery_level_percent"] == EnvironmentConditionStatus.MEASURED


def test_stabilization_models():
    """Verify StabilizationPolicy defaults and StabilizationResult tracking."""
    policy = StabilizationPolicy()
    assert policy.wake_screen is True
    assert policy.enforce_battery_min == 15
    assert policy.max_thermal_level == "moderate"

    res = StabilizationResult(
        attempted_actions=["wake_screen", "force_stop_app"],
        verified_conditions={"screen_awake": True, "battery_sufficient": True},
        limitations=["Background tasks not completely halt-able without root"],
        success=True,
    )
    assert res.success is True
    assert len(res.attempted_actions) == 2
    assert "screen_awake" in res.verified_conditions


def test_quality_report_model():
    """Verify QualityReport structure and clean baseline verdict."""
    qr = QualityReport(
        experiment_id="EXP-20260913-001",
        baseline_type="V0",
        device_serial="test_serial_123",
        device_model="vivo I2302",
        v0_software={"package": "com.example.iqoo_hexnil", "version_name": "1.0"},
        workloads_requested=["startup_01", "cpu_01"],
        iterations_requested_per_workload=5,
        total_iterations_requested=10,
        total_runs_completed=10,
        valid_runs_count=10,
        invalid_runs_count=0,
        failed_runs_count=0,
        precondition_failures_count=0,
        telemetry_records_count=40,
        artifacts_count=6,
        evidence_coverage="2/2 workloads validated with evidence",
        contamination_flags=[],
        is_clean_baseline=True,
        summary_verdict="TRUSTED_V0_BASELINE",
    )
    assert qr.is_clean_baseline is True
    assert qr.summary_verdict == "TRUSTED_V0_BASELINE"
    json_str = qr.model_dump_json()
    assert "TRUSTED_V0_BASELINE" in json_str


def test_provenance_record():
    """Verify ProvenanceRecord captures workload and artifact integrity hashes."""
    prov = ProvenanceRecord(
        experiment_id="EXP-20260913-001",
        analysis_version="1.0.0",
        created_at="2026-09-13T12:00:00Z",
        device_serial="test_serial_123",
        build_fingerprint="fingerprint_xyz",
        apk_sha256="abc123sha",
        workloads={
            "startup_01": WorkloadProvenance(
                workload_id="startup_01",
                workload_version="1.0.0",
                configuration_hash="hash123",
                run_ids=["RUN-1", "RUN-2"],
                valid_run_ids=["RUN-1", "RUN-2"],
                telemetry_files=["telemetry/android.jsonl"],
            )
        },
        artifact_hashes={"telemetry/android.jsonl": "hash_tel_001"},
    )
    assert prov.workloads["startup_01"].configuration_hash == "hash123"
    assert prov.artifact_hashes["telemetry/android.jsonl"] == "hash_tel_001"
