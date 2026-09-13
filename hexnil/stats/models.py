"""Domain models for Phase 6: Statistical Comparison & Regression Detection."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class MetricDirection(str, Enum):
    """Directional interpretation of metric values."""

    LOWER_IS_BETTER = "LOWER_IS_BETTER"
    HIGHER_IS_BETTER = "HIGHER_IS_BETTER"
    NEUTRAL = "NEUTRAL"
    UNKNOWN = "UNKNOWN"


class MetricEligibility(str, Enum):
    """Classification of whether a metric is eligible for statistical comparison."""

    SUPPORTED_AND_ELIGIBLE = "SUPPORTED_AND_ELIGIBLE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    UNSUPPORTED = "UNSUPPORTED"
    INCOMPATIBLE = "INCOMPATIBLE"
    INVALID = "INVALID"


class Verdict(str, Enum):
    """Deterministic engineering verdict on metric progression."""

    IMPROVEMENT = "IMPROVEMENT"
    REGRESSION = "REGRESSION"
    UNCHANGED = "UNCHANGED"
    INCONCLUSIVE = "INCONCLUSIVE"
    INVALID = "INVALID"


class Severity(str, Enum):
    """Engineering severity classification for regressions or changes."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"


class StatisticalTestResult(BaseModel):
    """Result of hypothesis testing on paired or independent samples."""

    test_name: str
    statistic: Optional[float] = None
    p_value: Optional[float] = None
    adjusted_p_value: Optional[float] = None
    alpha: float = 0.05
    is_significant: bool = False
    assumptions_met: bool = True
    status: str = "EXECUTED"  # "EXECUTED", "NOT_APPLICABLE", "INCONCLUSIVE"
    notes: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


class ConfidenceInterval(BaseModel):
    """Quantified interval of uncertainty for the estimated effect."""

    lower: Optional[float] = None
    upper: Optional[float] = None
    confidence_level: float = 0.95
    method: str = "student_t"  # "student_t", "bootstrap_percentile", "inconclusive"
    status: str = "ESTIMATED"  # "ESTIMATED", "INCONCLUSIVE"

    @property
    def ci_lower(self) -> Optional[float]:
        return self.lower

    @property
    def ci_upper(self) -> Optional[float]:
        return self.upper

    model_config = ConfigDict(extra="ignore")


class EngineeringThreshold(BaseModel):
    """Predeclared, versioned thresholds defining meaningful engineering significance."""

    threshold_type: str = "percent"  # "percent", "absolute", "hybrid"
    meaningful_change_percent: Optional[float] = None
    meaningful_change_absolute: Optional[float] = None
    severity_bands: Dict[str, float] = Field(default_factory=dict)
    version: str = "1.0.0"

    model_config = ConfigDict(extra="ignore")


class MetricComparison(BaseModel):
    """Complete statistical comparison document for a single metric across matched runs."""

    comparison_id: str
    workload_id: str
    metric_name: str
    metric_unit: str
    direction: MetricDirection
    eligibility: MetricEligibility = MetricEligibility.SUPPORTED_AND_ELIGIBLE
    sample_count: int = 0
    v0_run_ids: List[str] = Field(default_factory=list)
    v1_run_ids: List[str] = Field(default_factory=list)
    v0_values: List[float] = Field(default_factory=list)
    v1_values: List[float] = Field(default_factory=list)
    paired_differences: List[float] = Field(default_factory=list)
    v0_mean: Optional[float] = None
    v1_mean: Optional[float] = None
    v0_median: Optional[float] = None
    v1_median: Optional[float] = None
    absolute_delta: Optional[float] = None
    percent_delta: Optional[float] = None
    effect_size: Optional[float] = None  # e.g. Cohen's d_z for paired continuous differences
    effect_size_method: str = "cohens_d_z"
    confidence_interval: Optional[ConfidenceInterval] = None
    statistical_test: Optional[StatisticalTestResult] = None
    threshold: EngineeringThreshold
    verdict: Verdict
    severity: Severity = Severity.NONE
    verdict_reason: str = ""
    status: str = "VALID"

    model_config = ConfigDict(extra="ignore")


class StatisticalQualityReport(BaseModel):
    """Audit of statistical evidence completeness, coverage, and verdicts."""

    analysis_id: str
    comparison_id: str
    metrics_analyzed: int = 0
    metrics_eligible: int = 0
    metrics_inconclusive: int = 0
    metrics_invalid: int = 0
    metrics_unsupported: int = 0
    evidence_coverage: str = ""  # e.g. "8/8 eligible metrics with sufficient measured evidence"
    environment_confounders: List[str] = Field(default_factory=list)
    verdicts_summary: Dict[str, int] = Field(default_factory=dict)
    severity_summary: Dict[str, int] = Field(default_factory=dict)
    summary_verdict: str = "COMPLETED"

    model_config = ConfigDict(extra="ignore")


class StatisticalAnalysisRecord(BaseModel):
    """Master record of statistical comparison and regression detection results."""

    analysis_id: str
    phase: str = "06_statistical_comparison"
    comparison_id: str
    created_at: str
    analysis_version: str = "1.0.0"
    threshold_version: str = "1.0.0"
    multiple_comparison_policy: str = "NONE"
    random_seed: int = 42
    metric_results: List[MetricComparison] = Field(default_factory=list)
    quality: StatisticalQualityReport
    exclusions: List[Dict[str, Any]] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="ignore")
