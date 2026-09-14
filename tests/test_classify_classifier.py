"""Tests for Phase 10: Issue Classifier."""

import pytest
from hexnil.classify.classifier import IssueClassifier
from hexnil.classify.models import IssueCategory
from hexnil.monitor.models import (
    AnomalyType,
    PreUpdateAnomaly,
    PreUpdateAnomalyReport,
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


def _make_metric(
    workload_id="startup_01",
    metric_name="startup_duration_ms",
    verdict=Verdict.UNCHANGED,
    severity=Severity.NONE,
    eligibility=MetricEligibility.SUPPORTED_AND_ELIGIBLE,
    percent_delta=0.0,
    effect_size=0.0,
    p_value=0.5,
):
    return MetricComparison(
        comparison_id="CMP-0001",
        workload_id=workload_id,
        metric_name=metric_name,
        metric_unit="ms",
        direction=MetricDirection.LOWER_IS_BETTER,
        eligibility=eligibility,
        sample_count=5,
        v0_mean=100.0,
        v1_mean=100.0 + percent_delta,
        absolute_delta=percent_delta,
        percent_delta=percent_delta,
        effect_size=effect_size,
        statistical_test=StatisticalTestResult(
            test_name="paired_t", p_value=p_value, is_significant=p_value < 0.05,
        ),
        confidence_interval=ConfidenceInterval(lower=-5.0, upper=5.0),
        threshold=EngineeringThreshold(meaningful_change_percent=5.0),
        verdict=verdict,
        severity=severity,
    )


def _make_anomaly(metric_name="jank_percent"):
    return PreUpdateAnomaly(
        anomaly_id=f"ANOM-{metric_name}-5",
        anomaly_type=AnomalyType.JANK_SPIKE,
        metric_name=metric_name,
        description=f"Anomaly on {metric_name}",
        detected_at="2026-01-01T00:00:00Z",
    )


def _make_analysis(*metrics):
    return StatisticalAnalysisRecord(
        analysis_id="STAT-0001",
        comparison_id="CMP-0001",
        created_at="2026-01-01T00:00:00Z",
        metric_results=list(metrics),
        quality=StatisticalQualityReport(
            analysis_id="STAT-0001", comparison_id="CMP-0001",
        ),
    )


class TestIssueClassifier:
    def setup_method(self):
        self.classifier = IssueClassifier()

    def test_unchanged_no_anomaly(self):
        metric = _make_metric(verdict=Verdict.UNCHANGED)
        analysis = _make_analysis(metric)
        report = self.classifier.classify(
            session_id="MON-0001", comparison_id="CMP-0001",
            device_serial="ABC", v0_build_id="B1", v1_build_id="B2",
            analysis=analysis,
        )
        assert report.unchanged_count == 1
        assert report.classifications[0].category == IssueCategory.UNCHANGED

    def test_new_regression(self):
        metric = _make_metric(
            verdict=Verdict.REGRESSION, severity=Severity.HIGH,
            percent_delta=15.0, effect_size=1.2, p_value=0.01,
        )
        analysis = _make_analysis(metric)
        report = self.classifier.classify(
            session_id="MON-0001", comparison_id="CMP-0001",
            device_serial="ABC", v0_build_id="B1", v1_build_id="B2",
            analysis=analysis,
        )
        assert report.new_regression_count == 1
        assert report.has_regressions
        assert report.classifications[0].category == IssueCategory.NEW_REGRESSION

    def test_new_improvement(self):
        metric = _make_metric(
            verdict=Verdict.IMPROVEMENT, percent_delta=-10.0,
        )
        analysis = _make_analysis(metric)
        report = self.classifier.classify(
            session_id="MON-0001", comparison_id="CMP-0001",
            device_serial="ABC", v0_build_id="B1", v1_build_id="B2",
            analysis=analysis,
        )
        assert report.new_improvement_count == 1
        assert report.classifications[0].category == IssueCategory.NEW_IMPROVEMENT

    def test_fixed_with_anomaly(self):
        metric = _make_metric(
            metric_name="ui_frame_jank_percent",
            verdict=Verdict.IMPROVEMENT, percent_delta=-20.0,
        )
        anomaly = _make_anomaly("jank_percent")
        anomaly_report = PreUpdateAnomalyReport(
            session_id="MON-0001", device_serial="ABC",
            monitoring_duration_seconds=600.0, total_samples=10,
            anomalies=[anomaly], has_pre_existing_issues=True,
        )
        analysis = _make_analysis(metric)
        report = self.classifier.classify(
            session_id="MON-0001", comparison_id="CMP-0001",
            device_serial="ABC", v0_build_id="B1", v1_build_id="B2",
            analysis=analysis, anomaly_report=anomaly_report,
        )
        assert report.fixed_count == 1
        assert report.has_fixes
        assert report.classifications[0].category == IssueCategory.FIXED

    def test_persisted_with_anomaly(self):
        metric = _make_metric(
            metric_name="ui_frame_jank_percent",
            verdict=Verdict.UNCHANGED,
        )
        anomaly = _make_anomaly("jank_percent")
        anomaly_report = PreUpdateAnomalyReport(
            session_id="MON-0001", device_serial="ABC",
            monitoring_duration_seconds=600.0, total_samples=10,
            anomalies=[anomaly], has_pre_existing_issues=True,
        )
        analysis = _make_analysis(metric)
        report = self.classifier.classify(
            session_id="MON-0001", comparison_id="CMP-0001",
            device_serial="ABC", v0_build_id="B1", v1_build_id="B2",
            analysis=analysis, anomaly_report=anomaly_report,
        )
        assert report.persisted_count == 1
        assert report.classifications[0].category == IssueCategory.PERSISTED

    def test_persisted_worsened(self):
        metric = _make_metric(
            metric_name="ui_frame_jank_percent",
            verdict=Verdict.REGRESSION, severity=Severity.MEDIUM,
            percent_delta=25.0,
        )
        anomaly = _make_anomaly("jank_percent")
        anomaly_report = PreUpdateAnomalyReport(
            session_id="MON-0001", device_serial="ABC",
            monitoring_duration_seconds=600.0, total_samples=10,
            anomalies=[anomaly], has_pre_existing_issues=True,
        )
        analysis = _make_analysis(metric)
        report = self.classifier.classify(
            session_id="MON-0001", comparison_id="CMP-0001",
            device_serial="ABC", v0_build_id="B1", v1_build_id="B2",
            analysis=analysis, anomaly_report=anomaly_report,
        )
        assert report.persisted_count == 1
        assert report.classifications[0].category == IssueCategory.PERSISTED_WORSENED

    def test_insufficient_evidence(self):
        metric = _make_metric(
            verdict=Verdict.INCONCLUSIVE,
            eligibility=MetricEligibility.INSUFFICIENT_DATA,
        )
        analysis = _make_analysis(metric)
        report = self.classifier.classify(
            session_id="MON-0001", comparison_id="CMP-0001",
            device_serial="ABC", v0_build_id="B1", v1_build_id="B2",
            analysis=analysis,
        )
        assert report.insufficient_evidence_count == 1

    def test_multiple_metrics(self):
        m1 = _make_metric(
            workload_id="startup_01", metric_name="startup_duration_ms",
            verdict=Verdict.IMPROVEMENT, percent_delta=-15.0,
        )
        m2 = _make_metric(
            workload_id="video_power_01", metric_name="battery_discharge_proxy",
            verdict=Verdict.REGRESSION, severity=Severity.HIGH,
            percent_delta=20.0,
        )
        m3 = _make_metric(
            workload_id="scroll_01", metric_name="ui_frame_jank_percent",
            verdict=Verdict.UNCHANGED,
        )
        analysis = _make_analysis(m1, m2, m3)
        report = self.classifier.classify(
            session_id="MON-0001", comparison_id="CMP-0001",
            device_serial="ABC", v0_build_id="B1", v1_build_id="B2",
            analysis=analysis,
        )
        assert report.new_improvement_count == 1
        assert report.new_regression_count == 1
        assert report.unchanged_count == 1
        assert report.has_regressions

    def test_overall_assessment_text(self):
        metric = _make_metric(
            verdict=Verdict.REGRESSION, severity=Severity.HIGH,
        )
        analysis = _make_analysis(metric)
        report = self.classifier.classify(
            session_id="MON-0001", comparison_id="CMP-0001",
            device_serial="ABC", v0_build_id="B1", v1_build_id="B2",
            analysis=analysis,
        )
        assert "REGRESSION" in report.overall_assessment

    def test_confidence_calculation(self):
        metric = _make_metric(
            verdict=Verdict.REGRESSION, p_value=0.001, effect_size=1.5,
        )
        analysis = _make_analysis(metric)
        report = self.classifier.classify(
            session_id="MON-0001", comparison_id="CMP-0001",
            device_serial="ABC", v0_build_id="B1", v1_build_id="B2",
            analysis=analysis,
        )
        assert report.classifications[0].confidence > 0.8
