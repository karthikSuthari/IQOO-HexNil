"""Domain models for Phase 8: Evidence-Grounded AI Analyst (Groq)."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ExplanationSource(str, Enum):
    """Source provenance of the engineering explanation."""

    GROQ_AI = "GROQ_AI"
    DETERMINISTIC_ANALYSIS = "DETERMINISTIC_ANALYSIS"
    DETERMINISTIC_FALLBACK = "DETERMINISTIC_FALLBACK"


class EvidenceEligibilityState(str, Enum):
    """Integrity and eligibility status of the evidence package."""

    SUFFICIENT = "SUFFICIENT"
    PARTIAL = "PARTIAL"
    INSUFFICIENT = "INSUFFICIENT"
    INVALID = "INVALID"


class ClaimAssessment(BaseModel):
    """Evaluation of an update claim against measured differential evidence."""

    claim_id: str
    claim_text: str
    target_metric: str
    status: str  # "SUPPORTED", "CONTRADICTED", "INCONCLUSIVE", "UNSUPPORTED_METRIC"
    explanation: str

    model_config = ConfigDict(extra="ignore")


class EvidenceReference(BaseModel):
    """Traceable link to a verified upstream artifact, metric, or experiment."""

    reference_id: str
    type: str  # "metric", "workload", "comparison", "experiment", "claim", "plan"
    identifier: str
    artifact_path: Optional[str] = None
    description: str

    model_config = ConfigDict(extra="ignore")


class MetricEvidenceSummary(BaseModel):
    """Compact summary of a single metric's statistical comparison."""

    workload_id: str
    metric_name: str
    display_name: str
    unit: str
    direction: str
    sample_count: int
    v0_mean: Optional[float] = None
    v1_mean: Optional[float] = None
    absolute_delta: Optional[float] = None
    percent_delta: Optional[float] = None
    p_value: Optional[float] = None
    effect_size: Optional[float] = None
    ci_lower: Optional[float] = None
    ci_upper: Optional[float] = None
    verdict: str
    severity: str
    verdict_reason: str = ""
    status: str = "VALID"

    model_config = ConfigDict(extra="ignore")


class EvidencePackage(BaseModel):
    """Versioned, machine-readable evidence contract provided to the AI Analyst layer."""

    schema_version: str = "1.0"
    comparison_id: str
    v0_experiment_id: str
    v1_experiment_id: str
    device: Dict[str, Any] = Field(default_factory=dict)
    claims: List[Dict[str, Any]] = Field(default_factory=list)
    metrics: List[MetricEvidenceSummary] = Field(default_factory=list)
    statistics: Dict[str, Any] = Field(default_factory=dict)
    verdicts: List[Dict[str, Any]] = Field(default_factory=list)
    prediction: Dict[str, Any] = Field(default_factory=dict)
    evidence_quality: Dict[str, Any] = Field(default_factory=dict)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    evidence_state: EvidenceEligibilityState = EvidenceEligibilityState.SUFFICIENT
    evidence_hash: str = ""

    model_config = ConfigDict(extra="ignore")


class EvidenceExplanation(BaseModel):
    """Authoritative natural-language explanation grounded strictly in evidence."""

    explanation_id: str
    comparison_id: str
    source: ExplanationSource
    model: Optional[str] = None
    verdict: str
    severity: str
    summary: str
    claim_assessment: List[ClaimAssessment] = Field(default_factory=list)
    observed_changes: List[str] = Field(default_factory=list)
    statistical_interpretation: str
    limitations: List[str] = Field(default_factory=list)
    recommended_next_step: str
    evidence_references: List[EvidenceReference] = Field(default_factory=list)
    created_at: str
    latency_ms: Optional[float] = None
    is_cached: bool = False
    evidence_hash: str = ""

    model_config = ConfigDict(extra="ignore")
