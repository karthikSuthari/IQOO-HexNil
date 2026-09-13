"""Versioned engineering thresholds and severity bands."""

from typing import Dict, Optional

from hexnil.stats.models import EngineeringThreshold, Severity

CURRENT_THRESHOLD_VERSION = "1.0.0"

# Default versioned thresholds by metric name
DEFAULT_THRESHOLDS: Dict[str, EngineeringThreshold] = {
    # 1. Workload Durations (5% minimum meaningful change)
    "workload_duration_ms": EngineeringThreshold(
        threshold_type="percent",
        meaningful_change_percent=5.0,
        severity_bands={
            Severity.LOW.value: 5.0,
            Severity.MEDIUM.value: 10.0,
            Severity.HIGH.value: 20.0,
            Severity.CRITICAL.value: 40.0,
        },
        version=CURRENT_THRESHOLD_VERSION,
    ),
    "startup_duration_ms": EngineeringThreshold(
        threshold_type="percent",
        meaningful_change_percent=5.0,
        severity_bands={
            Severity.LOW.value: 5.0,
            Severity.MEDIUM.value: 10.0,
            Severity.HIGH.value: 20.0,
            Severity.CRITICAL.value: 40.0,
        },
        version=CURRENT_THRESHOLD_VERSION,
    ),
    "compute_duration_ms": EngineeringThreshold(
        threshold_type="percent",
        meaningful_change_percent=5.0,
        severity_bands={
            Severity.LOW.value: 5.0,
            Severity.MEDIUM.value: 10.0,
            Severity.HIGH.value: 20.0,
            Severity.CRITICAL.value: 40.0,
        },
        version=CURRENT_THRESHOLD_VERSION,
    ),
    "scroll_duration_ms": EngineeringThreshold(
        threshold_type="percent",
        meaningful_change_percent=5.0,
        severity_bands={
            Severity.LOW.value: 5.0,
            Severity.MEDIUM.value: 10.0,
            Severity.HIGH.value: 20.0,
            Severity.CRITICAL.value: 40.0,
        },
        version=CURRENT_THRESHOLD_VERSION,
    ),
    "playback_duration_ms": EngineeringThreshold(
        threshold_type="percent",
        meaningful_change_percent=5.0,
        severity_bands={
            Severity.LOW.value: 5.0,
            Severity.MEDIUM.value: 10.0,
            Severity.HIGH.value: 20.0,
            Severity.CRITICAL.value: 40.0,
        },
        version=CURRENT_THRESHOLD_VERSION,
    ),
    # 2. Memory (5% minimum meaningful change)
    "app_heap_allocated_mb": EngineeringThreshold(
        threshold_type="percent",
        meaningful_change_percent=5.0,
        severity_bands={
            Severity.LOW.value: 5.0,
            Severity.MEDIUM.value: 10.0,
            Severity.HIGH.value: 20.0,
            Severity.CRITICAL.value: 35.0,
        },
        version=CURRENT_THRESHOLD_VERSION,
    ),
    "device_memory_available_mb": EngineeringThreshold(
        threshold_type="percent",
        meaningful_change_percent=5.0,
        severity_bands={
            Severity.LOW.value: 5.0,
            Severity.MEDIUM.value: 10.0,
            Severity.HIGH.value: 20.0,
            Severity.CRITICAL.value: 35.0,
        },
        version=CURRENT_THRESHOLD_VERSION,
    ),
    # 3. Jank (2% absolute jank change)
    "ui_frame_jank_percent": EngineeringThreshold(
        threshold_type="absolute",
        meaningful_change_absolute=2.0,
        severity_bands={
            Severity.LOW.value: 2.0,
            Severity.MEDIUM.value: 5.0,
            Severity.HIGH.value: 10.0,
            Severity.CRITICAL.value: 20.0,
        },
        version=CURRENT_THRESHOLD_VERSION,
    ),
    # 4. Battery drain (1.0% absolute discharge level drop)
    "battery_discharge_proxy": EngineeringThreshold(
        threshold_type="absolute",
        meaningful_change_absolute=1.0,
        severity_bands={
            Severity.LOW.value: 1.0,
            Severity.MEDIUM.value: 2.0,
            Severity.HIGH.value: 4.0,
            Severity.CRITICAL.value: 8.0,
        },
        version=CURRENT_THRESHOLD_VERSION,
    ),
}

# Generic fallback threshold for unspecified metrics
FALLBACK_THRESHOLD = EngineeringThreshold(
    threshold_type="percent",
    meaningful_change_percent=5.0,
    severity_bands={
        Severity.LOW.value: 5.0,
        Severity.MEDIUM.value: 10.0,
        Severity.HIGH.value: 20.0,
        Severity.CRITICAL.value: 40.0,
    },
    version=CURRENT_THRESHOLD_VERSION,
)


def get_threshold_for_metric(metric_name: str) -> EngineeringThreshold:
    """Retrieve predeclared engineering threshold for a given metric."""
    return DEFAULT_THRESHOLDS.get(metric_name, FALLBACK_THRESHOLD)
