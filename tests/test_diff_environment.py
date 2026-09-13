"""Unit tests for environment comparison and drift detection."""

import pytest
from hexnil.baseline.models import EnvironmentSnapshot
from hexnil.diff.environment import compare_environment_snapshots
from hexnil.diff.models import EnvironmentMatchStatus


def test_compare_environment_identical():
    snap0 = EnvironmentSnapshot(
        timestamp="2026-09-13T10:00:00Z",
        battery_level_percent=60.0,
        battery_charging_state="DISCHARGING",
        screen_on=True,
        thermal_status="NONE",
        wifi_enabled=True,
        device_idle_state="ACTIVE",
    )
    snap1 = EnvironmentSnapshot(
        timestamp="2026-09-13T11:00:00Z",
        battery_level_percent=59.0,
        battery_charging_state="DISCHARGING",
        screen_on=True,
        thermal_status="NONE",
        wifi_enabled=True,
        device_idle_state="ACTIVE",
    )

    comp = compare_environment_snapshots(snap0, snap1)
    assert comp.battery_level_delta_percent == 1.0
    assert comp.condition_match_statuses["battery_level"] == EnvironmentMatchStatus.MATCHED
    assert comp.condition_match_statuses["charging_state"] == EnvironmentMatchStatus.MATCHED
    assert comp.condition_match_statuses["screen_state"] == EnvironmentMatchStatus.MATCHED
    assert comp.condition_match_statuses["thermal_status"] == EnvironmentMatchStatus.MATCHED
    assert comp.condition_match_statuses["wifi_enabled"] == EnvironmentMatchStatus.MATCHED
    assert comp.thermal_status_transition == "NONE -> NONE"
    assert len(comp.drift_summary) == 0


def test_compare_environment_drift():
    snap0 = EnvironmentSnapshot(
        timestamp="2026-09-13T10:00:00Z",
        battery_level_percent=70.0,
        battery_charging_state="DISCHARGING",
        screen_on=True,
        thermal_status="NONE",
        wifi_enabled=True,
    )
    snap1 = EnvironmentSnapshot(
        timestamp="2026-09-13T11:00:00Z",
        battery_level_percent=55.0,  # Delta = 15% (>5%)
        battery_charging_state="CHARGING",
        screen_on=False,
        thermal_status="MODERATE",
        wifi_enabled=False,
    )

    comp = compare_environment_snapshots(snap0, snap1)
    assert comp.battery_level_delta_percent == 15.0
    assert comp.condition_match_statuses["battery_level"] == EnvironmentMatchStatus.CHANGED
    assert comp.condition_match_statuses["charging_state"] == EnvironmentMatchStatus.CHANGED
    assert comp.condition_match_statuses["screen_state"] == EnvironmentMatchStatus.CHANGED
    assert comp.condition_match_statuses["thermal_status"] == EnvironmentMatchStatus.CHANGED
    assert comp.condition_match_statuses["wifi_enabled"] == EnvironmentMatchStatus.CHANGED
    assert comp.thermal_status_transition == "NONE -> MODERATE"
    assert len(comp.drift_summary) >= 4


def test_compare_environment_unsupported():
    snap0 = EnvironmentSnapshot(timestamp="2026-09-13T10:00:00Z")
    snap1 = EnvironmentSnapshot(timestamp="2026-09-13T11:00:00Z")

    comp = compare_environment_snapshots(snap0, snap1)
    assert comp.battery_level_delta_percent is None
    assert comp.condition_match_statuses["battery_level"] == EnvironmentMatchStatus.UNSUPPORTED
    assert comp.condition_match_statuses["charging_state"] == EnvironmentMatchStatus.UNKNOWN
    assert comp.condition_match_statuses["thermal_status"] == EnvironmentMatchStatus.UNSUPPORTED
