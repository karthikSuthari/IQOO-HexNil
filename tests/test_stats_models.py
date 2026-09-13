"""Unit tests for Phase 6 statistical domain models."""

import pytest
from pydantic import ValidationError

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


def test_metric_direction_enum():
    assert MetricDirection.LOWER_IS_BETTER.value == "LOWER_IS_BETTER"
    assert MetricDirection.HIGHER_IS_BETTER.value == "HIGHER_IS_BETTER"
    assert MetricDirection.UNKNOWN.value == "UNKNOWN"


def test_verdict_enum():
    assert Verdict.IMPROVEMENT.value == "IMPROVEMENT"
    assert Verdict.REGRESSION.value == "REGRESSION"
    assert Verdict.UNCHANGED.value == "UNCHANGED"
    assert Verdict.INCONCLUSIVE.value == "INCONCLUSIVE"
    assert Verdict.INVALID.value == "INVALID"


def test_severity_enum():
    assert Severity.NONE.value == "NONE"
    assert Severity.LOW.value == "LOW"
    assert Severity.MEDIUM.value == "MEDIUM"
    assert Severity.HIGH.value == "HIGH"
    assert Severity.CRITICAL.value == "CRITICAL"


def test_engineering_threshold_defaults():
    t = EngineeringThreshold(
        threshold_type="percent",
        meaningful_change_percent=5.0,
        severity_bands={"critical": 40.0},
    )
    assert t.meaningful_change_percent == 5.0
    assert t.meaningful_change_absolute is None
    assert "critical" in t.severity_bands


def test_metric_comparison_valid_serialization():
    comp = MetricComparison(
        comparison_id="CMP-20260913-001",
        workload_id="startup_01",
        metric_name="startup_duration_ms",
        metric_unit="ms",
        direction=MetricDirection.LOWER_IS_BETTER,
        eligibility=MetricEligibility.SUPPORTED_AND_ELIGIBLE,
        sample_count=3,
        v0_values=[8000.0, 8100.0, 7900.0],
        v1_values=[7800.0, 7750.0, 7850.0],
        paired_differences=[-200.0, -350.0, -50.0],
        absolute_delta=-200.0,
        percent_delta=-2.5,
        effect_size=-1.33,
        confidence_interval=ConfidenceInterval(
            confidence_level=0.95,
            ci_lower=-450.0,
            ci_upper=50.0,
            method="paired_student_t",
        ),
        statistical_test=StatisticalTestResult(
            test_name="paired_student_t",
            null_hypothesis="mean_diff == 0",
            alternative_hypothesis="mean_diff != 0",
            p_value=0.15,
            status="EXECUTED",
        ),
        threshold=EngineeringThreshold(
            threshold_type="percent",
            meaningful_change_percent=5.0,
        ),
        verdict=Verdict.UNCHANGED,
        severity=Severity.NONE,
        verdict_reason="Delta -2.5% is within 5.0% meaningful threshold.",
    )

    data = comp.model_dump()
    assert data["metric_name"] == "startup_duration_ms"
    assert data["verdict"] == "UNCHANGED"

    reconstructed = MetricComparison.model_validate(data)
    assert reconstructed.metric_name == comp.metric_name
    assert reconstructed.absolute_delta == -200.0


def test_statistical_quality_report():
    qr = StatisticalQualityReport(
        analysis_id="STATS-CMP-20260913-001",
        comparison_id="CMP-20260913-001",
        metrics_analyzed=9,
        metrics_eligible=5,
        metrics_inconclusive=4,
        metrics_invalid=0,
        metrics_unsupported=4,
        evidence_coverage="5/9 claims/metrics with sufficient measured evidence",
        environment_confounders=["Battery level drifted by +0.5%"],
        verdicts_summary={"UNCHANGED": 5, "INCONCLUSIVE": 4},
        severity_summary={"NONE": 9},
        summary_verdict="COMPLETED",
    )
    assert qr.metrics_eligible == 5
    assert qr.verdicts_summary["UNCHANGED"] == 5
