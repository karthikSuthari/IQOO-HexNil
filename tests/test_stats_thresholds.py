"""Unit tests for Phase 6 engineering threshold definitions and lookup."""

from hexnil.stats.models import MetricDirection
from hexnil.stats.thresholds import (
    CURRENT_THRESHOLD_VERSION,
    DEFAULT_THRESHOLDS,
    get_threshold_for_metric,
)


def test_current_threshold_version():
    assert CURRENT_THRESHOLD_VERSION == "1.0.0"


def test_default_thresholds_contain_core_metrics():
    assert "startup_duration_ms" in DEFAULT_THRESHOLDS
    assert "compute_duration_ms" in DEFAULT_THRESHOLDS
    assert "app_heap_allocated_mb" in DEFAULT_THRESHOLDS
    assert "device_memory_available_mb" in DEFAULT_THRESHOLDS
    assert "scroll_duration_ms" in DEFAULT_THRESHOLDS
    assert "ui_frame_jank_percent" in DEFAULT_THRESHOLDS
    assert "battery_discharge_proxy" in DEFAULT_THRESHOLDS


def test_get_threshold_for_registered_metric():
    t = get_threshold_for_metric("startup_duration_ms")
    assert t.meaningful_change_percent == 5.0
    assert t.severity_bands["CRITICAL"] == 40.0


def test_get_threshold_for_absolute_metric():
    t = get_threshold_for_metric("battery_discharge_proxy")
    assert t.meaningful_change_absolute == 1.0


def test_get_threshold_for_unknown_metric():
    t = get_threshold_for_metric("unknown_custom_metric")
    assert t.meaningful_change_percent == 5.0
    assert t.threshold_type == "percent"
