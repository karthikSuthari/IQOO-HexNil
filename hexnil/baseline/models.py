"""Domain models for Phase 4: V0 Baseline Experiment."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class EnvironmentConditionStatus(str, Enum):
    """Classification of an environment condition snapshot field."""

    MEASURED = "measured"
    CONTROLLED = "controlled"
    VERIFIED = "verified"
    UNSUPPORTED = "unsupported"


class V0SoftwareIdentity(BaseModel):
    """Exact software and build identity of the V0 baseline build."""

    package: str = "com.example.iqoo_hexnil"
    version_name: Optional[str] = None
    version_code: Optional[int] = None
    apk_path: Optional[str] = None
    apk_sha256: Optional[str] = None
    android_os_version: Optional[str] = None
    build_id: Optional[str] = None
    build_fingerprint: Optional[str] = None
    captured_at: str
    software_type: str = "V0_ORIGINAL"

    model_config = ConfigDict(extra="ignore")


class EnvironmentSnapshot(BaseModel):
    """Environmental state captured before or during the baseline experiment."""

    timestamp: str
    battery_level_percent: Optional[float] = None
    battery_charging_state: Optional[str] = None
    battery_temperature_c: Optional[float] = None
    screen_on: Optional[bool] = None
    screen_brightness: Optional[int] = None
    thermal_status: Optional[str] = None
    wifi_enabled: Optional[bool] = None
    wifi_connected: Optional[bool] = None
    device_idle_state: Optional[str] = None
    orientation: Optional[str] = None
    app_running: Optional[bool] = None
    condition_status: Dict[str, EnvironmentConditionStatus] = Field(default_factory=dict)

    model_config = ConfigDict(extra="ignore")


class StabilizationPolicy(BaseModel):
    """Configurable pre-run device stabilization policy."""

    wake_screen: bool = True
    enforce_battery_min: int = 15
    enforce_charging_state: str = "any"  # 'any', 'charging', 'discharging'
    max_thermal_level: str = "moderate"  # 'none', 'light', 'moderate', 'severe'
    force_stop_app_before: bool = True
    stabilization_cooldown_seconds: float = 2.0

    model_config = ConfigDict(extra="ignore")


class StabilizationResult(BaseModel):
    """Outcome of attempting pre-run device stabilization."""

    attempted_actions: List[str] = Field(default_factory=list)
    verified_conditions: Dict[str, bool] = Field(default_factory=dict)
    limitations: List[str] = Field(default_factory=list)
    success: bool = True

    model_config = ConfigDict(extra="ignore")


class BaselineRunMetric(BaseModel):
    """Individual extracted metric value for a specific workload run."""

    metric_name: str
    value: Optional[float] = None
    unit: Optional[str] = None
    is_outlier: bool = False
    outlier_reason: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


class BaselineMetricSummary(BaseModel):
    """Statistical summary of a metric computed from valid workload runs."""

    workload_id: str
    metric_name: str
    unit: Optional[str] = None
    n_valid_runs: int
    n_excluded_runs: int = 0
    mean: Optional[float] = None
    median: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    std_dev: Optional[float] = None
    variance: Optional[float] = None
    p25: Optional[float] = None
    p75: Optional[float] = None
    iqr: Optional[float] = None
    coefficient_of_variation: Optional[float] = None
    run_values: List[float] = Field(default_factory=list)
    outliers_detected: int = 0

    model_config = ConfigDict(extra="ignore")


class UncertaintyEstimate(BaseModel):
    """Quantified uncertainty and confidence interval for a baseline metric."""

    workload_id: str
    metric_name: str
    sample_size: int
    standard_error: Optional[float] = None
    ci_lower: Optional[float] = None
    ci_upper: Optional[float] = None
    confidence_level: float = 0.95
    method: str  # 'student_t', 'normal', 'inconclusive'
    uncertainty_status: str  # 'ESTIMATED', 'INCONCLUSIVE'
    explanation: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


class QualityReport(BaseModel):
    """Machine- and human-readable baseline quality summary."""

    experiment_id: str
    baseline_type: str = "V0"
    device_serial: str
    device_model: str
    v0_software: Dict[str, Any] = Field(default_factory=dict)
    workloads_requested: List[str] = Field(default_factory=list)
    iterations_requested_per_workload: int = 1
    total_iterations_requested: int = 1
    total_runs_completed: int = 0
    valid_runs_count: int = 0
    invalid_runs_count: int = 0
    failed_runs_count: int = 0
    precondition_failures_count: int = 0
    telemetry_records_count: int = 0
    artifacts_count: int = 0
    evidence_coverage: str = ""  # e.g. "5/5 workloads validated"
    contamination_flags: List[str] = Field(default_factory=list)
    is_clean_baseline: bool = True
    summary_verdict: str = "TRUSTED_V0_BASELINE"  # 'TRUSTED_V0_BASELINE', 'CONTAMINATED_BASELINE', 'INSUFFICIENT_DATA'

    model_config = ConfigDict(extra="ignore")


class WorkloadProvenance(BaseModel):
    """Provenance tracking for a single workload within an experiment."""

    workload_id: str
    workload_version: str
    configuration_hash: str
    run_ids: List[str] = Field(default_factory=list)
    valid_run_ids: List[str] = Field(default_factory=list)
    telemetry_files: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")


class ProvenanceRecord(BaseModel):
    """Immutable provenance record linking derived metrics back to source evidence."""

    experiment_id: str
    analysis_version: str = "1.0.0"
    created_at: str
    device_serial: str
    build_fingerprint: str
    apk_sha256: Optional[str] = None
    workloads: Dict[str, WorkloadProvenance] = Field(default_factory=dict)
    artifact_hashes: Dict[str, str] = Field(default_factory=dict)

    model_config = ConfigDict(extra="ignore")
