"""Strict response validation for Phase 8 Groq AI Analyst."""

import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from hexnil.explain.models import (
    ClaimAssessment,
    EvidencePackage,
    EvidenceReference,
)

logger = logging.getLogger("hexnil.explain.validator")

SEVERITY_ORDER = {
    "NONE": 0,
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
    "CRITICAL": 4,
}


def extract_numbers_from_text(text: str) -> List[float]:
    """Extract numeric tokens from text for verification against evidence."""
    # Match patterns like +3.05%, -22.9%, 12356.3, 0.01158
    found = []
    for token in re.findall(r"[-+]?\d*\.?\d+", text):
        try:
            val = float(token)
            found.append(val)
        except ValueError:
            pass
    return found


def validate_groq_response(
    response: Dict[str, Any],
    package: EvidencePackage,
) -> Tuple[bool, List[str], Optional[Dict[str, Any]]]:
    """Validate raw LLM output against the ground-truth EvidencePackage.

    Returns:
        (is_valid, validation_errors, sanitized_data_dict)
    """
    errors: List[str] = []

    # 1. Required Fields Check
    required_fields = [
        "summary",
        "observed_changes",
        "statistical_interpretation",
        "severity",
        "limitations",
        "recommended_next_step",
    ]
    for field in required_fields:
        if field not in response or not response[field]:
            errors.append(f"Missing or empty required field: '{field}'")

    if errors:
        return False, errors, None

    # 2. Authoritative Severity Check
    # Deter any escalation of severity beyond the deterministic maximum severity
    raw_severity = str(response.get("severity", "NONE")).upper().strip()
    # Find max severity from package metrics
    package_severities = [m.severity.upper() for m in package.metrics]
    max_package_order = max([SEVERITY_ORDER.get(s, 0) for s in package_severities], default=0)
    response_order = SEVERITY_ORDER.get(raw_severity, 0)

    if response_order > max_package_order:
        errors.append(
            f"Response severity '{raw_severity}' exceeds deterministic maximum severity "
            f"'{package_severities}'."
        )

    # 3. Verdict Consistency Check
    summary_text = response.get("summary", "")
    stat_summary = package.statistics.get("summary_verdict", "COMPLETED")
    has_regressions = package.statistics.get("metrics_regressions", 0) > 0

    # If package has 0 regressions, response summary must not falsely claim detected regressions
    if not has_regressions:
        lowered_sum = summary_text.lower()
        if "critical regression detected" in lowered_sum or "severe regression found" in lowered_sum:
            errors.append("Response claims a regression was detected when statistical evidence shows 0 regressions.")

    # 4. Metric Reference & Name Integrity Check
    valid_metric_names: Set[str] = {m.metric_name for m in package.metrics}
    valid_workload_ids: Set[str] = {m.workload_id for m in package.metrics}
    valid_claim_ids: Set[str] = {c.get("claim_id") for c in package.claims if "claim_id" in c}

    evidence_refs = response.get("evidence_references", [])
    parsed_refs: List[EvidenceReference] = []

    for ref in evidence_refs:
        if isinstance(ref, dict):
            ref_type = ref.get("type", "unknown")
            ref_id = ref.get("identifier", "")

            # Check if reference is known
            if ref_type == "metric" and ref_id and ref_id not in valid_metric_names:
                errors.append(f"Referenced unknown metric ID: '{ref_id}'.")
            elif ref_type == "workload" and ref_id and ref_id not in valid_workload_ids:
                errors.append(f"Referenced unknown workload ID: '{ref_id}'.")
            elif ref_type == "comparison" and ref_id and ref_id != package.comparison_id:
                errors.append(f"Referenced non-matching comparison ID: '{ref_id}' (expected '{package.comparison_id}').")
            elif ref_type == "claim" and ref_id and ref_id not in valid_claim_ids:
                errors.append(f"Referenced unknown claim ID: '{ref_id}'.")

            parsed_refs.append(
                EvidenceReference(
                    reference_id=ref.get("reference_id", f"REF-{len(parsed_refs)+1:03d}"),
                    type=ref_type,
                    identifier=ref_id,
                    artifact_path=ref.get("artifact_path"),
                    description=ref.get("description", ""),
                )
            )

    # 5. Claim Assessment Integrity Check
    claim_assessments: List[ClaimAssessment] = []
    raw_assessments = response.get("claim_assessment", [])
    for ca in raw_assessments:
        if isinstance(ca, dict):
            cid = ca.get("claim_id", "")
            if cid and cid not in valid_claim_ids:
                errors.append(f"Response evaluated unknown claim ID: '{cid}'.")
            claim_assessments.append(
                ClaimAssessment(
                    claim_id=cid,
                    claim_text=ca.get("claim_text", ""),
                    target_metric=ca.get("target_metric", ""),
                    status=ca.get("status", "INCONCLUSIVE"),
                    explanation=ca.get("explanation", ""),
                )
            )

    # 6. Observed Changes Format Check
    observed_changes: List[str] = []
    raw_changes = response.get("observed_changes", [])
    if isinstance(raw_changes, list):
        for ch in raw_changes:
            if isinstance(ch, str):
                observed_changes.append(ch)
            elif isinstance(ch, dict):
                # Convert dict to readable summary string
                observed_changes.append(f"{ch.get('metric', '')}: {ch.get('delta', '')} ({ch.get('verdict', '')})")

    limitations: List[str] = [str(l) for l in response.get("limitations", []) if l]

    if errors:
        logger.warning("Groq response failed ground-truth validation: %s", "; ".join(errors))
        return False, errors, None

    # Sanitize and lock authoritative verdict and severity to package values
    authoritative_severity = (
        package.metrics[0].severity if package.metrics else "NONE"
    )
    authoritative_verdict = package.statistics.get("summary_verdict", "COMPLETED")

    cleaned_data = {
        "summary": summary_text,
        "observed_changes": observed_changes,
        "statistical_interpretation": response.get("statistical_interpretation", ""),
        "severity": authoritative_severity,
        "verdict": authoritative_verdict,
        "claim_assessment": [ca.model_dump() for ca in claim_assessments],
        "limitations": limitations,
        "recommended_next_step": response.get("recommended_next_step", ""),
        "evidence_references": [r.model_dump() for r in parsed_refs],
    }

    return True, [], cleaned_data
