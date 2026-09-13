"""Unit tests for Phase 6 statistical engine calculations."""

import math
import pytest

from hexnil.stats.engine import (
    adjust_p_values,
    compute_absolute_delta,
    compute_bootstrap_confidence_interval,
    compute_cohens_d_paired,
    compute_paired_confidence_interval,
    compute_paired_differences,
    compute_percentage_delta,
    perform_paired_t_test,
)
from hexnil.stats.models import StatisticalTestResult


def test_compute_paired_differences():
    v0 = [10.0, 20.0, 30.0]
    v1 = [12.0, 25.0, 28.0]
    diffs = compute_paired_differences(v0, v1)
    assert diffs == [2.0, 5.0, -2.0]


def test_compute_paired_differences_unequal_lengths():
    with pytest.raises(ValueError):
        compute_paired_differences([1.0], [1.0, 2.0])


def test_compute_absolute_delta():
    assert compute_absolute_delta([100.0, 200.0], [150.0, 250.0]) == 50.0
    assert compute_absolute_delta([], []) == 0.0


def test_compute_percentage_delta():
    # Regular valid delta
    v0 = [100.0, 100.0]
    v1 = [110.0, 110.0]
    pct = compute_percentage_delta(v0, v1)
    assert pct == 10.0

    # Zero denominator
    v0_zero = [0.0, 0.0]
    v1_val = [5.0, 5.0]
    pct = compute_percentage_delta(v0_zero, v1_val)
    assert pct is None

    # Empty inputs
    pct = compute_percentage_delta([], [])
    assert pct is None


def test_compute_cohens_d_paired():
    diffs = [2.0, 2.0, 2.0, 2.0]
    assert compute_cohens_d_paired(diffs) == 0.0

    diffs_varied = [1.0, 2.0, 3.0]
    d = compute_cohens_d_paired(diffs_varied)
    assert d is not None
    assert d > 0


def test_compute_paired_confidence_interval_student_t():
    diffs = [10.0, 12.0, 14.0]
    ci = compute_paired_confidence_interval(diffs, confidence_level=0.95)
    assert ci.method == "student_t"
    assert ci.ci_lower is not None
    assert ci.ci_upper is not None
    assert ci.ci_lower < 12.0 < ci.ci_upper


def test_compute_paired_confidence_interval_insufficient_data():
    diffs = [10.0]
    ci = compute_paired_confidence_interval(diffs, confidence_level=0.95)
    assert ci.ci_lower is None
    assert ci.ci_upper is None


def test_compute_bootstrap_confidence_interval_deterministic():
    diffs = [5.0, 7.0, 8.0, 12.0, 14.0]
    ci1 = compute_bootstrap_confidence_interval(diffs, confidence_level=0.95, n_resamples=500, random_seed=42)
    ci2 = compute_bootstrap_confidence_interval(diffs, confidence_level=0.95, n_resamples=500, random_seed=42)
    assert ci1.ci_lower == ci2.ci_lower
    assert ci1.ci_upper == ci2.ci_upper
    assert "bootstrap_percentile" in ci1.method


def test_perform_paired_t_test():
    v0 = [100.0, 102.0, 99.0, 101.0]
    v1 = [120.0, 122.0, 119.0, 121.0]
    res = perform_paired_t_test(v0, v1, alpha=0.05)
    assert res.status == "EXECUTED"
    assert res.p_value is not None
    assert res.p_value < 0.001
    assert res.test_name == "paired_t_test"


def test_perform_paired_t_test_small_sample():
    v0 = [100.0, 102.0]
    v1 = [120.0, 122.0]
    res = perform_paired_t_test(v0, v1, alpha=0.05)
    assert res.status == "NOT_APPLICABLE"
    assert res.p_value is None


def test_adjust_p_values_none():
    t1 = StatisticalTestResult(test_name="t1", p_value=0.01, status="EXECUTED")
    t2 = StatisticalTestResult(test_name="t2", p_value=0.04, status="EXECUTED")
    t3 = StatisticalTestResult(test_name="t3", p_value=0.05, status="EXECUTED")
    results = [t1, t2, t3]
    adjusted = adjust_p_values(results, method="none")
    assert adjusted[0].adjusted_p_value == 0.01
    assert adjusted[1].adjusted_p_value == 0.04
    assert adjusted[2].adjusted_p_value == 0.05


def test_adjust_p_values_holm():
    t1 = StatisticalTestResult(test_name="t1", p_value=0.01, status="EXECUTED")
    t2 = StatisticalTestResult(test_name="t2", p_value=0.04, status="EXECUTED")
    t3 = StatisticalTestResult(test_name="t3", p_value=0.05, status="EXECUTED")
    results = [t1, t2, t3]
    adjusted = adjust_p_values(results, method="holm")
    assert adjusted[0].adjusted_p_value == round(0.01 * 3, 6)
    assert adjusted[1].adjusted_p_value == round(0.04 * 2, 6)
    # Holm enforces monotonicity: p3 adjusted cannot be less than p2 adjusted
    assert adjusted[2].adjusted_p_value == 0.08


def test_adjust_p_values_fdr():
    t1 = StatisticalTestResult(test_name="t1", p_value=0.01, status="EXECUTED")
    t2 = StatisticalTestResult(test_name="t2", p_value=0.04, status="EXECUTED")
    t3 = StatisticalTestResult(test_name="t3", p_value=0.05, status="EXECUTED")
    results = [t1, t2, t3]
    adjusted = adjust_p_values(results, method="fdr")
    assert len(adjusted) == 3
    assert adjusted[0].adjusted_p_value <= adjusted[1].adjusted_p_value <= adjusted[2].adjusted_p_value
