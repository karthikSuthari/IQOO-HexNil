"""Domain models for Phase 9: Continuous Monitoring & Update Detection."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class MonitoringPhase(str, Enum):
    """Current phase of the monitoring lifecycle."""

    INITIALIZING = "INITIALIZING"
    PRE_UPDATE_MONITORING = "PRE_UPDATE_MONITORING"
    BASELINE_COLLECTION = "BASELINE_COLLECTION"
    AWAITING_UPDATE = "AWAITING_UPDATE"
    UPDATE_DETECTED = "UPDATE_DETECTED"
    POST_UPDATE_STABILIZATION = "POST_UPDATE_STABILIZATION"
    POST_UPDATE_VALIDATION = "POST_UPDATE_VALIDATION"
    ANALYSIS_IN_PROGRESS = "ANALYSIS_IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TransitionType(str, Enum):
    """Classification of what changed during the OS transition."""

    OS_MAJOR_UPDATE = "OS_MAJOR_UPDATE"
    OS_MINOR_UPDATE = "OS_MINOR_UPDATE"
    SECURITY_PATCH = "SECURITY_PATCH"
    BUILD_CHANGE = "BUILD_CHANGE"
    VENDOR_UPDATE = "VENDOR_UPDATE"
    UNKNOWN = "UNKNOWN"


class AnomalyType(str, Enum):
    """Classification of pre-update anomalies detected during monitoring."""

    BATTERY_DRAIN = "BATTERY_DRAIN"
    THERMAL_THROTTLE = "THERMAL_THROTTLE"
    JANK_SPIKE = "JANK_SPIKE"
    MEMORY_LEAK = "MEMORY_LEAK"
    STARTUP_DEGRADATION = "STARTUP_DEGRADATION"
    CPU_SPIKE = "CPU_SPIKE"
    METRIC_DRIFT = "METRIC_DRIFT"


class DeviceOsState(BaseModel):
    """Complete snapshot of device OS/software identity at a point in time."""

    build_fingerprint: str
    build_id: str
    android_version: str
    security_patch_level: Optional[str] = None
    incremental_build: Optional[str] = None
    display_build_id: Optional[str] = None
    kernel_version: Optional[str] = None
    baseband_version: Optional[str] = None
    captured_at: str

    model_config = ConfigDict(extra="ignore")

    def identity_tuple(self) -> tuple:
        """Return the key identity fields used for update detection."""
        return (
            self.build_fingerprint,
            self.build_id,
            self.android_version,
            self.security_patch_level or "",
        )


class MonitoringSample(BaseModel):
    """Single timestamped telemetry/health sample during continuous monitoring."""

    session_id: str
    sample_index: int
    timestamp: str
    battery_level_percent: Optional[float] = None
    battery_charging_state: Optional[str] = None
    thermal_status: Optional[str] = None
    cpu_temperature_celsius: Optional[float] = None
    memory_available_mb: Optional[float] = None
    app_heap_mb: Optional[float] = None
    jank_percent: Optional[float] = None
    os_state: Optional[DeviceOsState] = None
    raw_metrics: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="ignore")


class PreUpdateAnomaly(BaseModel):
    """A detected anomaly in the pre-update monitoring window."""

    anomaly_id: str
    anomaly_type: AnomalyType
    metric_name: str
    description: str
    severity: str = "LOW"  # LOW, MEDIUM, HIGH
    detected_at: str
    sample_indices: List[int] = Field(default_factory=list)
    baseline_value: Optional[float] = None
    observed_value: Optional[float] = None
    z_score: Optional[float] = None

    model_config = ConfigDict(extra="ignore")


class PreUpdateAnomalyReport(BaseModel):
    """Aggregated report of all pre-update anomalies detected during monitoring."""

    session_id: str
    device_serial: str
    monitoring_duration_seconds: float
    total_samples: int
    anomalies: List[PreUpdateAnomaly] = Field(default_factory=list)
    has_pre_existing_issues: bool = False
    summary: str = ""

    model_config = ConfigDict(extra="ignore")


class UpdateTransition(BaseModel):
    """Detected V0 → V1 OS transition record."""

    v0_state: DeviceOsState
    v1_state: DeviceOsState
    transition_type: TransitionType
    transition_detected_at: str
    v0_fingerprint: str
    v1_fingerprint: str
    changes: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")


class PreUpdateSnapshot(BaseModel):
    """Aggregated V0 state: baseline evidence, anomalies, and predictions frozen before update."""

    session_id: str
    device_serial: str
    os_state: DeviceOsState
    baseline_experiment_id: Optional[str] = None
    anomaly_report: Optional[PreUpdateAnomalyReport] = None
    prediction_plan_id: Optional[str] = None
    frozen_at: str

    model_config = ConfigDict(extra="ignore")


class MonitoringSession(BaseModel):
    """Top-level session record for an end-to-end monitoring lifecycle."""

    session_id: str
    device_serial: str
    device_model: str
    created_at: str
    phase: MonitoringPhase = MonitoringPhase.INITIALIZING
    status: str = "running"

    # OS state tracking
    v0_os_state: Optional[DeviceOsState] = None
    v1_os_state: Optional[DeviceOsState] = None
    update_transition: Optional[UpdateTransition] = None

    # Phase references
    baseline_experiment_id: Optional[str] = None
    comparison_id: Optional[str] = None
    analysis_id: Optional[str] = None
    prediction_plan_id: Optional[str] = None
    report_id: Optional[str] = None

    # Pre-update evidence
    pre_update_snapshot: Optional[PreUpdateSnapshot] = None
    anomaly_report: Optional[PreUpdateAnomalyReport] = None

    # Configuration
    poll_interval_seconds: int = 60
    iterations: int = 3
    workload_suite: List[str] = Field(default_factory=list)
    release_notes_path: Optional[str] = None

    # Lifecycle tracking
    monitoring_started_at: Optional[str] = None
    update_detected_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None

    model_config = ConfigDict(extra="ignore")
