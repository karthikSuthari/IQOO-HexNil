"""Deterministic verdict and severity classification engine."""

from typing import Optional, Tuple

from hexnil.stats.models import (
    ConfidenceInterval,
    EngineeringThreshold,
    MetricDirection,
    MetricEligibility,
    Severity,
    StatisticalTestResult,
    Verdict,
)


def classify_verdict_and_severity(
    direction: MetricDirection,
    eligibility: MetricEligibility,
    absolute_delta: Optional[float],
    percent_delta: Optional[float],
    threshold: EngineeringThreshold,
    confidence_interval: Optional[ConfidenceInterval] = None,
    statistical_test: Optional[StatisticalTestResult] = None,
    sample_count: int = 0,
) -> Tuple[Verdict, Severity, str]:
    """Classify comparison into deterministic engineering verdict and severity.

    Returns:
        Tuple of (verdict, severity, explanation_reason)
    """
    # 1. Eligibility gate
    if eligibility == MetricEligibility.UNSUPPORTED:
        return Verdict.INCONCLUSIVE, Severity.NONE, "Metric is not supported by target device."
    if eligibility == MetricEligibility.INSUFFICIENT_DATA or sample_count < 3:
        return (
            Verdict.INCONCLUSIVE,
            Severity.NONE,
            f"Insufficient valid matched samples (n={sample_count}, minimum 3 required).",
        )
    if eligibility in (MetricEligibility.INCOMPATIBLE, MetricEligibility.INVALID):
        return Verdict.INVALID, Severity.NONE, "Metric data is invalid or incompatible across versions."

    # 2. Metric direction gate
    if direction in (MetricDirection.UNKNOWN, MetricDirection.NEUTRAL):
        return Verdict.INCONCLUSIVE, Severity.NONE, f"Metric direction is {direction.value}; cannot infer regression/improvement."

    if absolute_delta is None:
        return Verdict.INCONCLUSIVE, Severity.NONE, "Absolute delta cannot be computed."

    # 3. Determine if change is deterioration, improvement, or flat
    is_deterioration = False
    is_improvement = False

    if direction == MetricDirection.LOWER_IS_BETTER:
        if absolute_delta > 0:
            is_deterioration = True
        elif absolute_delta < 0:
            is_improvement = True
    elif direction == MetricDirection.HIGHER_IS_BETTER:
        if absolute_delta < 0:
            is_deterioration = True
        elif absolute_delta > 0:
            is_improvement = True

    # 4. Check against Engineering Threshold
    meaningful_exceeded = False
    magnitude_display = ""
    severity_val = 0.0

    if threshold.threshold_type == "percent" and percent_delta is not None:
        change_pct = abs(percent_delta)
        min_meaningful = threshold.meaningful_change_percent or 5.0
        meaningful_exceeded = (change_pct >= min_meaningful)
        magnitude_display = f"{change_pct:.1f}% (threshold: {min_meaningful:.1f}%)"
        severity_val = change_pct
    elif threshold.meaningful_change_absolute is not None:
        change_abs = abs(absolute_delta)
        min_meaningful = threshold.meaningful_change_absolute
        meaningful_exceeded = (change_abs >= min_meaningful)
        magnitude_display = f"{change_abs:.2f} (threshold: {min_meaningful:.2f})"
        severity_val = change_abs
    elif percent_delta is not None:
        change_pct = abs(percent_delta)
        min_meaningful = threshold.meaningful_change_percent or 5.0
        meaningful_exceeded = (change_pct >= min_meaningful)
        magnitude_display = f"{change_pct:.1f}% (threshold: {min_meaningful:.1f}%)"
        severity_val = change_pct
    else:
        # Fallback: if percentage is None and no absolute threshold is set
        change_abs = abs(absolute_delta)
        meaningful_exceeded = (change_abs > 0)
        magnitude_display = f"abs {change_abs:.2f}"
        severity_val = change_abs

    # 5. Classify Verdict
    if not meaningful_exceeded:
        return (
            Verdict.UNCHANGED,
            Severity.NONE,
            f"Observed change {magnitude_display} is within the acceptable engineering threshold.",
        )

    if is_deterioration:
        # If a formal test was executed and failed significance, do not call regression
        if statistical_test and statistical_test.status == "EXECUTED":
            if statistical_test.p_value is not None and not statistical_test.is_significant:
                return (
                    Verdict.INCONCLUSIVE,
                    Severity.NONE,
                    f"Observed shift {magnitude_display} is not statistically significant (p={statistical_test.p_value:.4f} >= {statistical_test.alpha}).",
                )
        # Assign severity based on bands
        sev = assign_severity(severity_val, threshold)
        reason = f"Deterioration detected: shifted by {magnitude_display} in unfavorable direction."
        return Verdict.REGRESSION, sev, reason

    if is_improvement:
        # If a formal test was executed and failed significance, do not call improvement
        if statistical_test and statistical_test.status == "EXECUTED":
            if statistical_test.p_value is not None and not statistical_test.is_significant:
                return (
                    Verdict.INCONCLUSIVE,
                    Severity.NONE,
                    f"Observed shift {magnitude_display} is not statistically significant (p={statistical_test.p_value:.4f} >= {statistical_test.alpha}).",
                )
        reason = f"Improvement detected: shifted by {magnitude_display} in favorable direction."
        return Verdict.IMPROVEMENT, Severity.NONE, reason

    return Verdict.UNCHANGED, Severity.NONE, "No net change detected."


def assign_severity(magnitude: float, threshold: EngineeringThreshold) -> Severity:
    """Map observed effect magnitude to severity band."""
    bands = threshold.severity_bands
    if not bands:
        return Severity.LOW

    # Normalize keys to uppercase for lookup
    normalized_bands = {str(k).upper(): v for k, v in bands.items()}

    crit_threshold = normalized_bands.get(Severity.CRITICAL.value, float("inf"))
    high_threshold = normalized_bands.get(Severity.HIGH.value, float("inf"))
    med_threshold = normalized_bands.get(Severity.MEDIUM.value, float("inf"))
    low_threshold = normalized_bands.get(Severity.LOW.value, 0.0)

    if magnitude >= crit_threshold:
        return Severity.CRITICAL
    elif magnitude >= high_threshold:
        return Severity.HIGH
    elif magnitude >= med_threshold:
        return Severity.MEDIUM
    elif magnitude >= low_threshold:
        return Severity.LOW
    else:
        return Severity.NONE
