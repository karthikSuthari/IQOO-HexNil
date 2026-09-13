"""Unit tests verifying Phase 6 reproducibility and determinism."""

from hexnil.stats.engine import (
    compute_bootstrap_confidence_interval,
    perform_paired_t_test,
)


def test_bootstrap_exact_reproducibility_with_seed():
    diffs = [12.5, -3.2, 14.1, 9.8, 11.2, 5.0, 7.8]

    ci1 = compute_bootstrap_confidence_interval(
        diffs, confidence_level=0.95, n_resamples=1000, random_seed=12345
    )
    ci2 = compute_bootstrap_confidence_interval(
        diffs, confidence_level=0.95, n_resamples=1000, random_seed=12345
    )

    assert ci1.ci_lower == ci2.ci_lower
    assert ci1.ci_upper == ci2.ci_upper
    assert ci1.confidence_level == ci2.confidence_level


def test_t_test_exact_reproducibility():
    v0 = [100.0, 105.0, 98.0, 102.0, 99.5]
    v1 = [110.0, 112.0, 108.0, 115.0, 109.0]

    t1 = perform_paired_t_test(v0, v1, alpha=0.05)
    t2 = perform_paired_t_test(v0, v1, alpha=0.05)

    assert t1.p_value == t2.p_value
    assert t1.test_name == t2.test_name
    assert t1.status == t2.status
