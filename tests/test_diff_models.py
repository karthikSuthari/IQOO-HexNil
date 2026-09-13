"""Unit tests for Phase 5 Differential models."""

import pytest
from hexnil.diff.models import (
    ComparisonQualityReport,
    ComparisonRecord,
    ComparisonRunPair,
    EnvironmentComparison,
    EnvironmentMatchStatus,
    InstallOutcome,
    InstallResult,
    PairStatus,
    V1SoftwareIdentity,
)


def test_v1_software_identity_defaults():
    ident = V1SoftwareIdentity(
        package="com.example.test",
        version_name="1.1",
        version_code=2,
        installed_at="2026-09-13T12:00:00Z",
    )
    assert ident.package == "com.example.test"
    assert ident.version_name == "1.1"
    assert ident.version_code == 2
    assert ident.software_type == "V1_UPDATED"
    assert ident.update_method == "adb_install_replace"
    assert ident.installed_at == "2026-09-13T12:00:00Z"


def test_install_result():
    res = InstallResult(
        apk_path="test.apk",
        apk_sha256="abc123sha",
        outcome=InstallOutcome.SUCCESS,
        raw_output="Success",
        duration_ms=145.0,
        success=True,
    )
    assert res.outcome == InstallOutcome.SUCCESS
    assert res.apk_sha256 == "abc123sha"
    assert res.error_message is None
    assert res.success is True


def test_environment_comparison():
    from hexnil.baseline.models import EnvironmentSnapshot

    snap0 = EnvironmentSnapshot(
        timestamp="2026-09-13T10:00:00Z",
        battery_level_percent=80.0,
        battery_charging_state="DISCHARGING",
        thermal_status="NONE",
    )
    snap1 = EnvironmentSnapshot(
        timestamp="2026-09-13T11:00:00Z",
        battery_level_percent=75.0,
        battery_charging_state="DISCHARGING",
        thermal_status="NONE",
    )
    env = EnvironmentComparison(
        v0_snapshot=snap0,
        v1_snapshot=snap1,
        battery_level_delta_percent=-5.0,
        thermal_status_transition="NONE -> NONE",
        condition_match_statuses={"battery": EnvironmentMatchStatus.MATCHED},
        drift_summary=["Battery dropped 5%"],
    )
    assert env.battery_level_delta_percent == -5.0
    assert env.condition_match_statuses["battery"] == EnvironmentMatchStatus.MATCHED
    assert env.thermal_status_transition == "NONE -> NONE"


def test_comparison_run_pair_matched():
    pair = ComparisonRunPair(
        comparison_id="CMP-20260913-001",
        workload_id="startup_01",
        iteration=1,
        v0_run_id="RUN-01",
        v1_run_id="RUN-02",
        v0_configuration_hash="hash123",
        v1_configuration_hash="hash123",
        v0_duration_ms=450.0,
        v1_duration_ms=430.0,
        pair_status=PairStatus.MATCHED,
    )
    assert pair.pair_status == PairStatus.MATCHED
    assert pair.v0_duration_ms == 450.0
    assert pair.v1_duration_ms == 430.0
    assert pair.mismatch_reason is None


def test_comparison_run_pair_mismatch():
    pair = ComparisonRunPair(
        comparison_id="CMP-20260913-001",
        workload_id="cpu_01",
        iteration=1,
        v0_run_id="RUN-01",
        v1_run_id="RUN-02",
        v0_configuration_hash="hashA",
        v1_configuration_hash="hashB",
        pair_status=PairStatus.CONFIGURATION_MISMATCH,
        mismatch_reason="Configuration hashes differ",
    )
    assert pair.pair_status == PairStatus.CONFIGURATION_MISMATCH
    assert "differ" in pair.mismatch_reason


def test_comparison_quality_report():
    report = ComparisonQualityReport(
        comparison_id="CMP-20260913-001",
        v0_experiment_id="EXP-20260913-010",
        v1_experiment_id="EXP-20260913-011",
        device_serial="serial-1",
        device_model="Test Model",
        workloads_requested=["startup_01", "cpu_01"],
        workloads_matched=["startup_01", "cpu_01"],
        workloads_mismatched=[],
        iterations_requested=3,
        v0_valid_runs_count=6,
        v1_valid_runs_count=6,
        matched_pairs_count=6,
        unmatched_pairs_count=0,
        evidence_coverage="2/2 workloads have matched V0/V1 evidence",
        is_clean_comparison=True,
        summary_verdict="[TRUSTED_DIFFERENTIAL_EVIDENCE]",
    )
    assert report.is_clean_comparison is True
    assert "2/2" in report.evidence_coverage
    assert report.matched_pairs_count == 6
