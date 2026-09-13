"""Unit tests for differential comparison quality reporting."""

import pytest
from hexnil.diff.models import ComparisonRunPair, PairStatus
from hexnil.diff.quality import evaluate_comparison_quality


def _make_pair(wid: str, iteration: int, status: PairStatus) -> ComparisonRunPair:
    return ComparisonRunPair(
        comparison_id="CMP-001",
        workload_id=wid,
        iteration=iteration,
        v0_run_id=f"V0-{wid}-{iteration}",
        v1_run_id=f"V1-{wid}-{iteration}",
        v0_configuration_hash="hash1",
        v1_configuration_hash="hash1",
        v0_duration_ms=100.0,
        v1_duration_ms=95.0,
        pair_status=status,
    )


def test_evaluate_comparison_quality_clean():
    workloads = ["startup_01", "cpu_01", "memory_01", "scroll_01", "video_power_01"]
    pairs = [_make_pair(w, i, PairStatus.MATCHED) for w in workloads for i in range(1, 4)]

    report = evaluate_comparison_quality(
        comparison_id="CMP-20260913-001",
        v0_experiment_id="EXP-V0",
        v1_experiment_id="EXP-V1",
        device_serial="serial-1",
        device_model="Test Model",
        v0_version="1.0",
        v1_version="1.1",
        v0_apk_sha256="sha0",
        v1_apk_sha256="sha1",
        workloads_requested=workloads,
        workloads_matched=workloads,
        workloads_mismatched=[],
        iterations_requested=3,
        v0_valid_runs_count=15,
        v1_valid_runs_count=15,
        pairs=pairs,
        contamination_flags=[],
    )

    assert report.is_clean_comparison is True
    assert report.summary_verdict == "TRUSTED_DIFFERENTIAL_EVIDENCE"
    assert report.matched_pairs_count == 15
    assert report.unmatched_pairs_count == 0
    assert report.evidence_coverage == "5/5 workloads have matched V0/V1 evidence"
    assert len(report.contamination_flags) == 0


def test_evaluate_comparison_quality_contamination():
    workloads = ["startup_01"]
    pairs = [_make_pair("startup_01", 1, PairStatus.MATCHED)]

    report = evaluate_comparison_quality(
        comparison_id="CMP-20260913-001",
        v0_experiment_id="EXP-V0",
        v1_experiment_id="EXP-V1",
        device_serial="serial-1",
        device_model="Test Model",
        v0_version="1.0",
        v1_version="1.1",
        v0_apk_sha256="sha0",
        v1_apk_sha256="sha1",
        workloads_requested=workloads,
        workloads_matched=workloads,
        workloads_mismatched=[],
        iterations_requested=1,
        v0_valid_runs_count=1,
        v1_valid_runs_count=1,
        pairs=pairs,
        contamination_flags=["Device serial mismatch between V0 and V1"],
    )

    assert report.is_clean_comparison is False
    assert report.summary_verdict == "CONTAMINATED_COMPARISON"
    assert len(report.contamination_flags) >= 1


def test_evaluate_comparison_quality_mismatched_config():
    workloads = ["startup_01", "cpu_01"]
    pairs = [
        _make_pair("startup_01", 1, PairStatus.MATCHED),
        _make_pair("cpu_01", 1, PairStatus.CONFIGURATION_MISMATCH),
    ]

    report = evaluate_comparison_quality(
        comparison_id="CMP-20260913-001",
        v0_experiment_id="EXP-V0",
        v1_experiment_id="EXP-V1",
        device_serial="serial-1",
        device_model="Test Model",
        v0_version="1.0",
        v1_version="1.1",
        v0_apk_sha256="sha0",
        v1_apk_sha256="sha1",
        workloads_requested=workloads,
        workloads_matched=["startup_01"],
        workloads_mismatched=["cpu_01"],
        iterations_requested=1,
        v0_valid_runs_count=2,
        v1_valid_runs_count=2,
        pairs=pairs,
        contamination_flags=[],
    )

    assert report.is_clean_comparison is False
    assert report.summary_verdict == "MISMATCHED_CONFIGURATION"
    assert "cpu_01" in report.workloads_mismatched


def test_evaluate_comparison_quality_insufficient_data():
    workloads = ["startup_01", "cpu_01"]
    report = evaluate_comparison_quality(
        comparison_id="CMP-20260913-001",
        v0_experiment_id="EXP-V0",
        v1_experiment_id="EXP-V1",
        device_serial="serial-1",
        device_model="Test Model",
        v0_version="1.0",
        v1_version="1.1",
        v0_apk_sha256="sha0",
        v1_apk_sha256="sha1",
        workloads_requested=workloads,
        workloads_matched=workloads,
        workloads_mismatched=[],
        iterations_requested=1,
        v0_valid_runs_count=0,
        v1_valid_runs_count=0,
        pairs=[],
        contamination_flags=[],
    )

    assert report.is_clean_comparison is False
    assert report.summary_verdict == "INSUFFICIENT_DATA"
    assert report.evidence_coverage == "0/2 workloads have matched V0/V1 evidence"
