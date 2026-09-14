"""Tests for Phase 9: Device State Tracker."""

import pytest
from unittest.mock import MagicMock

from hexnil.monitor.models import DeviceOsState, TransitionType
from hexnil.monitor.state_tracker import DeviceStateTracker


def _make_state(
    fingerprint="fp1", build_id="B1", android="15",
    security_patch="2025-01-01", incremental="12345",
    kernel=None, baseband=None,
):
    return DeviceOsState(
        build_fingerprint=fingerprint, build_id=build_id,
        android_version=android, security_patch_level=security_patch,
        incremental_build=incremental, kernel_version=kernel,
        baseband_version=baseband, captured_at="2026-01-01T00:00:00Z",
    )


class TestDeviceStateTracker:
    def setup_method(self):
        self.mock_adb = MagicMock()
        self.tracker = DeviceStateTracker(self.mock_adb)

    def test_capture_os_state(self):
        self.mock_adb.get_all_props.return_value = {
            "ro.build.fingerprint": "vivo/iQOO:15/AP3A/1234:user/release-keys",
            "ro.build.id": "AP3A.250101.001",
            "ro.build.version.release": "15",
            "ro.build.version.security_patch": "2025-01-01",
            "ro.build.version.incremental": "1234",
            "ro.build.display.id": "AP3A.250101.001",
        }
        state = self.tracker.capture_os_state("serial123")
        assert state.build_id == "AP3A.250101.001"
        assert state.android_version == "15"
        assert state.security_patch_level == "2025-01-01"

    def test_has_update_occurred_no_change(self):
        v0 = _make_state()
        current = _make_state()
        assert not self.tracker.has_update_occurred(v0, current)

    def test_has_update_occurred_fingerprint_changed(self):
        v0 = _make_state(fingerprint="fp_old")
        current = _make_state(fingerprint="fp_new")
        assert self.tracker.has_update_occurred(v0, current)

    def test_has_update_occurred_build_id_changed(self):
        v0 = _make_state(build_id="B1")
        current = _make_state(build_id="B2")
        assert self.tracker.has_update_occurred(v0, current)

    def test_has_update_occurred_security_patch_changed(self):
        v0 = _make_state(security_patch="2025-01-01")
        current = _make_state(security_patch="2025-03-01")
        assert self.tracker.has_update_occurred(v0, current)

    def test_classify_transition_major_update(self):
        v0 = _make_state(android="14")
        v1 = _make_state(android="15")
        assert self.tracker.classify_transition(v0, v1) == TransitionType.OS_MAJOR_UPDATE

    def test_classify_transition_minor_update(self):
        v0 = _make_state(android="15.0")
        v1 = _make_state(android="15.1")
        assert self.tracker.classify_transition(v0, v1) == TransitionType.OS_MINOR_UPDATE

    def test_classify_transition_security_patch(self):
        v0 = _make_state(security_patch="2025-01-01", build_id="B1")
        v1 = _make_state(security_patch="2025-03-01", build_id="B1")
        assert self.tracker.classify_transition(v0, v1) == TransitionType.SECURITY_PATCH

    def test_classify_transition_vendor_update(self):
        v0 = _make_state(build_id="B1")
        v1 = _make_state(build_id="B2")
        assert self.tracker.classify_transition(v0, v1) == TransitionType.VENDOR_UPDATE

    def test_classify_transition_build_change(self):
        v0 = _make_state(fingerprint="fp1", build_id="B1", security_patch="2025-01-01")
        v1 = _make_state(fingerprint="fp2", build_id="B1", security_patch="2025-01-01")
        assert self.tracker.classify_transition(v0, v1) == TransitionType.BUILD_CHANGE

    def test_classify_transition_unknown(self):
        v0 = _make_state()
        v1 = _make_state()
        assert self.tracker.classify_transition(v0, v1) == TransitionType.UNKNOWN

    def test_detect_changes_multiple(self):
        v0 = _make_state(fingerprint="fp1", build_id="B1", android="14", security_patch="2025-01-01")
        v1 = _make_state(fingerprint="fp2", build_id="B2", android="15", security_patch="2025-06-01")
        changes = self.tracker.detect_changes(v0, v1)
        assert len(changes) == 4
        assert any("Build fingerprint" in c for c in changes)
        assert any("Build ID" in c for c in changes)
        assert any("Android version" in c for c in changes)
        assert any("Security patch" in c for c in changes)

    def test_detect_changes_none(self):
        v0 = _make_state()
        v1 = _make_state()
        changes = self.tracker.detect_changes(v0, v1)
        assert len(changes) == 0

    def test_create_transition_record(self):
        v0 = _make_state(fingerprint="fp1", build_id="B1")
        v1 = _make_state(fingerprint="fp2", build_id="B2")
        transition = self.tracker.create_transition_record(v0, v1)
        assert transition.v0_fingerprint == "fp1"
        assert transition.v1_fingerprint == "fp2"
        assert transition.transition_type == TransitionType.VENDOR_UPDATE
        assert len(transition.changes) > 0
