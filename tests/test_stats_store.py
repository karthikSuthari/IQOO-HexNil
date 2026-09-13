"""Unit tests for Phase 6 statistical analysis store."""

import json
from pathlib import Path
import pytest

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
from hexnil.stats.store import StatisticalAnalysisStore


def test_save_and_load_statistical_analysis(tmp_path: Path):
    store = StatisticalAnalysisStore(tmp_path)
    comp_id = "CMP-TEST-001"

    quality = StatisticalQualityReport(
        analysis_id=f"STATS-{comp_id}",
        comparison_id=comp_id,
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
        comparison_id=comp_id,
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

    record = StatisticalAnalysisRecord(
        analysis_id=f"STATS-{comp_id}",
        phase="06_statistical_comparison",
        comparison_id=comp_id,
        created_at="2026-09-13T10:00:00Z",
        analysis_version="1.0.0",
        threshold_version="1.0.0",
        multiple_comparison_policy="NONE",
        random_seed=42,
        metric_results=[metric],
        quality=quality,
        exclusions=[],
        provenance={"test": "provenance_data"},
    )

    # 1. Save
    saved_path = store.save_analysis(record)
    assert saved_path.exists()
    assert store.has_analysis(comp_id)

    # 2. Check decomposed files exist
    analysis_dir = store.get_analysis_dir(comp_id)
    assert (analysis_dir / "analysis.json").exists()
    assert (analysis_dir / "metric_results.json").exists()
    assert (analysis_dir / "exclusions.json").exists()
    assert (analysis_dir / "configuration.json").exists()
    assert (analysis_dir / "provenance.json").exists()

    # 3. Check provenance file contents
    prov = json.loads((analysis_dir / "provenance.json").read_text(encoding="utf-8"))
    assert "file_hashes" in prov
    assert "analysis.json" in prov["file_hashes"]

    # 4. Load
    loaded = store.load_analysis(comp_id)
    assert loaded.analysis_id == record.analysis_id
    assert len(loaded.metric_results) == 1
    assert loaded.metric_results[0].metric_name == "startup_duration_ms"

    # 5. Load metric results
    metric_results = store.load_metric_results(comp_id)
    assert len(metric_results) == 1
    assert metric_results[0].verdict == Verdict.UNCHANGED
