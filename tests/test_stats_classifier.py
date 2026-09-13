"""Unit tests for Phase 6 deterministic verdict and severity classifier."""

from hexnil.stats.classifier import classify_verdict_and_severity
from hexnil.stats.models import (
    ConfidenceInterval,
    EngineeringThreshold,
    MetricDirection,
    MetricEligibility,
    Severity,
    StatisticalTestResult,
    Verdict,
)


def test_classify_inconclusive_when_not_eligible():
    threshold = EngineeringThreshold(
        threshold_type="percent",
        meaningful_change_percent=5.0,
    )
    v, s, reason = classify_verdict_and_severity(
        direction=MetricDirection.LOWER_IS_BETTER,
        eligibility=MetricEligibility.INSUFFICIENT_DATA,
        absolute_delta=100.0,
        percent_delta=10.0,
        threshold=threshold,
        sample_count=2,
    )
    assert v == Verdict.INCONCLUSIVE
    assert s == Severity.NONE


def test_classify_lower_is_better_unchanged_sub_threshold():
    threshold = EngineeringThreshold(
        threshold_type="percent",
        meaningful_change_percent=5.0,
    )
    v, s, reason = classify_verdict_and_severity(
        direction=MetricDirection.LOWER_IS_BETTER,
        eligibility=MetricEligibility.SUPPORTED_AND_ELIGIBLE,
        absolute_delta=100.0,
        percent_delta=2.0,  # Below 5.0% threshold
        threshold=threshold,
        confidence_interval=ConfidenceInterval(ci_lower=50.0, ci_upper=150.0, method="student_t"),
        statistical_test=StatisticalTestResult(
            test_name="paired_t_test",
            p_value=0.01,
            is_significant=True,
            status="EXECUTED",
        ),
        sample_count=5,
    )
    assert v == Verdict.UNCHANGED
    assert s == Severity.NONE


def test_classify_lower_is_better_regression_and_severity():
    threshold = EngineeringThreshold(
        threshold_type="percent",
        meaningful_change_percent=5.0,
        severity_bands={"low": 5.0, "medium": 10.0, "high": 20.0, "critical": 35.0},
    )

    # 1. Medium severity (+12% regression)
    v, s, reason = classify_verdict_and_severity(
        direction=MetricDirection.LOWER_IS_BETTER,
        eligibility=MetricEligibility.SUPPORTED_AND_ELIGIBLE,
        absolute_delta=600.0,
        percent_delta=12.0,
        threshold=threshold,
        confidence_interval=ConfidenceInterval(ci_lower=400.0, ci_upper=800.0, method="student_t"),
        statistical_test=StatisticalTestResult(
            test_name="paired_t_test",
            p_value=0.01,
            is_significant=True,
            status="EXECUTED",
        ),
        sample_count=5,
    )
    assert v == Verdict.REGRESSION
    assert s == Severity.MEDIUM

    # 2. Critical severity (+40% regression)
    v_crit, s_crit, _ = classify_verdict_and_severity(
        direction=MetricDirection.LOWER_IS_BETTER,
        eligibility=MetricEligibility.SUPPORTED_AND_ELIGIBLE,
        absolute_delta=2000.0,
        percent_delta=40.0,
        threshold=threshold,
        confidence_interval=ConfidenceInterval(ci_lower=1500.0, ci_upper=2500.0, method="student_t"),
        statistical_test=StatisticalTestResult(
            test_name="paired_t_test",
            p_value=0.001,
            is_significant=True,
            status="EXECUTED",
        ),
        sample_count=5,
    )
    assert v_crit == Verdict.REGRESSION
    assert s_crit == Severity.CRITICAL


def test_classify_lower_is_better_improvement():
    threshold = EngineeringThreshold(
        threshold_type="percent",
        meaningful_change_percent=5.0,
    )
    v, s, reason = classify_verdict_and_severity(
        direction=MetricDirection.LOWER_IS_BETTER,
        eligibility=MetricEligibility.SUPPORTED_AND_ELIGIBLE,
        absolute_delta=-500.0,
        percent_delta=-10.0,
        threshold=threshold,
        confidence_interval=ConfidenceInterval(ci_lower=-600.0, ci_upper=-400.0, method="student_t"),
        statistical_test=StatisticalTestResult(
            test_name="paired_t_test",
            p_value=0.01,
            is_significant=True,
            status="EXECUTED",
        ),
        sample_count=5,
    )
    assert v == Verdict.IMPROVEMENT
    assert s == Severity.NONE


def test_classify_higher_is_better_regression():
    threshold = EngineeringThreshold(
        threshold_type="percent",
        meaningful_change_percent=5.0,
        severity_bands={"low": 5.0, "medium": 15.0, "high": 25.0, "critical": 40.0},
    )
    # Available memory dropped by 18% -> REGRESSION
    v, s, reason = classify_verdict_and_severity(
        direction=MetricDirection.HIGHER_IS_BETTER,
        eligibility=MetricEligibility.SUPPORTED_AND_ELIGIBLE,
        absolute_delta=-360.0,
        percent_delta=-18.0,
        threshold=threshold,
        confidence_interval=ConfidenceInterval(ci_lower=-400.0, ci_upper=-320.0, method="student_t"),
        statistical_test=StatisticalTestResult(
            test_name="paired_t_test",
            p_value=0.01,
            is_significant=True,
            status="EXECUTED",
        ),
        sample_count=5,
    )
    assert v == Verdict.REGRESSION
    assert s == Severity.MEDIUM


def test_classify_inconclusive_when_p_value_not_significant():
    threshold = EngineeringThreshold(
        threshold_type="percent",
        meaningful_change_percent=5.0,
    )
    # Large delta (+15%) but p = 0.40 (not statistically significant)
    v, s, reason = classify_verdict_and_severity(
        direction=MetricDirection.LOWER_IS_BETTER,
        eligibility=MetricEligibility.SUPPORTED_AND_ELIGIBLE,
        absolute_delta=500.0,
        percent_delta=15.0,
        threshold=threshold,
        confidence_interval=ConfidenceInterval(ci_lower=-200.0, ci_upper=1200.0, method="student_t"),
        statistical_test=StatisticalTestResult(
            test_name="paired_t_test",
            p_value=0.40,
            is_significant=False,
            status="EXECUTED",
        ),
        sample_count=3,
    )
    assert v == Verdict.INCONCLUSIVE
    assert s == Severity.NONE
    assert "not statistically significant" in reason.lower()
