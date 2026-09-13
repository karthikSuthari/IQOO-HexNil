"""Unit tests for workload run persistence under ExperimentStore."""

import pytest
from hexnil.experiments.store import ExperimentStore
from hexnil.workloads.models import RunStatus, WorkloadRun


def test_save_load_list_workload_runs(tmp_path):
    store = ExperimentStore(tmp_path)
    exp_id = "EXP-20260913-050"

    run1 = WorkloadRun(
        experiment_id=exp_id,
        run_id="RUN-20260913-100000-001-A1B2",
        workload_id="cpu_01",
        workload_version="1.0.0",
        configuration_hash="hash_alpha",
        iteration=1,
        started_at="2026-09-13T10:00:00Z",
        ended_at="2026-09-13T10:00:01Z",
        duration_ms=100.5,
        status=RunStatus.SUCCESS,
    )
    run2 = WorkloadRun(
        experiment_id=exp_id,
        run_id="RUN-20260913-100002-002-C3D4",
        workload_id="cpu_01",
        workload_version="1.0.0",
        configuration_hash="hash_alpha",
        iteration=2,
        started_at="2026-09-13T10:00:02Z",
        ended_at="2026-09-13T10:00:03Z",
        duration_ms=98.2,
        status=RunStatus.SUCCESS,
    )
    run_other = WorkloadRun(
        experiment_id=exp_id,
        run_id="RUN-20260913-100005-001-E5F6",
        workload_id="memory_01",
        workload_version="1.0.0",
        configuration_hash="hash_beta",
        iteration=1,
        started_at="2026-09-13T10:00:05Z",
        ended_at="2026-09-13T10:00:06Z",
        duration_ms=250.0,
        status=RunStatus.SUCCESS,
    )

    path1 = store.save_workload_run(exp_id, run1)
    path2 = store.save_workload_run(exp_id, run2)
    path3 = store.save_workload_run(exp_id, run_other)

    assert path1.exists()
    assert "workload_runs" in str(path1)
    assert path1.name == f"{run1.run_id}.json"

    # Test single load
    loaded1 = store.load_workload_run(exp_id, "cpu_01", run1.run_id)
    assert loaded1.run_id == run1.run_id
    assert loaded1.iteration == 1
    assert loaded1.duration_ms == 100.5

    # Test list filtered by workload_id
    cpu_runs = store.list_workload_runs(exp_id, "cpu_01")
    assert len(cpu_runs) == 2
    assert [r.run_id for r in cpu_runs] == [run1.run_id, run2.run_id]

    # Test list all runs for experiment
    all_runs = store.list_workload_runs(exp_id)
    assert len(all_runs) == 3
