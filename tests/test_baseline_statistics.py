"""Unit tests for baseline statistical computations and uncertainty estimates."""

import pytest
from hexnil.baseline.extractor import (
    compute_percentiles,
    estimate_uncertainty,
    get_t_critical_95,
    summarize_metric_values,
)


def test_compute_percentiles_odd_and_even():
    """Verify percentiles calculation on deterministic lists."""
    vals = [10.0, 20.0, 30.0, 40.0, 50.0]
    p25, med, p75 = compute_percentiles(vals)
    assert med == 30.0
    assert p25 == 20.0
    assert p75 == 40.0

    single = [42.0]
    p25_s, med_s, p75_s = compute_percentiles(single)
    assert p25_s == 42.0
    assert med_s == 42.0
    assert p75_s == 42.0


def test_summarize_metric_values_descriptive_stats():
    """Verify mean, median, std_dev, min, max, IQR, and CV computations."""
    data = [100.0, 102.0, 98.0, 101.0, 99.0]
    summary = summarize_metric_values(
        workload_id="startup_01",
        metric_name="startup_duration_ms",
        values=data,
        unit="ms",
        n_excluded=1,
    )
    assert summary.n_valid_runs == 5
    assert summary.n_excluded_runs == 1
    assert summary.mean == 100.0
    assert summary.median == 100.0
    assert summary.min == 98.0
    assert summary.max == 102.0
    assert summary.std_dev == pytest.approx(1.581, 0.01)
    assert summary.variance == pytest.approx(2.5, 0.01)
    assert summary.coefficient_of_variation == pytest.approx(0.0158, 0.001)
    assert summary.run_values == data
    assert summary.outliers_detected == 0


def test_outlier_detection_preserves_raw_data():
    """Verify outliers are identified via 1.5*IQR without dropping from run_values."""
    # 10, 11, 12, 11, 10, 100 (100 is an extreme outlier)
    data = [10.0, 11.0, 12.0, 11.0, 10.0, 100.0]
    summary = summarize_metric_values(
        workload_id="cpu_01",
        metric_name="compute_duration_ms",
        values=data,
        unit="ms",
    )
    assert summary.n_valid_runs == 6
    assert summary.outliers_detected == 1
    # Raw values must be preserved intact
    assert len(summary.run_values) == 6
    assert 100.0 in summary.run_values


def test_uncertainty_small_sample_inconclusive():
    """Verify n < 3 returns uncertainty_status = INCONCLUSIVE with explanation."""
    data = [150.0, 155.0]
    unc = estimate_uncertainty(
        workload_id="startup_01",
        metric_name="startup_duration_ms",
        values=data,
    )
    assert unc.uncertainty_status == "INCONCLUSIVE"
    assert unc.sample_size == 2
    assert "insufficient" in unc.explanation.lower()
    assert unc.ci_lower is None
    assert unc.ci_upper is None


def test_uncertainty_zero_variance_inconclusive():
    """Verify zero variance returns uncertainty_status = INCONCLUSIVE."""
    data = [200.0, 200.0, 200.0, 200.0]
    unc = estimate_uncertainty(
        workload_id="startup_01",
        metric_name="startup_duration_ms",
        values=data,
    )
    assert unc.uncertainty_status == "INCONCLUSIVE"
    assert "zero" in unc.explanation.lower()


def test_uncertainty_estimated_confidence_interval():
    """Verify valid Student's t 95% confidence interval estimation."""
    data = [100.0, 105.0, 95.0, 102.0, 98.0]  # mean = 100.0
    unc = estimate_uncertainty(
        workload_id="startup_01",
        metric_name="startup_duration_ms",
        values=data,
    )
    assert unc.uncertainty_status == "ESTIMATED"
    assert unc.method == "student_t"
    assert unc.confidence_level == 0.95
    assert unc.standard_error > 0
    assert unc.ci_lower < 100.0
    assert unc.ci_upper > 100.0
    # Symmetry around mean 100.0
    diff_lower = 100.0 - unc.ci_lower
    diff_upper = unc.ci_upper - 100.0
    assert abs(diff_lower - diff_upper) < 0.05


def test_t_critical_lookup():
    """Verify Student's t critical values for standard and asymptotic degrees of freedom."""
    assert get_t_critical_95(4) == 2.776
    assert get_t_critical_95(9) == 2.262
    assert get_t_critical_95(50) == 1.960
