"""Tests for Phase 12: Report Models."""

import pytest
from hexnil.report.models import FinalEvidenceReport
from hexnil.monitor.models import DeviceOsState, UpdateTransition, TransitionType


class TestFinalEvidenceReport:
    def _make_report(self, **kwargs):
        defaults = dict(
            report_id="RPT-MON-0001",
            session_id="MON-0001",
            created_at="2026-01-01T00:00:00Z",
            device_serial="ABC123",
            device_model="iQOO Neo9 Pro",
            pre_update_os_state=DeviceOsState(
                build_fingerprint="fp_v0",
                build_id="B1",
                android_version="15",
                captured_at="2026-01-01T00:00:00Z",
            ),
        )
        defaults.update(kwargs)
        return FinalEvidenceReport(**defaults)

    def test_create_minimal(self):
        report = self._make_report()
        assert report.report_id == "RPT-MON-0001"
        assert report.device_model == "iQOO Neo9 Pro"
        assert report.overall_verdict == ""

    def test_pre_update_state(self):
        report = self._make_report()
        assert report.pre_update_os_state.android_version == "15"
        assert report.pre_update_os_state.build_id == "B1"

    def test_with_transition(self):
        v0 = DeviceOsState(
            build_fingerprint="fp_v0", build_id="B1",
            android_version="15", captured_at="2026-01-01T00:00:00Z",
        )
        v1 = DeviceOsState(
            build_fingerprint="fp_v1", build_id="B2",
            android_version="15", captured_at="2026-01-02T00:00:00Z",
        )
        transition = UpdateTransition(
            v0_state=v0, v1_state=v1,
            transition_type=TransitionType.VENDOR_UPDATE,
            transition_detected_at="2026-01-02T00:00:00Z",
            v0_fingerprint="fp_v0", v1_fingerprint="fp_v1",
            changes=["Build ID: B1 → B2"],
        )
        report = self._make_report(
            update_transition=transition,
            post_update_os_state=v1,
        )
        assert report.update_transition.transition_type == TransitionType.VENDOR_UPDATE
        assert report.post_update_os_state.build_id == "B2"

    def test_with_verdict(self):
        report = self._make_report(
            overall_verdict="UPDATE_SAFE",
            executive_summary="All metrics stable.",
        )
        assert report.overall_verdict == "UPDATE_SAFE"

    def test_with_regressions(self):
        report = self._make_report(
            overall_verdict="UPDATE_HAS_REGRESSIONS",
            recommendations=["Investigate battery drain regression."],
        )
        assert report.overall_verdict == "UPDATE_HAS_REGRESSIONS"
        assert len(report.recommendations) == 1

    def test_empty_lists_default(self):
        report = self._make_report()
        assert report.pre_update_anomalies == []
        assert report.post_update_changes == []
        assert report.fixed_issues == []
        assert report.persisted_issues == []
        assert report.new_regressions == []
        assert report.insufficient_evidence_items == []
        assert report.recommendations == []

    def test_serialization_round_trip(self):
        report = self._make_report(overall_verdict="UPDATE_SAFE")
        json_str = report.model_dump_json()
        loaded = FinalEvidenceReport.model_validate_json(json_str)
        assert loaded.report_id == report.report_id
        assert loaded.overall_verdict == "UPDATE_SAFE"
