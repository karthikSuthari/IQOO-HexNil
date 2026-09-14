"""Domain models for Phase 12: Final Evidence Report."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from hexnil.classify.models import IssueClassification, IssueReport
from hexnil.evaluate.models import PredictionEvaluationReport
from hexnil.monitor.models import DeviceOsState, PreUpdateAnomalyReport, UpdateTransition


class FinalEvidenceReport(BaseModel):
    """Master evidence report answering the 10 core questions about the OS update impact.

    Questions answered:
    1. What was the device like before the update?
    2. What problems/anomalies existed before the update?
    3. What risks did the ML model predict?
    4. What exact OS/software/security update occurred?
    5. What changed after the update?
    6. Did the update fix an existing problem?
    7. Did an existing problem remain?
    8. Did the update introduce a new regression?
    9. Is there insufficient evidence?
    10. Did the ML prediction match the actual outcome?
    """

    report_id: str
    session_id: str
    created_at: str

    # Device identity
    device_serial: str
    device_model: str

    # Q1: Pre-update device state
    pre_update_os_state: DeviceOsState
    pre_update_summary: str = ""

    # Q2: Pre-update anomalies
    pre_update_anomalies: List[str] = Field(default_factory=list)
    anomaly_report: Optional[PreUpdateAnomalyReport] = None

    # Q3: ML predictions
    ml_prediction_summary: str = ""
    predicted_risk_bands: Dict[str, str] = Field(default_factory=dict)
    prediction_plan_id: Optional[str] = None

    # Q4: Update transition
    update_transition: Optional[UpdateTransition] = None
    update_description: str = ""

    # Q5: Post-update changes
    post_update_os_state: Optional[DeviceOsState] = None
    post_update_changes: List[str] = Field(default_factory=list)
    comparison_id: Optional[str] = None
    analysis_id: Optional[str] = None

    # Q6: Fixed issues
    fixed_issues: List[IssueClassification] = Field(default_factory=list)

    # Q7: Persisted issues
    persisted_issues: List[IssueClassification] = Field(default_factory=list)

    # Q8: New regressions
    new_regressions: List[IssueClassification] = Field(default_factory=list)

    # Q9: Insufficient evidence
    insufficient_evidence_items: List[IssueClassification] = Field(default_factory=list)

    # Q10: Prediction evaluation
    prediction_evaluation: Optional[PredictionEvaluationReport] = None
    prediction_accuracy_summary: str = ""

    # Issue report
    issue_report: Optional[IssueReport] = None

    # Overall
    overall_verdict: str = ""  # "UPDATE_SAFE", "UPDATE_HAS_REGRESSIONS", "MIXED_RESULTS", "INSUFFICIENT_DATA"
    executive_summary: str = ""
    recommendations: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")
