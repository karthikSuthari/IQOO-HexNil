"""Domain models for Phase 11: Prediction Evaluation."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class PredictionHit(str, Enum):
    """Whether the ML prediction matched the actual outcome."""

    TRUE_POSITIVE = "TRUE_POSITIVE"    # Predicted risk, actual regression/change
    TRUE_NEGATIVE = "TRUE_NEGATIVE"    # Predicted low risk, actual unchanged
    FALSE_POSITIVE = "FALSE_POSITIVE"  # Predicted risk, actual unchanged
    FALSE_NEGATIVE = "FALSE_NEGATIVE"  # Predicted low risk, actual regression
    UNEVALUATED = "UNEVALUATED"        # Insufficient evidence to evaluate


class PredictionOutcome(BaseModel):
    """Evaluation of a single claim prediction against actual outcome."""

    claim_id: str
    claim_text: str
    subsystem: str
    predicted_risk_band: str  # From Phase 7
    predicted_risk_score: float
    prediction_path: str
    actual_verdict: Optional[str] = None  # From Phase 6 / Phase 10
    actual_severity: Optional[str] = None
    hit_classification: PredictionHit = PredictionHit.UNEVALUATED
    explanation: str = ""

    model_config = ConfigDict(extra="ignore")


class PredictionEvaluationReport(BaseModel):
    """Aggregated prediction accuracy evaluation report."""

    session_id: str
    comparison_id: str
    plan_id: str

    # Claim-level outcomes
    outcomes: List[PredictionOutcome] = Field(default_factory=list)

    # Aggregate metrics
    total_predictions: int = 0
    evaluated_predictions: int = 0
    true_positives: int = 0
    true_negatives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    unevaluated: int = 0

    # Computed accuracy metrics
    accuracy: Optional[float] = None        # (TP + TN) / evaluated
    precision: Optional[float] = None       # TP / (TP + FP)
    recall: Optional[float] = None          # TP / (TP + FN)
    f1_score: Optional[float] = None        # 2 * (P * R) / (P + R)

    overall_assessment: str = ""
    created_at: str = ""

    model_config = ConfigDict(extra="ignore")

    @property
    def prediction_quality(self) -> str:
        """Qualitative assessment of prediction quality."""
        if self.evaluated_predictions == 0:
            return "UNEVALUATED"
        if self.accuracy is not None:
            if self.accuracy >= 0.80:
                return "HIGH_ACCURACY"
            elif self.accuracy >= 0.60:
                return "MODERATE_ACCURACY"
            elif self.accuracy >= 0.40:
                return "LOW_ACCURACY"
        return "POOR_ACCURACY"
