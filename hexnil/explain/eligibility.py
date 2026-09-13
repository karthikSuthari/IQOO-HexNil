"""Deterministic Evidence Eligibility Gate for Phase 8 AI Analyst."""

from typing import List, Tuple
from hexnil.explain.models import EvidenceEligibilityState, EvidencePackage


def validate_evidence_eligibility(package: EvidencePackage) -> Tuple[bool, EvidenceEligibilityState, List[str]]:
    """Validate that the evidence package meets strict deterministic eligibility criteria.

    Returns:
        (is_eligible_for_ai, overall_state, list_of_reasons_or_caveats)
    """
    reasons: List[str] = []

    # 1. Comparison Identity & Schema Check
    if not package.comparison_id or not package.comparison_id.startswith("CMP-"):
        reasons.append("Missing or malformed comparison ID.")
        package.evidence_state = EvidenceEligibilityState.INVALID
        return False, EvidenceEligibilityState.INVALID, reasons

    if not package.v0_experiment_id or not package.v1_experiment_id:
        reasons.append("Missing V0 or V1 experiment identity linking evidence.")
        package.evidence_state = EvidenceEligibilityState.INVALID
        return False, EvidenceEligibilityState.INVALID, reasons

    # 2. Statistical Metrics Check
    if not package.metrics:
        reasons.append("Zero comparison metrics present in evidence package.")
        package.evidence_state = EvidenceEligibilityState.INSUFFICIENT
        return False, EvidenceEligibilityState.INSUFFICIENT, reasons

    eligible_metrics = [m for m in package.metrics if m.status == "VALID" and m.sample_count > 0]
    unsupported_metrics = [m for m in package.metrics if m.status in ("UNSUPPORTED", "NOT_APPLICABLE")]
    inconclusive_metrics = [m for m in package.metrics if m.verdict == "INCONCLUSIVE"]

    if not eligible_metrics:
        reasons.append("Zero metrics have sufficient valid sample observations.")
        package.evidence_state = EvidenceEligibilityState.INSUFFICIENT
        return False, EvidenceEligibilityState.INSUFFICIENT, reasons

    # 3. Provenance & Statistics Completeness
    stats = package.statistics or {}
    if "summary_verdict" not in stats:
        reasons.append("Statistical summary verdict missing from evidence package.")
        package.evidence_state = EvidenceEligibilityState.INVALID
        return False, EvidenceEligibilityState.INVALID, reasons

    # 4. Determine overall evidence state
    # Caveats for partial / unsupported data
    if unsupported_metrics:
        reasons.append(f"{len(unsupported_metrics)} metrics are unsupported by physical device platform.")
    if inconclusive_metrics:
        reasons.append(f"{len(inconclusive_metrics)} metrics are statistically inconclusive due to sample variance.")

    # Integrity verification: ensure missing data was not coerced to 0 or unchanged
    for m in package.metrics:
        if m.status == "UNSUPPORTED":
            if m.verdict not in ("INCONCLUSIVE", "INVALID", "UNSUPPORTED"):
                reasons.append(f"Metric '{m.metric_name}' is unsupported but assigned verdict '{m.verdict}'.")
                package.evidence_state = EvidenceEligibilityState.INVALID
                return False, EvidenceEligibilityState.INVALID, reasons

    if len(eligible_metrics) < len(package.metrics) // 2:
        state = EvidenceEligibilityState.PARTIAL
        reasons.append("Fewer than 50% of metrics have complete observation evidence.")
    else:
        state = EvidenceEligibilityState.SUFFICIENT

    package.evidence_state = state
    return True, state, reasons
