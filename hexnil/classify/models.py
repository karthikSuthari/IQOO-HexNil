"""Domain models for Phase 10: Issue Classification."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class IssueCategory(str, Enum):
    """Classification of how an issue relates to the OS update."""

    FIXED = "FIXED"                           # Pre-update anomaly no longer present
    PERSISTED = "PERSISTED"                   # Pre-update anomaly still present
    PERSISTED_WORSENED = "PERSISTED_WORSENED"  # Pre-update anomaly that got worse
    NEW_REGRESSION = "NEW_REGRESSION"         # New problem introduced by the update
    NEW_IMPROVEMENT = "NEW_IMPROVEMENT"       # Unexpected improvement from the update
    UNCHANGED = "UNCHANGED"                   # No change detected
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"  # Not enough data to classify


class IssueClassification(BaseModel):
    """Classification of a single metric's relationship to the OS update."""

    classification_id: str
    workload_id: str
    metric_name: str
    category: IssueCategory
    pre_update_anomaly_existed: bool = False
    pre_update_anomaly_id: Optional[str] = None
    pre_update_anomaly_description: Optional[str] = None
    post_update_verdict: str = "UNCHANGED"  # From Phase 6 statistical verdict
    post_update_severity: str = "NONE"
    absolute_delta: Optional[float] = None
    percent_delta: Optional[float] = None
    effect_size: Optional[float] = None
    explanation: str = ""
    confidence: float = 0.0

    model_config = ConfigDict(extra="ignore")


class IssueReport(BaseModel):
    """Aggregated issue classification report for the entire update validation."""

    session_id: str
    comparison_id: str
    device_serial: str
    v0_build_id: str
    v1_build_id: str
    classifications: List[IssueClassification] = Field(default_factory=list)

    # Summary counts
    fixed_count: int = 0
    persisted_count: int = 0
    new_regression_count: int = 0
    new_improvement_count: int = 0
    unchanged_count: int = 0
    insufficient_evidence_count: int = 0

    overall_assessment: str = ""
    created_at: str = ""

    model_config = ConfigDict(extra="ignore")

    @property
    def total_issues(self) -> int:
        return self.fixed_count + self.persisted_count + self.new_regression_count

    @property
    def has_regressions(self) -> bool:
        return self.new_regression_count > 0

    @property
    def has_fixes(self) -> bool:
        return self.fixed_count > 0
