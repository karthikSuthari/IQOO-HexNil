"""Tests for Phase 11: Prediction Evaluation Models."""

import pytest
from hexnil.evaluate.models import (
    PredictionEvaluationReport,
    PredictionHit,
    PredictionOutcome,
)


class TestPredictionHit:
    def test_enum_values(self):
        assert PredictionHit.TRUE_POSITIVE.value == "TRUE_POSITIVE"
        assert PredictionHit.TRUE_NEGATIVE.value == "TRUE_NEGATIVE"
        assert PredictionHit.FALSE_POSITIVE.value == "FALSE_POSITIVE"
        assert PredictionHit.FALSE_NEGATIVE.value == "FALSE_NEGATIVE"
        assert PredictionHit.UNEVALUATED.value == "UNEVALUATED"


class TestPredictionOutcome:
    def test_create_true_positive(self):
        outcome = PredictionOutcome(
            claim_id="CLM-001",
            claim_text="Improved battery life",
            subsystem="battery",
            predicted_risk_band="HIGH",
            predicted_risk_score=0.75,
            prediction_path="PATH_B_CLAIM_HISTORY",
            actual_verdict="REGRESSION",
            actual_severity="HIGH",
            hit_classification=PredictionHit.TRUE_POSITIVE,
        )
        assert outcome.hit_classification == PredictionHit.TRUE_POSITIVE

    def test_create_unevaluated(self):
        outcome = PredictionOutcome(
            claim_id="CLM-002",
            claim_text="Performance fix",
            subsystem="cpu/performance",
            predicted_risk_band="MODERATE",
            predicted_risk_score=0.4,
            prediction_path="PATH_B_CLAIM_HISTORY",
        )
        assert outcome.hit_classification == PredictionHit.UNEVALUATED
        assert outcome.actual_verdict is None


class TestPredictionEvaluationReport:
    def test_prediction_quality_high(self):
        report = PredictionEvaluationReport(
            session_id="MON-0001", comparison_id="CMP-0001",
            plan_id="PLAN-0001",
            evaluated_predictions=10, accuracy=0.9,
        )
        assert report.prediction_quality == "HIGH_ACCURACY"

    def test_prediction_quality_moderate(self):
        report = PredictionEvaluationReport(
            session_id="MON-0001", comparison_id="CMP-0001",
            plan_id="PLAN-0001",
            evaluated_predictions=10, accuracy=0.65,
        )
        assert report.prediction_quality == "MODERATE_ACCURACY"

    def test_prediction_quality_low(self):
        report = PredictionEvaluationReport(
            session_id="MON-0001", comparison_id="CMP-0001",
            plan_id="PLAN-0001",
            evaluated_predictions=10, accuracy=0.45,
        )
        assert report.prediction_quality == "LOW_ACCURACY"

    def test_prediction_quality_poor(self):
        report = PredictionEvaluationReport(
            session_id="MON-0001", comparison_id="CMP-0001",
            plan_id="PLAN-0001",
            evaluated_predictions=10, accuracy=0.2,
        )
        assert report.prediction_quality == "POOR_ACCURACY"

    def test_prediction_quality_unevaluated(self):
        report = PredictionEvaluationReport(
            session_id="MON-0001", comparison_id="CMP-0001",
            plan_id="PLAN-0001",
            evaluated_predictions=0,
        )
        assert report.prediction_quality == "UNEVALUATED"

    def test_empty_report(self):
        report = PredictionEvaluationReport(
            session_id="MON-0001", comparison_id="CMP-0001",
            plan_id="PLAN-0001",
        )
        assert report.total_predictions == 0
        assert report.accuracy is None
