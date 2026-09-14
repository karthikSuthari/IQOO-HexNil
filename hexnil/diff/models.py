"""Domain models for Phase 5: V0 -> V1 Differential Experiment."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from hexnil.baseline.models import EnvironmentSnapshot, V0SoftwareIdentity
from hexnil.device.models import DeviceMetadata


class InstallOutcome(str, Enum):
    """Classification of APK or OS update installation outcomes."""

    SUCCESS = "SUCCESS"
    SUCCESS_OS_UPDATE = "SUCCESS_OS_UPDATE"
    INSTALL_FAILED_ALREADY_EXISTS = "INSTALL_FAILED_ALREADY_EXISTS"
    INSTALL_FAILED_INVALID_APK = "INSTALL_FAILED_INVALID_APK"
    INSTALL_FAILED_VERSION_DOWNGRADE = "INSTALL_FAILED_VERSION_DOWNGRADE"
    INSTALL_FAILED_UPDATE_INCOMPATIBLE = "INSTALL_FAILED_UPDATE_INCOMPATIBLE"
    INSTALL_FAILED_INSUFFICIENT_STORAGE = "INSTALL_FAILED_INSUFFICIENT_STORAGE"
    TIMEOUT = "TIMEOUT"
    ERROR = "ERROR"


class InstallResult(BaseModel):
    """Outcome of attempting to install a target V1 update APK or verify an OS update via ADB."""

    apk_path: str
    apk_sha256: str
    outcome: InstallOutcome
    raw_output: str
    duration_ms: float
    success: bool
    error_message: Optional[str] = None
    update_type: str = "apk_update"

    model_config = ConfigDict(extra="ignore")


class V1SoftwareIdentity(BaseModel):
    """Exact software and build identity of the V1 updated build."""

    package: str = "com.example.iqoo_hexnil"
    version_name: Optional[str] = None
    version_code: Optional[int] = None
    apk_path: Optional[str] = None
    apk_sha256: Optional[str] = None
    android_os_version: Optional[str] = None
    build_id: Optional[str] = None
    build_fingerprint: Optional[str] = None
    installed_at: str
    update_method: str = "adb_install_replace"
    software_type: str = "V1_UPDATED"

    model_config = ConfigDict(extra="ignore")


class EnvironmentMatchStatus(str, Enum):
    """Comparison status between V0 and V1 environmental conditions."""

    MATCHED = "MATCHED"
    CHANGED = "CHANGED"
    UNSUPPORTED = "UNSUPPORTED"
    UNKNOWN = "UNKNOWN"


class EnvironmentComparison(BaseModel):
    """Detailed comparison between V0 baseline and V1 update environments."""

    v0_snapshot: EnvironmentSnapshot
    v1_snapshot: EnvironmentSnapshot
    battery_level_delta_percent: Optional[float] = None
    thermal_status_transition: str = "UNKNOWN -> UNKNOWN"
    condition_match_statuses: Dict[str, EnvironmentMatchStatus] = Field(default_factory=dict)
    drift_summary: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")


class PairStatus(str, Enum):
    """Status of an iteration-level run pair between V0 and V1."""

    MATCHED = "MATCHED"
    UNMATCHED_V0_MISSING = "UNMATCHED_V0_MISSING"
    UNMATCHED_V1_MISSING = "UNMATCHED_V1_MISSING"
    CONFIGURATION_MISMATCH = "CONFIGURATION_MISMATCH"
    INVALID = "INVALID"


class ComparisonRunPair(BaseModel):
    """Matched pair of identical workload iterations executed on V0 and V1."""

    comparison_id: str
    workload_id: str
    iteration: int
    v0_run_id: Optional[str] = None
    v1_run_id: Optional[str] = None
    v0_duration_ms: Optional[float] = None
    v1_duration_ms: Optional[float] = None
    v0_configuration_hash: str
    v1_configuration_hash: str
    pair_status: PairStatus
    mismatch_reason: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


class ComparisonQualityReport(BaseModel):
    """Audit of differential experiment completeness, matching, and integrity."""

    comparison_id: str
    v0_experiment_id: str
    v1_experiment_id: str
    device_serial: str
    device_model: str
    update_type: str = "apk_update"
    v0_version: Optional[str] = None
    v1_version: Optional[str] = None
    v0_apk_sha256: Optional[str] = None
    v1_apk_sha256: Optional[str] = None
    v0_build_id: Optional[str] = None
    v1_build_id: Optional[str] = None
    v0_os_version: Optional[str] = None
    v1_os_version: Optional[str] = None
    workloads_requested: List[str] = Field(default_factory=list)
    workloads_matched: List[str] = Field(default_factory=list)
    workloads_mismatched: List[str] = Field(default_factory=list)
    iterations_requested: int = 1
    v0_valid_runs_count: int = 0
    v1_valid_runs_count: int = 0
    matched_pairs_count: int = 0
    unmatched_pairs_count: int = 0
    evidence_coverage: str = ""  # e.g. "5/5 workloads have matched V0/V1 evidence"
    contamination_flags: List[str] = Field(default_factory=list)
    is_clean_comparison: bool = True
    summary_verdict: str = "TRUSTED_DIFFERENTIAL_EVIDENCE"

    model_config = ConfigDict(extra="ignore")


class ComparisonRecord(BaseModel):
    """Master differential record tying together V0 baseline and V1 update evidence."""

    comparison_id: str
    phase: str = "05_v0_v1_differential"
    update_type: str = "apk_update"
    created_at: str
    v0_experiment_id: str
    v1_experiment_id: str
    device: DeviceMetadata
    v0_software: V0SoftwareIdentity
    v1_software: V1SoftwareIdentity
    workload_suite: List[str] = Field(default_factory=list)
    environment_comparison: EnvironmentComparison
    run_pairs: List[ComparisonRunPair] = Field(default_factory=list)
    install_result: InstallResult
    artifacts: Dict[str, List[str]] = Field(default_factory=dict)
    status: str = "completed"

    model_config = ConfigDict(extra="ignore")
