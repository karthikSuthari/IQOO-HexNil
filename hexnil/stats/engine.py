"""Statistical engine for paired comparisons, effect sizes, uncertainty, and hypothesis testing."""

import math
import random
import statistics
from typing import List, Optional, Tuple
from scipy import stats

from hexnil.baseline.extractor import get_t_critical_95
from hexnil.stats.models import ConfidenceInterval, StatisticalTestResult


def compute_paired_differences(v0_values: List[float], v1_values: List[float]) -> List[float]:
    """Compute iteration-level paired differences: D_i = V1_i - V0_i."""
    if len(v0_values) != len(v1_values):
        raise ValueError(
            f"V0 values count ({len(v0_values)}) must match V1 values count ({len(v1_values)}) for paired analysis."
        )
    return [round(v1 - v0, 4) for v0, v1 in zip(v0_values, v1_values)]


def compute_absolute_delta(v0_values: List[float], v1_values: List[float]) -> float:
    """Compute absolute change between V1 mean and V0 mean: mean(V1) - mean(V0)."""
    if not v0_values or not v1_values:
        return 0.0
    v0_mean = statistics.mean(v0_values)
    v1_mean = statistics.mean(v1_values)
    return round(v1_mean - v0_mean, 4)


def compute_percentage_delta(v0_values: List[float], v1_values: List[float]) -> Optional[float]:
    """Compute percentage change relative to V0 baseline mean with safe denominator handling.

    Returns:
        Percentage delta (float) or None if V0 mean is zero or non-positive.
    """
    if not v0_values or not v1_values:
        return None
    v0_mean = statistics.mean(v0_values)
    v1_mean = statistics.mean(v1_values)

    # Safe denominator check: zero or negative baseline cannot yield meaningful percentage change
    if v0_mean <= 0:
        return None

    pct = ((v1_mean - v0_mean) / v0_mean) * 100.0
    return round(pct, 2)


def compute_cohens_d_paired(paired_differences: List[float]) -> Optional[float]:
    """Compute Cohen's d_z for paired continuous differences: mean(D) / stdev(D)."""
    n = len(paired_differences)
    if n < 2:
        return None
    std_diff = statistics.stdev(paired_differences)
    if std_diff == 0.0:
        return 0.0
    mean_diff = statistics.mean(paired_differences)
    return round(mean_diff / std_diff, 4)


def compute_paired_confidence_interval(
    paired_differences: List[float],
    confidence_level: float = 0.95,
) -> ConfidenceInterval:
    """Compute two-tailed confidence interval on paired differences using Student's t distribution."""
    n = len(paired_differences)
    if n < 3:
        return ConfidenceInterval(
            confidence_level=confidence_level,
            method="inconclusive",
            status="INCONCLUSIVE",
        )

    mean_diff = statistics.mean(paired_differences)
    std_diff = statistics.stdev(paired_differences)

    if std_diff == 0.0:
        return ConfidenceInterval(
            lower=round(mean_diff, 4),
            upper=round(mean_diff, 4),
            confidence_level=confidence_level,
            method="student_t_zero_variance",
            status="ESTIMATED",
        )

    se = std_diff / math.sqrt(n)
    df = n - 1
    t_crit = get_t_critical_95(df)
    margin = t_crit * se

    return ConfidenceInterval(
        lower=round(mean_diff - margin, 4),
        upper=round(mean_diff + margin, 4),
        confidence_level=confidence_level,
        method="student_t",
        status="ESTIMATED",
    )


def compute_deterministic_bootstrap_ci(
    paired_differences: List[float],
    confidence_level: float = 0.95,
    n_resamples: int = 2000,
    seed: int = 42,
    random_seed: Optional[int] = None,
) -> ConfidenceInterval:
    """Compute deterministic bootstrap confidence interval for paired differences."""
    actual_seed = random_seed if random_seed is not None else seed
    n = len(paired_differences)
    if n < 3:
        return ConfidenceInterval(
            confidence_level=confidence_level,
            method="bootstrap_inconclusive",
            status="INCONCLUSIVE",
        )

    rng = random.Random(actual_seed)
    boot_means: List[float] = []

    for _ in range(n_resamples):
        sample = [rng.choice(paired_differences) for _ in range(n)]
        boot_means.append(statistics.mean(sample))

    boot_means.sort()
    alpha = 1.0 - confidence_level
    lower_idx = int(n_resamples * (alpha / 2.0))
    upper_idx = int(n_resamples * (1.0 - alpha / 2.0)) - 1

    return ConfidenceInterval(
        lower=round(boot_means[lower_idx], 4),
        upper=round(boot_means[upper_idx], 4),
        confidence_level=confidence_level,
        method=f"bootstrap_percentile_n{n_resamples}",
        status="ESTIMATED",
    )


compute_bootstrap_confidence_interval = compute_deterministic_bootstrap_ci


def perform_paired_t_test(
    v0_values: List[float],
    v1_values: List[float],
    alpha: float = 0.05,
) -> StatisticalTestResult:
    """Execute paired Student's t-test with explicit assumption checking."""
    n = len(v0_values)
    if n < 3:
        return StatisticalTestResult(
            test_name="paired_t_test",
            alpha=alpha,
            assumptions_met=False,
            status="NOT_APPLICABLE",
            notes=f"Sample size (n={n}) is too small for hypothesis testing (minimum 3 required).",
        )

    paired_diffs = [v1 - v0 for v0, v1 in zip(v0_values, v1_values)]
    std_diff = statistics.stdev(paired_diffs) if n > 1 else 0.0

    if std_diff == 0.0:
        mean_diff = statistics.mean(paired_diffs)
        return StatisticalTestResult(
            test_name="paired_t_test",
            statistic=0.0,
            p_value=1.0 if mean_diff == 0.0 else 0.0,
            alpha=alpha,
            is_significant=False,
            assumptions_met=True,
            status="EXECUTED",
            notes="Zero variance in paired differences across samples.",
        )

    # Use scipy.stats for high-precision paired t-test
    res = stats.ttest_rel(v1_values, v0_values)
    stat = float(res.statistic)
    p_val = float(res.pvalue)

    return StatisticalTestResult(
        test_name="paired_t_test",
        statistic=round(stat, 4),
        p_value=round(p_val, 5),
        alpha=alpha,
        is_significant=(p_val < alpha),
        assumptions_met=True,
        status="EXECUTED",
    )


def adjust_p_values(
    test_results: List[StatisticalTestResult],
    method: str = "holm",
) -> List[StatisticalTestResult]:
    """Apply multiple-comparison correction across a family of test results.

    Supported methods:
        - 'none': unadjusted p-values (exploratory analysis)
        - 'holm': Holm-Bonferroni step-down correction
        - 'fdr' / 'benjamini_hochberg': Benjamini-Hochberg False Discovery Rate
    """
    clean_method = method.lower().strip()
    if clean_method == "none":
        for r in test_results:
            r.adjusted_p_value = r.p_value
        return test_results

    # Collect tests with valid p-values
    valid_indices = [
        i for i, r in enumerate(test_results)
        if r.status == "EXECUTED" and r.p_value is not None
    ]
    m = len(valid_indices)
    if m == 0:
        return test_results

    p_vals = [(test_results[idx].p_value, idx) for idx in valid_indices]

    if clean_method == "holm":
        # Sort by p-value ascending
        p_vals.sort(key=lambda x: x[0])
        max_adj = 0.0
        for rank, (p, idx) in enumerate(p_vals):
            # Holm multiplier: m - rank
            adj = min(1.0, (m - rank) * p)
            adj = max(adj, max_adj)  # Monotonicity enforcement
            max_adj = adj
            test_results[idx].adjusted_p_value = round(adj, 5)
            test_results[idx].is_significant = (adj < test_results[idx].alpha)

    elif clean_method in ("fdr", "benjamini_hochberg"):
        p_vals.sort(key=lambda x: x[0])
        adj_vals = [0.0] * m
        # Step-down from largest
        for rank in range(m - 1, -1, -1):
            p, idx = p_vals[rank]
            raw_adj = (p * m) / (rank + 1)
            if rank == m - 1:
                adj_vals[rank] = min(1.0, raw_adj)
            else:
                adj_vals[rank] = min(1.0, min(raw_adj, adj_vals[rank + 1]))
        for rank, (p, idx) in enumerate(p_vals):
            adj = adj_vals[rank]
            test_results[idx].adjusted_p_value = round(adj, 5)
            test_results[idx].is_significant = (adj < test_results[idx].alpha)

    return test_results
