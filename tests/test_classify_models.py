"""Tests for Phase 10: Issue Classification Models."""

import pytest
from hexnil.classify.models import (
    IssueCategory,
    IssueClassification,
    IssueReport,
)


class TestIssueCategory:
    def test_enum_values(self):
        assert IssueCategory.FIXED.value == "FIXED"
        assert IssueCategory.PERSISTED.value == "PERSISTED"
        assert IssueCategory.PERSISTED_WORSENED.value == "PERSISTED_WORSENED"
        assert IssueCategory.NEW_REGRESSION.value == "NEW_REGRESSION"
        assert IssueCategory.NEW_IMPROVEMENT.value == "NEW_IMPROVEMENT"
        assert IssueCategory.UNCHANGED.value == "UNCHANGED"
        assert IssueCategory.INSUFFICIENT_EVIDENCE.value == "INSUFFICIENT_EVIDENCE"


class TestIssueClassification:
    def test_create_fixed(self):
        cls = IssueClassification(
            classification_id="CLS-startup-startup_duration_ms",
            workload_id="startup_01",
            metric_name="startup_duration_ms",
            category=IssueCategory.FIXED,
            pre_update_anomaly_existed=True,
            pre_update_anomaly_id="ANOM-startup-5",
            post_update_verdict="IMPROVEMENT",
            explanation="Fixed by update.",
            confidence=0.9,
        )
        assert cls.category == IssueCategory.FIXED
        assert cls.pre_update_anomaly_existed

    def test_create_new_regression(self):
        cls = IssueClassification(
            classification_id="CLS-battery-drain",
            workload_id="video_power_01",
            metric_name="battery_discharge_proxy",
            category=IssueCategory.NEW_REGRESSION,
            pre_update_anomaly_existed=False,
            post_update_verdict="REGRESSION",
            post_update_severity="HIGH",
            percent_delta=15.5,
            explanation="New regression.",
            confidence=0.85,
        )
        assert cls.category == IssueCategory.NEW_REGRESSION
        assert not cls.pre_update_anomaly_existed


class TestIssueReport:
    def _make_report(self, fixed=1, persisted=0, regressions=0, improvements=0):
        return IssueReport(
            session_id="MON-0001",
            comparison_id="CMP-0001",
            device_serial="ABC",
            v0_build_id="B1",
            v1_build_id="B2",
            fixed_count=fixed,
            persisted_count=persisted,
            new_regression_count=regressions,
            new_improvement_count=improvements,
            unchanged_count=3,
            insufficient_evidence_count=1,
            created_at="2026-01-01T00:00:00Z",
        )

    def test_total_issues(self):
        report = self._make_report(fixed=2, persisted=1, regressions=1)
        assert report.total_issues == 4

    def test_has_regressions(self):
        report = self._make_report(regressions=1)
        assert report.has_regressions

    def test_no_regressions(self):
        report = self._make_report(regressions=0)
        assert not report.has_regressions

    def test_has_fixes(self):
        report = self._make_report(fixed=2)
        assert report.has_fixes

    def test_no_fixes(self):
        report = self._make_report(fixed=0)
        assert not report.has_fixes

    def test_empty_report(self):
        report = IssueReport(
            session_id="MON-0001", comparison_id="CMP-0001",
            device_serial="ABC", v0_build_id="B1", v1_build_id="B2",
        )
        assert report.total_issues == 0
        assert not report.has_regressions
        assert not report.has_fixes
