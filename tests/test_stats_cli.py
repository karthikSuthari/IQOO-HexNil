"""Unit tests for Phase 6 stats CLI subcommands."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from hexnil.cli import main
from hexnil.stats.models import (
    EngineeringThreshold,
    MetricComparison,
    MetricDirection,
    MetricEligibility,
    Severity,
    StatisticalAnalysisRecord,
    StatisticalQualityReport,
    Verdict,
)


@pytest.fixture
def mock_record():
    quality = StatisticalQualityReport(
        analysis_id="STATS-CMP-MOCK-001",
        comparison_id="CMP-MOCK-001",
        metrics_analyzed=1,
        metrics_eligible=1,
        metrics_inconclusive=0,
        metrics_invalid=0,
        metrics_unsupported=0,
        evidence_coverage="1/1 claims/metrics with sufficient measured evidence",
        environment_confounders=[],
        verdicts_summary={"UNCHANGED": 1},
        severity_summary={"NONE": 1},
        summary_verdict="COMPLETED",
    )
    metric = MetricComparison(
        comparison_id="CMP-MOCK-001",
        workload_id="startup_01",
        metric_name="startup_duration_ms",
        metric_unit="ms",
        direction=MetricDirection.LOWER_IS_BETTER,
        eligibility=MetricEligibility.SUPPORTED_AND_ELIGIBLE,
        sample_count=3,
        v0_values=[1000.0, 1010.0, 1020.0],
        v1_values=[1005.0, 1015.0, 1025.0],
        paired_differences=[5.0, 5.0, 5.0],
        absolute_delta=5.0,
        percent_delta=0.5,
        threshold=EngineeringThreshold(
            threshold_type="percent",
            meaningful_change_percent=5.0,
        ),
        verdict=Verdict.UNCHANGED,
        severity=Severity.NONE,
        verdict_reason="Change below threshold",
    )
    return StatisticalAnalysisRecord(
        analysis_id="STATS-CMP-MOCK-001",
        phase="06_statistical_comparison",
        comparison_id="CMP-MOCK-001",
        created_at="2026-09-13T10:00:00Z",
        analysis_version="1.0.0",
        threshold_version="1.0.0",
        multiple_comparison_policy="NONE",
        random_seed=42,
        metric_results=[metric],
        quality=quality,
        exclusions=[],
        provenance={"mock": "data"},
    )


def test_cli_stats_inspect(capsys):
    mock_inspection = {
        "comparison_id": "CMP-MOCK-001",
        "v0_experiment_id": "EXP-V0",
        "v1_experiment_id": "EXP-V1",
        "device_serial": "TEST-SERIAL",
        "device_model": "Test Model",
        "v0_version": "1.0",
        "v1_version": "1.1",
        "total_pairs": 3,
        "matched_pairs": 3,
        "unmatched_pairs": 0,
        "is_clean_comparison": true if False else True,
        "is_ready_for_stats": True,
    }

    with patch("hexnil.stats.orchestrator.StatisticalAnalysisOrchestrator.inspect_comparison", return_value=mock_inspection):
        code = main(["stats", "inspect", "CMP-MOCK-001"])
        assert code == 0
        out = capsys.readouterr().out
        assert "Hexnil Comparison Statistical Readiness Inspection" in out
        assert "CMP-MOCK-001" in out


def test_cli_stats_inspect_json(capsys):
    mock_inspection = {
        "comparison_id": "CMP-MOCK-001",
        "v0_experiment_id": "EXP-V0",
        "v1_experiment_id": "EXP-V1",
        "device_serial": "TEST-SERIAL",
        "device_model": "Test Model",
        "v0_version": "1.0",
        "v1_version": "1.1",
        "total_pairs": 3,
        "matched_pairs": 3,
        "unmatched_pairs": 0,
        "is_clean_comparison": True,
        "is_ready_for_stats": True,
    }

    with patch("hexnil.stats.orchestrator.StatisticalAnalysisOrchestrator.inspect_comparison", return_value=mock_inspection):
        code = main(["stats", "inspect", "CMP-MOCK-001", "--json"])
        assert code == 0
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["comparison_id"] == "CMP-MOCK-001"
        assert data["is_ready_for_stats"] is True


def test_cli_stats_analyze(capsys, mock_record):
    with patch("hexnil.stats.orchestrator.StatisticalAnalysisOrchestrator.analyze_comparison", return_value=mock_record):
        code = main(["stats", "analyze", "CMP-MOCK-001", "--correction", "holm", "--seed", "123"])
        assert code == 0
        out = capsys.readouterr().out
        assert "Hexnil Statistical Analysis & Regression Detection" in out
        assert "CMP-MOCK-001" in out


def test_cli_stats_show(capsys, mock_record):
    with patch("hexnil.stats.store.StatisticalAnalysisStore.load_analysis", return_value=mock_record):
        code = main(["stats", "show", "CMP-MOCK-001"])
        assert code == 0
        out = capsys.readouterr().out
        assert "Hexnil Statistical Analysis & Regression Detection" in out


def test_cli_stats_metrics(capsys, mock_record):
    with patch("hexnil.stats.store.StatisticalAnalysisStore.load_analysis", return_value=mock_record):
        code = main(["stats", "metrics", "CMP-MOCK-001"])
        assert code == 0
        out = capsys.readouterr().out
        assert "Hexnil Metric Detailed Comparisons" in out
        assert "startup_duration_ms" in out


def test_cli_stats_quality(capsys, mock_record):
    with patch("hexnil.stats.store.StatisticalAnalysisStore.load_analysis", return_value=mock_record):
        code = main(["stats", "quality", "CMP-MOCK-001"])
        assert code == 0
        out = capsys.readouterr().out
        assert "Hexnil Statistical Analysis Quality Audit" in out
        assert "Evidence Coverage:" in out
