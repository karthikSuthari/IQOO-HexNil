"""Tests for Phase 12: Report Generator."""

import pytest
from hexnil.classify.models import IssueCategory, IssueClassification, IssueReport
from hexnil.evaluate.models import PredictionEvaluationReport
from hexnil.monitor.models import (
    DeviceOsState,
    MonitoringPhase,
    MonitoringSession,
    PreUpdateAnomalyReport,
    TransitionType,
    UpdateTransition,
)
from hexnil.report.generator import ReportGenerator
from hexnil.report.models import FinalEvidenceReport


def _make_session(**kwargs):
    defaults = dict(
        session_id="MON-0001",
        device_serial="ABC123",
        device_model="iQOO Neo9 Pro",
        created_at="2026-01-01T00:00:00Z",
        phase=MonitoringPhase.COMPLETED,
        v0_os_state=DeviceOsState(
            build_fingerprint="fp_v0", build_id="B1",
            android_version="15", security_patch_level="2025-01-01",
            captured_at="2026-01-01T00:00:00Z",
        ),
    )
    defaults.update(kwargs)
    return MonitoringSession(**defaults)


def _make_issue_report(fixed=0, persisted=0, regressions=0, improvements=0):
    classifications = []
    for i in range(fixed):
        classifications.append(IssueClassification(
            classification_id=f"CLS-fixed-{i}",
            workload_id="startup_01",
            metric_name=f"metric_fixed_{i}",
            category=IssueCategory.FIXED,
            pre_update_anomaly_existed=True,
            post_update_verdict="IMPROVEMENT",
            explanation="Fixed by update.",
        ))
    for i in range(regressions):
        classifications.append(IssueClassification(
            classification_id=f"CLS-reg-{i}",
            workload_id="video_power_01",
            metric_name=f"metric_reg_{i}",
            category=IssueCategory.NEW_REGRESSION,
            post_update_verdict="REGRESSION",
            post_update_severity="HIGH",
            percent_delta=15.0,
            explanation="New regression.",
        ))
    return IssueReport(
        session_id="MON-0001", comparison_id="CMP-0001",
        device_serial="ABC", v0_build_id="B1", v1_build_id="B2",
        classifications=classifications,
        fixed_count=fixed, persisted_count=persisted,
        new_regression_count=regressions,
        new_improvement_count=improvements,
        created_at="2026-01-01T00:00:00Z",
    )


class TestReportGenerator:
    def setup_method(self):
        self.gen = ReportGenerator()

    def test_generate_minimal(self):
        session = _make_session()
        report = self.gen.generate(session)
        assert isinstance(report, FinalEvidenceReport)
        assert report.session_id == "MON-0001"
        assert report.device_model == "iQOO Neo9 Pro"

    def test_generate_with_transition(self):
        v0 = DeviceOsState(
            build_fingerprint="fp_v0", build_id="B1",
            android_version="15", captured_at="2026-01-01T00:00:00Z",
        )
        v1 = DeviceOsState(
            build_fingerprint="fp_v1", build_id="B2",
            android_version="15", captured_at="2026-01-02T00:00:00Z",
        )
        transition = UpdateTransition(
            v0_state=v0, v1_state=v1,
            transition_type=TransitionType.VENDOR_UPDATE,
            transition_detected_at="2026-01-02T00:00:00Z",
            v0_fingerprint="fp_v0", v1_fingerprint="fp_v1",
            changes=["Build ID: B1 → B2"],
        )
        session = _make_session(
            v1_os_state=v1,
            update_transition=transition,
        )
        report = self.gen.generate(session)
        assert report.update_transition is not None
        assert "VENDOR_UPDATE" in report.update_description

    def test_generate_with_issues(self):
        session = _make_session()
        issue_report = _make_issue_report(fixed=1, regressions=2)
        report = self.gen.generate(session, issue_report=issue_report)
        assert len(report.fixed_issues) == 1
        assert len(report.new_regressions) == 2
        assert report.overall_verdict == "CRITICAL_REGRESSIONS"

    def test_generate_safe_verdict(self):
        session = _make_session()
        issue_report = _make_issue_report(fixed=2)
        report = self.gen.generate(session, issue_report=issue_report)
        assert report.overall_verdict == "UPDATE_SAFE_WITH_FIXES"

    def test_generate_with_prediction_evaluation(self):
        session = _make_session()
        pred_eval = PredictionEvaluationReport(
            session_id="MON-0001", comparison_id="CMP-0001",
            plan_id="PLAN-0001",
            evaluated_predictions=5,
            true_positives=3, true_negatives=1,
            false_positives=1, false_negatives=0,
            accuracy=0.8,
        )
        report = self.gen.generate(session, prediction_evaluation=pred_eval)
        assert "80.0%" in report.prediction_accuracy_summary

    def test_format_text_contains_all_questions(self):
        session = _make_session()
        report = self.gen.generate(session)
        text = self.gen.format_text(report)
        assert "Q1." in text
        assert "Q2." in text
        assert "Q3." in text
        assert "Q4." in text
        assert "Q5." in text
        assert "Q6." in text
        assert "Q7." in text
        assert "Q8." in text
        assert "Q9." in text
        assert "Q10." in text
        assert "OVERALL VERDICT" in text

    def test_format_text_with_regressions(self):
        session = _make_session()
        issue_report = _make_issue_report(regressions=1)
        report = self.gen.generate(session, issue_report=issue_report)
        text = self.gen.format_text(report)
        assert "⚠" in text or "NEW" in text
        assert "regression" in text.lower()

    def test_recommendations_with_regressions(self):
        session = _make_session()
        issue_report = _make_issue_report(regressions=2)
        report = self.gen.generate(session, issue_report=issue_report)
        assert len(report.recommendations) > 0
        assert any("regression" in r.lower() for r in report.recommendations)

    def test_recommendations_safe(self):
        session = _make_session()
        report = self.gen.generate(session)
        assert len(report.recommendations) > 0
        assert any("No action" in r for r in report.recommendations)

    def test_pre_update_summary(self):
        session = _make_session()
        report = self.gen.generate(session)
        assert "Android 15" in report.pre_update_summary
        assert "B1" in report.pre_update_summary
