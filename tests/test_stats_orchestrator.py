"""Unit tests for Phase 6 StatisticalAnalysisOrchestrator."""

from unittest.mock import MagicMock
import pytest

from hexnil.diff.models import (
    ComparisonQualityReport,
    ComparisonRecord,
    ComparisonRunPair,
    PairStatus,
)
from hexnil.diff.store import ComparisonStore
from hexnil.experiments.store import ExperimentStore
from hexnil.stats.models import (
    MetricEligibility,
    StatisticalAnalysisRecord,
    Verdict,
)
from hexnil.stats.orchestrator import StatisticalAnalysisOrchestrator
from hexnil.stats.store import StatisticalAnalysisStore
from hexnil.workloads.models import RunStatus, StepAction, StepResult, WorkloadRun


@pytest.fixture
def mock_stores():
    exp_store = MagicMock(spec=ExperimentStore)
    comp_store = MagicMock(spec=ComparisonStore)
    stats_store = MagicMock(spec=StatisticalAnalysisStore)
    return exp_store, comp_store, stats_store


def test_orchestrator_inspect_comparison_not_ready(mock_stores):
    exp_store, comp_store, stats_store = mock_stores
    orchestrator = StatisticalAnalysisOrchestrator(exp_store, comp_store, stats_store)

    comp_record = MagicMock(spec=ComparisonRecord)
    comp_record.v0_experiment_id = "V0"
    comp_record.v1_experiment_id = "V1"
    comp_record.device = MagicMock(serial="DEV1", manufacturer="Brand", model="Model")
    comp_record.v0_software = MagicMock(version_name="1.0")
    comp_record.v1_software = MagicMock(version_name="1.1")

    comp_store.load_comparison.return_value = comp_record
    comp_store.load_comparison_quality.return_value = None
    comp_store.load_comparison_pairs.return_value = []

    res = orchestrator.inspect_comparison("CMP-TEST")
    assert res["is_ready_for_stats"] is False
    assert res["matched_pairs"] == 0


def test_orchestrator_analyze_comparison_clean(mock_stores):
    exp_store, comp_store, stats_store = mock_stores
    orchestrator = StatisticalAnalysisOrchestrator(exp_store, comp_store, stats_store)

    comp_record = MagicMock(spec=ComparisonRecord)
    comp_record.comparison_id = "CMP-001"
    comp_record.v0_experiment_id = "EXP-V0"
    comp_record.v1_experiment_id = "EXP-V1"
    comp_record.workload_suite = ["startup_01"]
    comp_record.device = MagicMock(serial="DEV1", manufacturer="Vivo", model="I2302", build_fingerprint="fp")
    comp_record.v0_software = MagicMock(version_name="1.0", apk_sha256="sha_v0")
    comp_record.v1_software = MagicMock(version_name="1.1", apk_sha256="sha_v1")
    comp_record.environment_comparison = MagicMock(
        battery_level_delta_percent=0.0,
        thermal_status_transition="NONE -> NONE",
        drift_summary=[],
    )

    quality = MagicMock(spec=ComparisonQualityReport)
    quality.is_clean_comparison = True
    quality.summary_verdict = "TRUSTED_DIFFERENTIAL_EVIDENCE"

    pair1 = ComparisonRunPair(
        comparison_id="CMP-001",
        workload_id="startup_01",
        iteration=1,
        v0_run_id="run_v0_1",
        v1_run_id="run_v1_1",
        v0_configuration_hash="hash",
        v1_configuration_hash="hash",
        v0_duration_ms=8000.0,
        v1_duration_ms=8020.0,
        duration_delta_ms=20.0,
        pair_status=PairStatus.MATCHED,
    )
    pair2 = ComparisonRunPair(
        comparison_id="CMP-001",
        workload_id="startup_01",
        iteration=2,
        v0_run_id="run_v0_2",
        v1_run_id="run_v1_2",
        v0_configuration_hash="hash",
        v1_configuration_hash="hash",
        v0_duration_ms=8100.0,
        v1_duration_ms=8080.0,
        duration_delta_ms=-20.0,
        pair_status=PairStatus.MATCHED,
    )
    pair3 = ComparisonRunPair(
        comparison_id="CMP-001",
        workload_id="startup_01",
        iteration=3,
        v0_run_id="run_v0_3",
        v1_run_id="run_v1_3",
        v0_configuration_hash="hash",
        v1_configuration_hash="hash",
        v0_duration_ms=7950.0,
        v1_duration_ms=7980.0,
        duration_delta_ms=30.0,
        pair_status=PairStatus.MATCHED,
    )

    comp_store.load_comparison.return_value = comp_record
    comp_store.load_comparison_quality.return_value = quality
    comp_store.load_comparison_pairs.return_value = [pair1, pair2, pair3]

    # Mock workload runs
    def make_run(exp_id, run_id, dur):
        return WorkloadRun(
            experiment_id=exp_id,
            run_id=run_id,
            workload_id="startup_01",
            workload_version="1.0",
            configuration_hash="hash",
            iteration=1,
            started_at="2026-09-13T10:00:00Z",
            ended_at="2026-09-13T10:00:10Z",
            duration_ms=dur,
            status=RunStatus.SUCCESS,
            steps=[
                StepResult(
                    step_id="step_launch",
                    action=StepAction.LAUNCH_APP,
                    status=RunStatus.SUCCESS,
                    started_at="2026-09-13T10:00:00Z",
                    ended_at="2026-09-13T10:00:08Z",
                    duration_ms=dur,
                )
            ],
        )

    exp_store.list_workload_runs.side_effect = lambda exp_id: [
        make_run(exp_id, f"run_v0_1" if "V0" in exp_id else "run_v1_1", 8000.0 if "V0" in exp_id else 8020.0),
        make_run(exp_id, f"run_v0_2" if "V0" in exp_id else "run_v1_2", 8100.0 if "V0" in exp_id else 8080.0),
        make_run(exp_id, f"run_v0_3" if "V0" in exp_id else "run_v1_3", 7950.0 if "V0" in exp_id else 7980.0),
    ]
    exp_store.load_telemetry.return_value = []

    record = orchestrator.analyze_comparison("CMP-001")
    assert record.analysis_id == "STATS-CMP-001"
    assert record.quality.summary_verdict == "COMPLETED"
    assert len(record.metric_results) >= 1

    # Verify that persistence was called
    stats_store.save_analysis.assert_called_once_with(record)
