"""Metric direction, units, and eligibility registry for release validation."""

from typing import Dict, List, Optional
from pydantic import BaseModel

from hexnil.stats.models import MetricDirection


class MetricMetadata(BaseModel):
    """Metadata describing interpretation and unit of a measured metric."""

    metric_name: str
    workload_id: str
    unit: str
    direction: MetricDirection
    description: str


# Versioned registry of known metrics across Hexnil workloads
METRIC_REGISTRY: Dict[str, MetricMetadata] = {
    # 1. Universal duration (all workloads)
    "workload_duration_ms": MetricMetadata(
        metric_name="workload_duration_ms",
        workload_id="universal",
        unit="ms",
        direction=MetricDirection.LOWER_IS_BETTER,
        description="Overall monotonic duration of workload execution from start to finish.",
    ),
    # 2. startup_01
    "startup_duration_ms": MetricMetadata(
        metric_name="startup_duration_ms",
        workload_id="startup_01",
        unit="ms",
        direction=MetricDirection.LOWER_IS_BETTER,
        description="Cold application process launch and initial frame rendering latency.",
    ),
    # 3. cpu_01
    "compute_duration_ms": MetricMetadata(
        metric_name="compute_duration_ms",
        workload_id="cpu_01",
        unit="ms",
        direction=MetricDirection.LOWER_IS_BETTER,
        description="Deterministic CPU-bound SHA-256 compute step duration.",
    ),
    # 4. memory_01
    "app_heap_allocated_mb": MetricMetadata(
        metric_name="app_heap_allocated_mb",
        workload_id="memory_01",
        unit="MB",
        direction=MetricDirection.LOWER_IS_BETTER,
        description="Application Dalvik/ART runtime allocated heap memory.",
    ),
    "device_memory_available_mb": MetricMetadata(
        metric_name="device_memory_available_mb",
        workload_id="memory_01",
        unit="MB",
        direction=MetricDirection.HIGHER_IS_BETTER,
        description="Total system free and available physical RAM on the device.",
    ),
    # 5. scroll_01
    "scroll_duration_ms": MetricMetadata(
        metric_name="scroll_duration_ms",
        workload_id="scroll_01",
        unit="ms",
        direction=MetricDirection.LOWER_IS_BETTER,
        description="Monotonic execution time of fixed-distance programmatic UI scroll gestures.",
    ),
    "ui_frame_jank_percent": MetricMetadata(
        metric_name="ui_frame_jank_percent",
        workload_id="scroll_01",
        unit="%",
        direction=MetricDirection.LOWER_IS_BETTER,
        description="Percentage of UI frame presentations exceeding standard vsync deadlines.",
    ),
    # 6. video_power_01
    "playback_duration_ms": MetricMetadata(
        metric_name="playback_duration_ms",
        workload_id="video_power_01",
        unit="ms",
        direction=MetricDirection.LOWER_IS_BETTER,
        description="Duration of local video player playback step.",
    ),
    "battery_discharge_proxy": MetricMetadata(
        metric_name="battery_discharge_proxy",
        workload_id="video_power_01",
        unit="delta_percent_proxy",
        direction=MetricDirection.LOWER_IS_BETTER,
        description="Battery percentage level drop observed across workload execution (proxy for drain).",
    ),
}


def get_metric_metadata(metric_name: str) -> Optional[MetricMetadata]:
    """Retrieve metadata for a registered metric."""
    return METRIC_REGISTRY.get(metric_name)


def get_metric_direction(metric_name: str) -> MetricDirection:
    """Determine whether lower or higher values indicate improvement."""
    meta = METRIC_REGISTRY.get(metric_name)
    if meta:
        return meta.direction
    return MetricDirection.UNKNOWN


def get_registered_metrics_for_workload(workload_id: str) -> List[MetricMetadata]:
    """Retrieve all metrics applicable to a specific workload ID (including universal)."""
    return [
        m for m in METRIC_REGISTRY.values()
        if m.workload_id in (workload_id, "universal")
    ]
