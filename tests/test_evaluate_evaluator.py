"""Tests for Phase 11: Prediction Evaluator."""

import pytest
from hexnil.evaluate.evaluator import PredictionEvaluator
from hexnil.evaluate.models import PredictionHit
from hexnil.predict.models import (
    ClaimPrediction,
    ExtractionMethod,
    FeatureAvailability,
    PredictionPath,
    RiskBand,
    StructuredClaim,
    ValidationPlan,
)
from hexnil.stats.models import (
    ConfidenceInterval,
    EngineeringThreshold,
    MetricComparison,
    MetricDirection,
    Severity,
    StatisticalAnalysisRecord,
    StatisticalQualityReport,
    StatisticalTestResult,
    Verdict,
)


def _make_claim(claim_id="CLM-001", subsystem="battery", metric="battery_discharge_proxy"):
    return StructuredClaim(
        claim_id=claim_id,
        raw_text="Improved battery life",
        normalized_text="Battery consumption reduced",
        subsystem=subsystem,
        condition="any",
        metric=metric,
        confidence=0.8,
    )


def _make_prediction(claim_id="CLM-001", risk_band=RiskBand.HIGH, score=0.75):
    return ClaimPrediction(
        claim_id=claim_id,
        raw_risk_score=score,
        risk_band=risk_band,
        prediction_path=PredictionPath.PATH_B_CLAIM_HISTORY,
        model_name="hexnil_claim_risk_v1",
        model_version="1.0.0",
        feature_availability=FeatureAvailability(),
        confidence=0.8,
    )


def _make_metric(
    workload_id="video_power_01",
    metric_name="battery_discharge_proxy",
    verdict=Verdict.REGRESSION,
    severity=Severity.HIGH,
):
    return MetricComparison(
        comparison_id="CMP-0001",
        workload_id=workload_id,
        metric_name=metric_name,
        metric_unit="mAh",
        direction=MetricDirection.LOWER_IS_BETTER,
        sample_count=5,
        v0_mean=100.0, v1_mean=115.0,
        absolute_delta=15.0, percent_delta=15.0,
        effect_size=1.2,
        statistical_test=StatisticalTestResult(
            test_name="paired_t", p_value=0.01, is_significant=True,
        ),
        confidence_interval=ConfidenceInterval(lower=5.0, upper=25.0),
        threshold=EngineeringThreshold(meaningful_change_percent=5.0),
        verdict=verdict,
        severity=severity,
    )


def _make_plan(claims, predictions):
    return ValidationPlan(
        plan_id="PLAN-0001",
        created_at="2026-01-01T00:00:00Z",
        source_release_notes_raw="Test notes",
        source_release_notes_hash="abc123",
        claims=claims,
        predictions=predictions,
        feature_availability=FeatureAvailability(),
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


class TestPredictionEvaluator:
    def setup_method(self):
        self.evaluator = PredictionEvaluator()

    def test_true_positive(self):
        claim = _make_claim()
        pred = _make_prediction(risk_band=RiskBand.HIGH)
        metric = _make_metric(verdict=Verdict.REGRESSION)
        plan = _make_plan([claim], [pred])
        analysis = _make_analysis(metric)

        report = self.evaluator.evaluate("MON-0001", "CMP-0001", plan, analysis)
        assert report.true_positives == 1
        assert report.outcomes[0].hit_classification == PredictionHit.TRUE_POSITIVE

    def test_true_negative(self):
        claim = _make_claim()
        pred = _make_prediction(risk_band=RiskBand.LOW, score=0.1)
        metric = _make_metric(verdict=Verdict.UNCHANGED)
        plan = _make_plan([claim], [pred])
        analysis = _make_analysis(metric)

        report = self.evaluator.evaluate("MON-0001", "CMP-0001", plan, analysis)
        assert report.true_negatives == 1
        assert report.outcomes[0].hit_classification == PredictionHit.TRUE_NEGATIVE

    def test_false_positive(self):
        claim = _make_claim()
        pred = _make_prediction(risk_band=RiskBand.CRITICAL, score=0.9)
        metric = _make_metric(verdict=Verdict.UNCHANGED)
        plan = _make_plan([claim], [pred])
        analysis = _make_analysis(metric)

        report = self.evaluator.evaluate("MON-0001", "CMP-0001", plan, analysis)
        assert report.false_positives == 1
        assert report.outcomes[0].hit_classification == PredictionHit.FALSE_POSITIVE

    def test_false_negative(self):
        claim = _make_claim()
        pred = _make_prediction(risk_band=RiskBand.LOW, score=0.1)
        metric = _make_metric(verdict=Verdict.REGRESSION, severity=Severity.HIGH)
        plan = _make_plan([claim], [pred])
        analysis = _make_analysis(metric)

        report = self.evaluator.evaluate("MON-0001", "CMP-0001", plan, analysis)
        assert report.false_negatives == 1

    def test_accuracy_computation(self):
        c1 = _make_claim("CLM-001")
        c2 = _make_claim("CLM-002", subsystem="startup/performance", metric="startup_duration_ms")
        p1 = _make_prediction("CLM-001", RiskBand.HIGH)
        p2 = _make_prediction("CLM-002", RiskBand.LOW, 0.1)
        m1 = _make_metric(verdict=Verdict.REGRESSION)
        m2 = _make_metric(
            workload_id="startup_01", metric_name="startup_duration_ms",
            verdict=Verdict.UNCHANGED,
        )
        plan = _make_plan([c1, c2], [p1, p2])
        analysis = _make_analysis(m1, m2)

        report = self.evaluator.evaluate("MON-0001", "CMP-0001", plan, analysis)
        assert report.accuracy == 1.0
        assert report.true_positives == 1
        assert report.true_negatives == 1

    def test_unevaluated_no_matching_metric(self):
        claim = _make_claim(metric="nonexistent_metric_xyz", subsystem="unknown")
        pred = _make_prediction()
        plan = _make_plan([claim], [pred])
        analysis = _make_analysis()  # No metrics

        report = self.evaluator.evaluate("MON-0001", "CMP-0001", plan, analysis)
        assert report.unevaluated == 1

    def test_empty_plan(self):
        plan = _make_plan([], [])
        analysis = _make_analysis()
        report = self.evaluator.evaluate("MON-0001", "CMP-0001", plan, analysis)
        assert report.total_predictions == 0
        assert report.accuracy is None

    def test_overall_assessment_text(self):
        claim = _make_claim()
        pred = _make_prediction(risk_band=RiskBand.HIGH)
        metric = _make_metric(verdict=Verdict.REGRESSION)
        plan = _make_plan([claim], [pred])
        analysis = _make_analysis(metric)

        report = self.evaluator.evaluate("MON-0001", "CMP-0001", plan, analysis)
        assert "accuracy" in report.overall_assessment.lower()
