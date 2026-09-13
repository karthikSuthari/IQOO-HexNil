"""Feature inspection, prediction path selection, and risk scoring engine for Phase 7."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import joblib
import numpy as np
import pandas as pd

from hexnil.predict.models import (
    ClaimPrediction,
    ClaimSubsystem,
    FeatureAvailability,
    MetricStatus,
    PredictionPath,
    RiskBand,
    StructuredClaim,
)

PREDICTOR_VERSION = "1.0.0"
MODEL_DIR = Path(__file__).parent / "models"
MODEL_PATH = MODEL_DIR / "code_risk_model.joblib"

# Code change feature names expected by Model A
CODE_CHANGE_FEATURE_NAMES = [
    "delta_loc",
    "delta_nom",
    "delta_noc",
    "delta_wmc",
    "delta_cbo",
    "delta_bad_smells",
]

# Baseline historical empirical risk priors by subsystem (Path B)
SUBSYSTEM_RISK_PRIORS: Dict[str, float] = {
    ClaimSubsystem.BATTERY.value: 0.65,          # High mobile variance & background drain risk
    ClaimSubsystem.MEMORY.value: 0.55,           # Heap allocation & memory leak regression risk
    ClaimSubsystem.STABILITY.value: 0.52,        # Crash fix lifecycle regression risk
    ClaimSubsystem.STARTUP.value: 0.45,          # Cold launch JIT/AOT variance
    ClaimSubsystem.UI_PERFORMANCE.value: 0.40,   # Frame presentation deadline jank
    ClaimSubsystem.CPU_PERFORMANCE.value: 0.35,  # Monotonic compute duration
    ClaimSubsystem.THERMAL.value: 0.30,          # Thermal throttling proxy
    ClaimSubsystem.UNKNOWN.value: 0.15,          # Vague / unmapped claim
}


def score_to_risk_band(score: float) -> RiskBand:
    """Classify normalized continuous risk score into versioned risk bands."""
    clamped = max(0.0, min(1.0, score))
    if clamped < 0.20:
        return RiskBand.LOW
    elif clamped < 0.50:
        return RiskBand.MODERATE
    elif clamped < 0.80:
        return RiskBand.HIGH
    else:
        return RiskBand.CRITICAL


def inspect_feature_availability(
    claims: List[StructuredClaim],
    code_changes: Optional[Dict[str, Any]] = None,
    history_available: bool = False,
) -> FeatureAvailability:
    """Inspect and record genuinely available prediction features without fabrication."""
    has_claims = len(claims) > 0
    has_subsystem = any(c.subsystem != ClaimSubsystem.UNKNOWN.value for c in claims)
    has_metric = any(c.metric_status == MetricStatus.SUPPORTED for c in claims)
    has_direction = any(c.expected_direction.value != "UNKNOWN" for c in claims)

    has_code = False
    if code_changes and isinstance(code_changes, dict):
        has_code = all(feat in code_changes for feat in CODE_CHANGE_FEATURE_NAMES)

    available: List[str] = []
    missing: List[str] = []

    if has_claims:
        available.append("claim_text")
    else:
        missing.append("claim_text")

    if has_subsystem:
        available.append("claim_subsystem")
    else:
        missing.append("claim_subsystem")

    if has_metric:
        available.append("measured_telemetry_metrics")
    else:
        missing.append("measured_telemetry_metrics")

    if has_direction:
        available.append("expected_metric_direction")
    else:
        missing.append("expected_metric_direction")

    if has_code:
        available.append("code_change_ast_metrics")
    else:
        missing.append("code_change_ast_metrics")

    if history_available:
        available.append("historical_comparison_evidence")
    else:
        missing.append("historical_comparison_evidence")

    return FeatureAvailability(
        has_claim_text=has_claims,
        has_subsystem=has_subsystem,
        has_metric=has_metric,
        has_expected_direction=has_direction,
        has_historical_claim_outcomes=history_available,
        has_historical_workload_outcomes=history_available,
        has_code_change_features=has_code,
        has_app_version_history=False,
        available_features=available,
        missing_features=missing,
    )


def select_prediction_path(features: FeatureAvailability) -> PredictionPath:
    """Select appropriate prediction path based strictly on available features."""
    if features.has_code_change_features:
        return PredictionPath.PATH_A_CODE_CHANGE
    elif features.has_claim_text and (features.has_subsystem or features.has_metric):
        return PredictionPath.PATH_B_CLAIM_HISTORY
    else:
        return PredictionPath.PATH_C_INSUFFICIENT_EVIDENCE


def predict_claim_risk(
    claim: StructuredClaim,
    features: FeatureAvailability,
    code_changes: Optional[Dict[str, Any]] = None,
    history_multiplier: float = 1.0,
) -> ClaimPrediction:
    """Predict validation risk for a single structured claim under the selected path."""
    selected_path = select_prediction_path(features)

    # --------------------------------------------------------------------------
    # PATH A: CODE-CHANGE-AWARE MODEL
    # --------------------------------------------------------------------------
    if selected_path == PredictionPath.PATH_A_CODE_CHANGE and code_changes and MODEL_PATH.exists():
        try:
            model = joblib.load(MODEL_PATH)
            X = pd.DataFrame(
                [[code_changes.get(feat, 0.0) for feat in CODE_CHANGE_FEATURE_NAMES]],
                columns=CODE_CHANGE_FEATURE_NAMES,
            )
            probs = model.predict_proba(X)
            raw_score = float(probs[0][1])
            model_name = "RandomForestCodeRiskClassifier"
            model_version = "1.0.0"
            explanation = [
                f"Prediction Path: {selected_path.value}",
                f"Evaluated Model A (RandomForest) on code-change complexity metrics: {code_changes}",
                f"Predicted code degradation probability: {raw_score:.3f}",
            ]
            confidence = 0.85
        except Exception as exc:
            # Fallback to Path B if model fails
            selected_path = PredictionPath.PATH_B_CLAIM_HISTORY
            explanation = [f"Path A model execution failed ({exc}); fallen back to {selected_path.value}."]
            model_name = "SubsystemRiskPriorFallback"
            model_version = PREDICTOR_VERSION
            raw_score = SUBSYSTEM_RISK_PRIORS.get(claim.subsystem, 0.20)
            confidence = claim.confidence

    # --------------------------------------------------------------------------
    # PATH B: CLAIM / HISTORY MODEL
    # --------------------------------------------------------------------------
    elif selected_path == PredictionPath.PATH_B_CLAIM_HISTORY:
        model_name = "SubsystemClaimHistoryHeuristic"
        model_version = PREDICTOR_VERSION

        base_prior = SUBSYSTEM_RISK_PRIORS.get(claim.subsystem, 0.15)
        # Weight by claim extraction confidence
        adjusted_score = base_prior * (0.8 + 0.2 * claim.confidence) * history_multiplier
        raw_score = max(0.0, min(1.0, adjusted_score))
        confidence = claim.confidence

        explanation = [
            f"Prediction Path: {selected_path.value} (Release notes analyzed; no code churn features supplied).",
            f"Target Subsystem: {claim.subsystem} (Domain baseline risk: {base_prior:.2f}).",
            f"Measured Telemetry Metric: {claim.metric} ({claim.metric_status.value}).",
        ]
        if claim.metric_status == MetricStatus.SUPPORTED:
            explanation.append(
                f"Metric '{claim.metric}' is directly measurable in Hexnil via repeated workload runs."
            )
        else:
            explanation.append(
                f"Metric for claim '{claim.claim_id}' is unsupported in continuous telemetry; recorded as coverage gap."
            )

    # --------------------------------------------------------------------------
    # PATH C: INSUFFICIENT EVIDENCE
    # --------------------------------------------------------------------------
    else:
        model_name = "InsufficientEvidenceBaseline"
        model_version = PREDICTOR_VERSION
        raw_score = 0.05
        confidence = 0.10
        explanation = [
            f"Prediction Path: {selected_path.value}",
            "Claim lacks recognizable subsystem or measurable metric. Inconclusive validation risk.",
        ]

    raw_score = round(raw_score, 4)
    risk_band = score_to_risk_band(raw_score)

    return ClaimPrediction(
        claim_id=claim.claim_id,
        raw_risk_score=raw_score,
        risk_band=risk_band,
        prediction_path=selected_path,
        model_name=model_name,
        model_version=model_version,
        feature_availability=features,
        confidence=confidence,
        explanation=explanation,
        recommendations=[],
    )
