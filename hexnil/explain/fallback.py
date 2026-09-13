"""Deterministic fallback explanation generator for Phase 8."""

import datetime
from typing import List

from hexnil.explain.models import (
    ClaimAssessment,
    EvidenceExplanation,
    EvidencePackage,
    EvidenceReference,
    ExplanationSource,
)


def generate_deterministic_explanation(
    package: EvidencePackage,
    reason: str = "Groq API unavailable or offline mode requested",
    source: ExplanationSource = ExplanationSource.DETERMINISTIC_FALLBACK,
) -> EvidenceExplanation:
    """Deterministically synthesize a factual, statistically sound explanation directly from evidence."""
    comparison_id = package.comparison_id
    stats = package.statistics or {}
    metrics = package.metrics or []

    metrics_analyzed = stats.get("metrics_analyzed", len(metrics))
    metrics_unchanged = stats.get("metrics_unchanged", 0)
    metrics_regressions = stats.get("metrics_regressions", 0)
    metrics_inconclusive = stats.get("metrics_inconclusive", 0)
    summary_verdict = stats.get("summary_verdict", "COMPLETED")

    # Authoritative severity from metrics
    severities = [m.severity for m in metrics]
    primary_severity = "CRITICAL" if "CRITICAL" in severities else ("HIGH" if "HIGH" in severities else ("MEDIUM" if "MEDIUM" in severities else ("LOW" if "LOW" in severities else "NONE")))

    # 1. Executive Summary
    if metrics_regressions == 0:
        summary = (
            f"Deterministic analysis of comparison {comparison_id} verified {metrics_analyzed} metrics against "
            f"baseline {package.v0_experiment_id}. Zero regressions were detected. "
            f"{metrics_unchanged} metrics remained stable within engineering thresholds, while {metrics_inconclusive} "
            f"metrics exhibited high runtime variance yielding inconclusive statistical significance."
        )
    else:
        summary = (
            f"Deterministic analysis of comparison {comparison_id} detected {metrics_regressions} regression(s) "
            f"across {metrics_analyzed} analyzed metrics against baseline {package.v0_experiment_id}."
        )

    # 2. Observed Changes
    observed_changes: List[str] = []
    for m in metrics:
        if m.status == "VALID" and m.percent_delta is not None:
            sign = "+" if m.percent_delta > 0 else ""
            delta_str = f"{sign}{m.percent_delta:.2f}%"
            observed_changes.append(
                f"{m.display_name} ({m.workload_id}): shifted by {delta_str} "
                f"(V0: {m.v0_mean} {m.unit} -> V1: {m.v1_mean} {m.unit}, n={m.sample_count}) [{m.verdict}]"
            )
        elif m.status == "UNSUPPORTED":
            observed_changes.append(
                f"{m.display_name} ({m.workload_id}): Telemetry unsupported by physical device platform [{m.verdict}]"
            )

    # 3. Statistical Interpretation
    stat_lines = [
        f"Evaluation performed using paired difference testing across {package.v0_experiment_id} and {package.v1_experiment_id}."
    ]
    for m in metrics:
        if m.p_value is not None:
            sig_text = "statistically significant" if m.p_value < 0.05 else "not statistically significant"
            ci_text = f"95% CI [{m.ci_lower}, {m.ci_upper}]" if m.ci_lower is not None and m.ci_upper is not None else "CI uncalculated"
            stat_lines.append(
                f"• {m.display_name}: p-value = {m.p_value:.4f} ({sig_text} at alpha=0.05, {ci_text}). Reason: {m.verdict_reason}"
            )
    statistical_interpretation = "\n".join(stat_lines)

    # 4. Claim Assessments
    claim_assessments: List[ClaimAssessment] = []
    for c in package.claims:
        target_metric = c.get("metric", "")
        cid = c.get("claim_id", "CLM-???")
        claim_text = c.get("raw_text", "")

        # Find matching metric in package
        matched_metric = next((m for m in metrics if m.metric_name == target_metric), None)
        if matched_metric is None:
            status = "UNSUPPORTED_METRIC"
            expl = f"Target metric '{target_metric}' was not measured or supported in this test suite."
        elif matched_metric.verdict == "UNCHANGED":
            status = "INCONCLUSIVE"
            expl = f"Metric '{matched_metric.display_name}' remained unchanged within 5% threshold; optimization not statistically confirmed."
        elif matched_metric.verdict == "IMPROVEMENT":
            status = "SUPPORTED"
            expl = f"Metric '{matched_metric.display_name}' improved by {matched_metric.percent_delta}% (p={matched_metric.p_value})."
        elif matched_metric.verdict == "REGRESSION":
            status = "CONTRADICTED"
            expl = f"Metric '{matched_metric.display_name}' regressed by {matched_metric.percent_delta}% (p={matched_metric.p_value})."
        else:
            status = "INCONCLUSIVE"
            expl = f"Observation variance yielded inconclusive statistical significance (p={matched_metric.p_value})."

        claim_assessments.append(
            ClaimAssessment(
                claim_id=cid,
                claim_text=claim_text,
                target_metric=target_metric,
                status=status,
                explanation=expl,
            )
        )

    # 5. Limitations
    limitations: List[str] = []
    unsupported = [m for m in metrics if m.status == "UNSUPPORTED"]
    if unsupported:
        names = ", ".join(m.display_name for m in unsupported)
        limitations.append(f"Platform restrictions on device prevented collection of {names}.")

    sample_counts = [m.sample_count for m in metrics if m.sample_count > 0]
    min_n = min(sample_counts, default=0)
    if min_n < 5:
        limitations.append(f"Sample size of {min_n} matched pairs provides limited statistical power; subtle regressions (<5%) may escape detection.")

    limitations.append(f"Fallback mode active: {reason}.")

    # 6. Recommended Next Step
    if metrics_inconclusive > 0:
        recommended_next_step = (
            f"Execute an additional 5 matched iterations under stable thermal preconditions for inconclusive workloads "
            f"(e.g. startup_01) to narrow the 95% confidence intervals."
        )
    elif metrics_regressions > 0:
        recommended_next_step = (
            f"Investigate trace artifacts for detected regressions before approving software release build {package.v1_experiment_id}."
        )
    else:
        recommended_next_step = (
            f"All {metrics_analyzed} metrics are within acceptable engineering thresholds. Proceed to release candidate sign-off."
        )

    # 7. Traceable Evidence References
    references: List[EvidenceReference] = [
        EvidenceReference(
            reference_id="REF-001",
            type="comparison",
            identifier=comparison_id,
            artifact_path=f"data/experiments/comparisons/{comparison_id}/comparison.json",
            description="Master differential comparison record",
        ),
        EvidenceReference(
            reference_id="REF-002",
            type="experiment",
            identifier=package.v0_experiment_id,
            artifact_path=f"data/experiments/{package.v0_experiment_id}/baseline.json",
            description="V0 baseline experiment evidence",
        ),
        EvidenceReference(
            reference_id="REF-003",
            type="experiment",
            identifier=package.v1_experiment_id,
            artifact_path=f"data/experiments/{package.v1_experiment_id}/experiment.json",
            description="V1 differential test experiment evidence",
        ),
    ]

    for idx, m in enumerate(metrics[:3], start=4):
        references.append(
            EvidenceReference(
                reference_id=f"REF-{idx:03d}",
                type="metric",
                identifier=m.metric_name,
                artifact_path=f"data/experiments/comparisons/{comparison_id}/statistical_analysis/metric_results.json",
                description=f"Statistical analysis record for {m.display_name}",
            )
        )

    return EvidenceExplanation(
        explanation_id=f"EXP-DET-{comparison_id}",
        comparison_id=comparison_id,
        source=source,
        model=None,
        verdict=summary_verdict,
        severity=primary_severity,
        summary=summary,
        claim_assessment=claim_assessments,
        observed_changes=observed_changes,
        statistical_interpretation=statistical_interpretation,
        limitations=limitations,
        recommended_next_step=recommended_next_step,
        evidence_references=references,
        created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        latency_ms=0.0,
        is_cached=False,
        evidence_hash=package.evidence_hash,
    )
