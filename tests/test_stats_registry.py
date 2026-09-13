"""Unit tests for Phase 6 metric registry."""

from hexnil.stats.models import MetricDirection
from hexnil.stats.registry import (
    METRIC_REGISTRY,
    get_metric_direction,
    get_metric_metadata,
    get_registered_metrics_for_workload,
)


def test_metric_registry_coverage():
    assert "workload_duration_ms" in METRIC_REGISTRY
    assert "startup_duration_ms" in METRIC_REGISTRY
    assert "compute_duration_ms" in METRIC_REGISTRY
    assert "app_heap_allocated_mb" in METRIC_REGISTRY
    assert "device_memory_available_mb" in METRIC_REGISTRY
    assert "scroll_duration_ms" in METRIC_REGISTRY
    assert "ui_frame_jank_percent" in METRIC_REGISTRY
    assert "playback_duration_ms" in METRIC_REGISTRY
    assert "battery_discharge_proxy" in METRIC_REGISTRY


def test_metric_directions():
    # LOWER_IS_BETTER
    assert get_metric_direction("startup_duration_ms") == MetricDirection.LOWER_IS_BETTER
    assert get_metric_direction("compute_duration_ms") == MetricDirection.LOWER_IS_BETTER
    assert get_metric_direction("app_heap_allocated_mb") == MetricDirection.LOWER_IS_BETTER
    assert get_metric_direction("ui_frame_jank_percent") == MetricDirection.LOWER_IS_BETTER
    assert get_metric_direction("battery_discharge_proxy") == MetricDirection.LOWER_IS_BETTER

    # HIGHER_IS_BETTER
    assert get_metric_direction("device_memory_available_mb") == MetricDirection.HIGHER_IS_BETTER

    # UNKNOWN fallback
    assert get_metric_direction("some_random_unregistered_metric") == MetricDirection.UNKNOWN


def test_registered_metrics_for_workload():
    startup_metrics = get_registered_metrics_for_workload("startup_01")
    names = [m.metric_name for m in startup_metrics]
    assert "startup_duration_ms" in names

    cpu_metrics = get_registered_metrics_for_workload("cpu_01")
    names = [m.metric_name for m in cpu_metrics]
    assert "compute_duration_ms" in names

    memory_metrics = get_registered_metrics_for_workload("memory_01")
    names = [m.metric_name for m in memory_metrics]
    assert "app_heap_allocated_mb" in names
    assert "device_memory_available_mb" in names


def test_get_metric_metadata():
    meta = get_metric_metadata("compute_duration_ms")
    assert meta is not None
    assert meta.unit == "ms"
    assert meta.direction == MetricDirection.LOWER_IS_BETTER
