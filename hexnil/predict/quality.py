"""Quality audit and coverage analysis for Phase 7 predictions."""

from hexnil.predict.models import (
    ClaimSubsystem,
    MetricStatus,
    PredictionPath,
    PredictionQuality,
    ValidationPlan,
)


def audit_prediction_quality(plan: ValidationPlan) -> PredictionQuality:
    """Audit pre-update claim extraction and validation plan quality.

    Distinguishes:
    - Claims extracted vs mapped vs unmapped
    - Metrics supported vs unsupported
    - Predictions generated vs inconclusive
    - Workloads recommended
    - Feature availability
    """
    total_claims = len(plan.claims)
    if total_claims == 0:
        return PredictionQuality(
            plan_id=plan.plan_id,
            claims_extracted=0,
            claims_mapped=0,
            claims_unmapped=0,
            metrics_supported=0,
            metrics_unsupported=0,
            predictions_generated=0,
            predictions_inconclusive=0,
            workloads_recommended=0,
            feature_availability_summary="No claims extracted from source text.",
            quality_verdict="INCONCLUSIVE",
        )

    claims_mapped = sum(1 for c in plan.claims if c.subsystem != ClaimSubsystem.UNKNOWN.value)
    claims_unmapped = total_claims - claims_mapped

    metrics_supported = sum(1 for c in plan.claims if c.metric_status == MetricStatus.SUPPORTED)
    metrics_unsupported = sum(1 for c in plan.claims if c.metric_status == MetricStatus.UNSUPPORTED)

    predictions_generated = len(plan.predictions)
    predictions_inconclusive = sum(
        1 for p in plan.predictions if p.prediction_path == PredictionPath.PATH_C_INSUFFICIENT_EVIDENCE or p.confidence < 0.3
    )

    distinct_workloads = len(plan.prioritized_workloads)

    features_str = f"Available: [{', '.join(plan.feature_availability.available_features)}], Missing: [{', '.join(plan.feature_availability.missing_features)}]"

    # Determine overall quality verdict
    if claims_mapped == total_claims and metrics_supported == total_claims and distinct_workloads > 0:
        verdict = "HIGH_CONFIDENCE"
    elif claims_mapped > 0 and distinct_workloads > 0:
        verdict = "PARTIAL_COVERAGE"
    else:
        verdict = "INCONCLUSIVE"

    return PredictionQuality(
        plan_id=plan.plan_id,
        claims_extracted=total_claims,
        claims_mapped=claims_mapped,
        claims_unmapped=claims_unmapped,
        metrics_supported=metrics_supported,
        metrics_unsupported=metrics_unsupported,
        predictions_generated=predictions_generated,
        predictions_inconclusive=predictions_inconclusive,
        workloads_recommended=distinct_workloads,
        feature_availability_summary=features_str,
        quality_verdict=verdict,
    )
