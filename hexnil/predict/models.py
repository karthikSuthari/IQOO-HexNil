"""Domain models for Phase 7: Claim Intelligence & Pre-Update Prediction."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from hexnil.stats.models import MetricDirection


class ExtractionMethod(str, Enum):
    """Method used to extract and parse claim from text."""

    RULE_BASED = "RULE_BASED"
    ML_CLASSIFIER = "ML_CLASSIFIER"
    HYBRID = "HYBRID"
    MANUAL_STRUCTURED = "MANUAL_STRUCTURED"
    FALLBACK = "FALLBACK"


class ClaimSubsystem(str, Enum):
    """Standardized subsystem categories for Hexnil validation."""

    BATTERY = "battery"
    STARTUP = "startup/performance"
    MEMORY = "memory"
    UI_PERFORMANCE = "ui/frame performance"
    CPU_PERFORMANCE = "cpu/performance"
    STABILITY = "stability/crash"
    THERMAL = "thermal"
    UNKNOWN = "unknown"


class MetricStatus(str, Enum):
    """Status of metric support in Hexnil telemetry measurement system."""

    SUPPORTED = "SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    AMBIGUOUS = "AMBIGUOUS"


class PredictionPath(str, Enum):
    """Explicit source classification for pre-update prediction."""

    PATH_A_CODE_CHANGE = "PATH_A_CODE_CHANGE"
    PATH_B_CLAIM_HISTORY = "PATH_B_CLAIM_HISTORY"
    PATH_C_INSUFFICIENT_EVIDENCE = "PATH_C_INSUFFICIENT_EVIDENCE"


class RiskBand(str, Enum):
    """Versioned risk classification bands."""

    LOW = "LOW"            # 0.0 <= score < 0.2
    MODERATE = "MODERATE"  # 0.2 <= score < 0.5
    HIGH = "HIGH"          # 0.5 <= score < 0.8
    CRITICAL = "CRITICAL"  # 0.8 <= score <= 1.0


class RawClaim(BaseModel):
    """Raw claim extracted from source release notes prior to normalization."""

    raw_text: str
    line_number: Optional[int] = None
    source: str = "release_notes"

    model_config = ConfigDict(extra="ignore")


class StructuredClaim(BaseModel):
    """Structured engineering representation of an update claim."""

    claim_id: str
    raw_text: str
    normalized_text: str
    subsystem: str
    condition: str
    metric: str
    metric_status: MetricStatus = MetricStatus.SUPPORTED
    expected_direction: MetricDirection = MetricDirection.UNKNOWN
    confidence: float = Field(ge=0.0, le=1.0)
    source: str = "release_notes"
    extraction_method: ExtractionMethod = ExtractionMethod.RULE_BASED
    mapping_notes: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


class FeatureAvailability(BaseModel):
    """Explicit inspection record of genuinely available prediction features."""

    has_claim_text: bool = True
    has_subsystem: bool = True
    has_metric: bool = True
    has_expected_direction: bool = True
    has_historical_claim_outcomes: bool = False
    has_historical_workload_outcomes: bool = False
    has_code_change_features: bool = False
    has_app_version_history: bool = False
    available_features: List[str] = Field(default_factory=list)
    missing_features: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")


class WorkloadRecommendation(BaseModel):
    """Workload recommendation mapped from a structured claim."""

    workload_id: str
    reason: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    required_metrics: List[str] = Field(default_factory=list)
    claim_id: str
    execution_type: str = "Android-side test"

    model_config = ConfigDict(extra="ignore")


class ClaimPrediction(BaseModel):
    """Risk prediction and explanation for an individual structured claim."""

    claim_id: str
    raw_risk_score: float = Field(ge=0.0, le=1.0)
    risk_band: RiskBand
    prediction_path: PredictionPath
    model_name: str
    model_version: str
    feature_availability: FeatureAvailability
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: List[str] = Field(default_factory=list)
    recommendations: List[WorkloadRecommendation] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")


class PrioritizedWorkload(BaseModel):
    """Prioritized validation workload ranked deterministically for execution."""

    priority_rank: int
    workload_id: str
    priority_score: float = Field(ge=0.0, le=1.0)
    associated_claim_ids: List[str] = Field(default_factory=list)
    target_metrics: List[str] = Field(default_factory=list)
    rationale: str
    execution_type: str = "Android-side test"
    estimated_duration_ms: Optional[int] = None

    model_config = ConfigDict(extra="ignore")


class PredictionQuality(BaseModel):
    """Audit report for claim extraction and prediction quality."""

    plan_id: str
    claims_extracted: int = 0
    claims_mapped: int = 0
    claims_unmapped: int = 0
    metrics_supported: int = 0
    metrics_unsupported: int = 0
    predictions_generated: int = 0
    predictions_inconclusive: int = 0
    workloads_recommended: int = 0
    feature_availability_summary: str = ""
    quality_verdict: str = "HIGH_CONFIDENCE"  # "HIGH_CONFIDENCE", "PARTIAL_COVERAGE", "INCONCLUSIVE"

    model_config = ConfigDict(extra="ignore")


class ValidationPlan(BaseModel):
    """Master machine-readable pre-update validation plan."""

    plan_id: str
    phase: str = "07_claim_intelligence_prediction"
    created_at: str
    source_release_notes_raw: str
    source_release_notes_hash: str
    claims: List[StructuredClaim] = Field(default_factory=list)
    predictions: List[ClaimPrediction] = Field(default_factory=list)
    prioritized_workloads: List[PrioritizedWorkload] = Field(default_factory=list)
    model_versions: Dict[str, str] = Field(default_factory=dict)
    feature_availability: FeatureAvailability
    overall_risk_score: float = 0.0
    overall_risk_band: RiskBand = RiskBand.LOW
    overall_path: PredictionPath = PredictionPath.PATH_B_CLAIM_HISTORY
    evidence_linkage_schema: Dict[str, Any] = Field(default_factory=dict)
    provenance: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="ignore")
