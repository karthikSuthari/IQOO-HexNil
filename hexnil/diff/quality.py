"""Differential experiment quality auditing and evidence coverage reporting."""

import logging
from typing import List, Optional

from hexnil.diff.models import ComparisonQualityReport, ComparisonRunPair, PairStatus

logger = logging.getLogger("hexnil.diff.quality")


def evaluate_comparison_quality(
    comparison_id: str,
    v0_experiment_id: str,
    v1_experiment_id: str,
    device_serial: str,
    device_model: str,
    v0_version: Optional[str],
    v1_version: Optional[str],
    v0_apk_sha256: Optional[str],
    v1_apk_sha256: Optional[str],
    workloads_requested: List[str],
    workloads_matched: List[str],
    workloads_mismatched: List[str],
    iterations_requested: int,
    v0_valid_runs_count: int,
    v1_valid_runs_count: int,
    pairs: List[ComparisonRunPair],
    contamination_flags: List[str],
) -> ComparisonQualityReport:
    """Audit differential experiment quality, evidence coverage, and run pairing completeness."""
    matched_pairs = [p for p in pairs if p.pair_status == PairStatus.MATCHED]
    unmatched_pairs = [p for p in pairs if p.pair_status != PairStatus.MATCHED]

    # Calculate evidence coverage across workloads
    matched_workload_set = {p.workload_id for p in matched_pairs}
    coverage_count = sum(1 for w in workloads_requested if w in matched_workload_set)
    evidence_coverage = f"{coverage_count}/{len(workloads_requested)} workloads have matched V0/V1 evidence"

    flags = list(contamination_flags)
    if workloads_mismatched:
        flags.append(f"Workload configuration mismatch detected on: {', '.join(workloads_mismatched)}")
    if unmatched_pairs:
        flags.append(f"{len(unmatched_pairs)} run pair(s) were unmatched or invalid")

    # Determine verdict
    if contamination_flags or any("fingerprint mismatch" in f.lower() for f in flags):
        verdict = "CONTAMINATED_COMPARISON"
        is_clean = False
    elif workloads_mismatched:
        verdict = "MISMATCHED_CONFIGURATION"
        is_clean = False
    elif coverage_count < len(workloads_requested) or len(matched_pairs) == 0:
        verdict = "INSUFFICIENT_DATA"
        is_clean = False
    elif len(unmatched_pairs) == 0 and coverage_count == len(workloads_requested):
        verdict = "TRUSTED_DIFFERENTIAL_EVIDENCE"
        is_clean = True
    else:
        verdict = "PARTIAL_DIFFERENTIAL_EVIDENCE"
        is_clean = False

    return ComparisonQualityReport(
        comparison_id=comparison_id,
        v0_experiment_id=v0_experiment_id,
        v1_experiment_id=v1_experiment_id,
        device_serial=device_serial,
        device_model=device_model,
        v0_version=v0_version,
        v1_version=v1_version,
        v0_apk_sha256=v0_apk_sha256,
        v1_apk_sha256=v1_apk_sha256,
        workloads_requested=workloads_requested,
        workloads_matched=workloads_matched,
        workloads_mismatched=workloads_mismatched,
        iterations_requested=iterations_requested,
        v0_valid_runs_count=v0_valid_runs_count,
        v1_valid_runs_count=v1_valid_runs_count,
        matched_pairs_count=len(matched_pairs),
        unmatched_pairs_count=len(unmatched_pairs),
        evidence_coverage=evidence_coverage,
        contamination_flags=flags,
        is_clean_comparison=is_clean,
        summary_verdict=verdict,
    )
