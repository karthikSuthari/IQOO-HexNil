"""Tests for Phase 9: Monitor Models."""

import pytest
from hexnil.monitor.models import (
    AnomalyType,
    DeviceOsState,
    MonitoringPhase,
    MonitoringSample,
    MonitoringSession,
    PreUpdateAnomaly,
    PreUpdateAnomalyReport,
    PreUpdateSnapshot,
    TransitionType,
    UpdateTransition,
)


# ── DeviceOsState ──────────────────────────────────────────────────────────

class TestDeviceOsState:
    def test_create_minimal(self):
        state = DeviceOsState(
            build_fingerprint="google/raven/raven:15/AP3A.250101.001/1234567:user/release-keys",
            build_id="AP3A.250101.001",
            android_version="15",
            captured_at="2026-01-01T00:00:00Z",
        )
        assert state.build_fingerprint.startswith("google/raven")
        assert state.build_id == "AP3A.250101.001"
        assert state.android_version == "15"

    def test_create_full(self):
        state = DeviceOsState(
            build_fingerprint="vivo/V2307/V2307:15/AP3A.250305.001/compiler1234:user/release-keys",
            build_id="AP3A.250305.001",
            android_version="15",
            security_patch_level="2025-03-05",
            incremental_build="compiler1234",
            display_build_id="AP3A.250305.001 dev-keys",
            kernel_version="5.15.149",
            baseband_version="1.0.0",
            captured_at="2026-09-14T00:00:00Z",
        )
        assert state.security_patch_level == "2025-03-05"
        assert state.kernel_version == "5.15.149"

    def test_identity_tuple_different_fingerprints(self):
        v0 = DeviceOsState(
            build_fingerprint="fp_v0", build_id="B1", android_version="15",
            security_patch_level="2025-01-01", captured_at="2026-01-01T00:00:00Z",
        )
        v1 = DeviceOsState(
            build_fingerprint="fp_v1", build_id="B1", android_version="15",
            security_patch_level="2025-01-01", captured_at="2026-01-02T00:00:00Z",
        )
        assert v0.identity_tuple() != v1.identity_tuple()

    def test_identity_tuple_same(self):
        v0 = DeviceOsState(
            build_fingerprint="fp_same", build_id="B1", android_version="15",
            security_patch_level="2025-01-01", captured_at="2026-01-01T00:00:00Z",
        )
        v1 = DeviceOsState(
            build_fingerprint="fp_same", build_id="B1", android_version="15",
            security_patch_level="2025-01-01", captured_at="2026-01-02T00:00:00Z",
        )
        assert v0.identity_tuple() == v1.identity_tuple()

    def test_identity_tuple_none_security_patch(self):
        state = DeviceOsState(
            build_fingerprint="fp", build_id="B1", android_version="15",
            captured_at="2026-01-01T00:00:00Z",
        )
        assert state.identity_tuple() == ("fp", "B1", "15", "")


# ── MonitoringSample ───────────────────────────────────────────────────────

class TestMonitoringSample:
    def test_create(self):
        sample = MonitoringSample(
            session_id="MON-0001", sample_index=0,
            timestamp="2026-01-01T00:00:00Z",
            battery_level_percent=85.0,
            battery_charging_state="DISCHARGING",
        )
        assert sample.session_id == "MON-0001"
        assert sample.battery_level_percent == 85.0

    def test_raw_metrics(self):
        sample = MonitoringSample(
            session_id="MON-0001", sample_index=1,
            timestamp="2026-01-01T00:01:00Z",
            raw_metrics={"custom_metric": 42.0},
        )
        assert sample.raw_metrics["custom_metric"] == 42.0


# ── UpdateTransition ──────────────────────────────────────────────────────

class TestUpdateTransition:
    def test_create(self):
        v0 = DeviceOsState(
            build_fingerprint="fp_v0", build_id="B1", android_version="15",
            captured_at="2026-01-01T00:00:00Z",
        )
        v1 = DeviceOsState(
            build_fingerprint="fp_v1", build_id="B2", android_version="15",
            captured_at="2026-01-02T00:00:00Z",
        )
        transition = UpdateTransition(
            v0_state=v0, v1_state=v1,
            transition_type=TransitionType.VENDOR_UPDATE,
            transition_detected_at="2026-01-02T00:00:00Z",
            v0_fingerprint="fp_v0", v1_fingerprint="fp_v1",
            changes=["Build ID: B1 → B2"],
        )
        assert transition.transition_type == TransitionType.VENDOR_UPDATE
        assert len(transition.changes) == 1


# ── MonitoringSession ──────────────────────────────────────────────────────

class TestMonitoringSession:
    def test_create_default_phase(self):
        session = MonitoringSession(
            session_id="MON-0001",
            device_serial="ABC123",
            device_model="iQOO Neo9 Pro",
            created_at="2026-01-01T00:00:00Z",
        )
        assert session.phase == MonitoringPhase.INITIALIZING
        assert session.status == "running"
        assert session.iterations == 3
        assert session.poll_interval_seconds == 60

    def test_phase_transitions(self):
        session = MonitoringSession(
            session_id="MON-0001",
            device_serial="ABC123",
            device_model="Test",
            created_at="2026-01-01T00:00:00Z",
        )
        session.phase = MonitoringPhase.PRE_UPDATE_MONITORING
        assert session.phase == MonitoringPhase.PRE_UPDATE_MONITORING
        session.phase = MonitoringPhase.AWAITING_UPDATE
        assert session.phase == MonitoringPhase.AWAITING_UPDATE
        session.phase = MonitoringPhase.COMPLETED
        assert session.phase == MonitoringPhase.COMPLETED


# ── PreUpdateAnomaly ──────────────────────────────────────────────────────

class TestPreUpdateAnomaly:
    def test_create(self):
        anomaly = PreUpdateAnomaly(
            anomaly_id="ANOM-battery-5",
            anomaly_type=AnomalyType.BATTERY_DRAIN,
            metric_name="battery_level_percent",
            description="Excessive drain at sample 5",
            severity="HIGH",
            detected_at="2026-01-01T00:05:00Z",
            sample_indices=[5],
            baseline_value=80.0,
            observed_value=40.0,
            z_score=3.5,
        )
        assert anomaly.anomaly_type == AnomalyType.BATTERY_DRAIN
        assert anomaly.z_score == 3.5


# ── PreUpdateAnomalyReport ────────────────────────────────────────────────

class TestPreUpdateAnomalyReport:
    def test_empty_report(self):
        report = PreUpdateAnomalyReport(
            session_id="MON-0001",
            device_serial="ABC",
            monitoring_duration_seconds=600.0,
            total_samples=10,
        )
        assert not report.has_pre_existing_issues
        assert len(report.anomalies) == 0

    def test_report_with_anomalies(self):
        anomaly = PreUpdateAnomaly(
            anomaly_id="ANOM-1", anomaly_type=AnomalyType.JANK_SPIKE,
            metric_name="jank_percent",
            description="Jank spike", detected_at="2026-01-01T00:00:00Z",
        )
        report = PreUpdateAnomalyReport(
            session_id="MON-0001", device_serial="ABC",
            monitoring_duration_seconds=600.0, total_samples=10,
            anomalies=[anomaly], has_pre_existing_issues=True,
        )
        assert report.has_pre_existing_issues
        assert len(report.anomalies) == 1


# ── PreUpdateSnapshot ─────────────────────────────────────────────────────

class TestPreUpdateSnapshot:
    def test_create(self):
        state = DeviceOsState(
            build_fingerprint="fp", build_id="B1", android_version="15",
            captured_at="2026-01-01T00:00:00Z",
        )
        snapshot = PreUpdateSnapshot(
            session_id="MON-0001", device_serial="ABC",
            os_state=state, frozen_at="2026-01-01T00:10:00Z",
        )
        assert snapshot.os_state.build_id == "B1"
        assert snapshot.baseline_experiment_id is None


# ── Enums ──────────────────────────────────────────────────────────────────

class TestEnums:
    def test_monitoring_phase_values(self):
        assert MonitoringPhase.INITIALIZING.value == "INITIALIZING"
        assert MonitoringPhase.COMPLETED.value == "COMPLETED"
        assert MonitoringPhase.FAILED.value == "FAILED"

    def test_transition_type_values(self):
        assert TransitionType.OS_MAJOR_UPDATE.value == "OS_MAJOR_UPDATE"
        assert TransitionType.SECURITY_PATCH.value == "SECURITY_PATCH"

    def test_anomaly_type_values(self):
        assert AnomalyType.BATTERY_DRAIN.value == "BATTERY_DRAIN"
        assert AnomalyType.MEMORY_LEAK.value == "MEMORY_LEAK"
