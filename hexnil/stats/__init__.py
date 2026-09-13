"""Hexnil Phase 6: Statistical Comparison & Regression Detection."""

from hexnil.stats.classifier import assign_severity, classify_verdict_and_severity
from hexnil.stats.engine import (
    adjust_p_values,
    compute_absolute_delta,
    compute_cohens_d_paired,
    compute_deterministic_bootstrap_ci,
    compute_paired_confidence_interval,
    compute_paired_differences,
    compute_percentage_delta,
    perform_paired_t_test,
)
from hexnil.stats.models import (
    ConfidenceInterval,
    EngineeringThreshold,
    MetricComparison,
    MetricDirection,
    MetricEligibility,
    Severity,
    StatisticalAnalysisRecord,
    StatisticalQualityReport,
    StatisticalTestResult,
    Verdict,
)
from hexnil.stats.orchestrator import StatisticalAnalysisOrchestrator
from hexnil.stats.registry import (
    METRIC_REGISTRY,
    MetricMetadata,
    get_metric_direction,
    get_metric_metadata,
    get_registered_metrics_for_workload,
)
from hexnil.stats.store import StatisticalAnalysisStore
from hexnil.stats.thresholds import CURRENT_THRESHOLD_VERSION, DEFAULT_THRESHOLDS, get_threshold_for_metric

__all__ = [
    "ConfidenceInterval",
    "EngineeringThreshold",
    "MetricComparison",
    "MetricDirection",
    "MetricEligibility",
    "MetricMetadata",
    "Severity",
    "StatisticalAnalysisRecord",
    "StatisticalAnalysisOrchestrator",
    "StatisticalAnalysisStore",
    "StatisticalQualityReport",
    "StatisticalTestResult",
    "Verdict",
    "METRIC_REGISTRY",
    "CURRENT_THRESHOLD_VERSION",
    "DEFAULT_THRESHOLDS",
    "adjust_p_values",
    "assign_severity",
    "classify_verdict_and_severity",
    "compute_absolute_delta",
    "compute_cohens_d_paired",
    "compute_deterministic_bootstrap_ci",
    "compute_paired_confidence_interval",
    "compute_paired_differences",
    "compute_percentage_delta",
    "get_metric_direction",
    "get_metric_metadata",
    "get_registered_metrics_for_workload",
    "get_threshold_for_metric",
    "perform_paired_t_test",
]
