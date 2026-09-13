"""Unit tests for WorkloadRunMatcher and configuration locking."""

import pytest
from hexnil.diff.matcher import WorkloadRunMatcher
from hexnil.diff.models import PairStatus
from hexnil.workloads.models import RunStatus, WorkloadRun


def test_verify_configuration_lock_identical():
    matcher = WorkloadRunMatcher()
    v0_hashes = {"startup_01": "hashA", "cpu_01": "hashB"}
    v1_hashes = {"startup_01": "hashA", "cpu_01": "hashB"}

    matched, mismatched = matcher.verify_configuration_lock(v0_hashes, v1_hashes)
    assert matched == ["startup_01", "cpu_01"]
    assert mismatched == []


def test_verify_configuration_lock_mismatch():
    matcher = WorkloadRunMatcher()
    v0_hashes = {"startup_01": "hashA", "cpu_01": "hashB", "memory_01": "hashC"}
    v1_hashes = {"startup_01": "hashA", "cpu_01": "hashB_MODIFIED"}  # memory_01 missing, cpu_01 modified

    matched, mismatched = matcher.verify_configuration_lock(v0_hashes, v1_hashes)
    assert matched == ["startup_01"]
    assert "cpu_01" in mismatched
    assert "memory_01" in mismatched


def test_match_runs_success():
    matcher = WorkloadRunMatcher()
    v0_run = WorkloadRun(
        run_id="RUN-V0-01",
        workload_id="startup_01",
        workload_version="1.0",
        iteration=1,
        status=RunStatus.SUCCESS,
        duration_ms=420.0,
        configuration_hash="hash123",
        experiment_id="EXP-V0",
        started_at="2026-09-13T10:00:00Z",
        ended_at="2026-09-13T10:00:01Z",
    )
    v1_run = WorkloadRun(
        run_id="RUN-V1-01",
        workload_id="startup_01",
        workload_version="1.0",
        iteration=1,
        status=RunStatus.SUCCESS,
        duration_ms=410.0,
        configuration_hash="hash123",
        experiment_id="EXP-V1",
        started_at="2026-09-13T11:00:00Z",
        ended_at="2026-09-13T11:00:01Z",
    )

    hashes = {"startup_01": "hash123"}
    pairs = matcher.match_runs(
        comparison_id="CMP-001",
        v0_runs=[v0_run],
        v1_runs=[v1_run],
        v0_workload_hashes=hashes,
        v1_workload_hashes=hashes,
    )

    assert len(pairs) == 1
    p = pairs[0]
    assert p.pair_status == PairStatus.MATCHED
    assert p.v0_run_id == "RUN-V0-01"
    assert p.v1_run_id == "RUN-V1-01"
    assert p.v0_duration_ms == 420.0
    assert p.v1_duration_ms == 410.0


def test_match_runs_hash_mismatch():
    matcher = WorkloadRunMatcher()
    v0_run = WorkloadRun(
        run_id="RUN-V0-01",
        workload_id="cpu_01",
        workload_version="1.0",
        iteration=1,
        status=RunStatus.SUCCESS,
        duration_ms=1000.0,
        configuration_hash="hash_orig",
        experiment_id="EXP-V0",
        started_at="2026-09-13T10:00:00Z",
        ended_at="2026-09-13T10:00:01Z",
    )
    v1_run = WorkloadRun(
        run_id="RUN-V1-01",
        workload_id="cpu_01",
        workload_version="1.0",
        iteration=1,
        status=RunStatus.SUCCESS,
        duration_ms=900.0,
        configuration_hash="hash_modified",
        experiment_id="EXP-V1",
        started_at="2026-09-13T11:00:00Z",
        ended_at="2026-09-13T11:00:01Z",
    )

    pairs = matcher.match_runs(
        comparison_id="CMP-001",
        v0_runs=[v0_run],
        v1_runs=[v1_run],
        v0_workload_hashes={"cpu_01": "hash_orig"},
        v1_workload_hashes={"cpu_01": "hash_modified"},
    )

    assert len(pairs) == 1
    p = pairs[0]
    assert p.pair_status == PairStatus.CONFIGURATION_MISMATCH
    assert "Configuration hash mismatch" in p.mismatch_reason


def test_match_runs_missing_runs():
    matcher = WorkloadRunMatcher()
    v0_run1 = WorkloadRun(
        run_id="RUN-V0-01",
        workload_id="startup_01",
        workload_version="1.0",
        iteration=1,
        status=RunStatus.SUCCESS,
        duration_ms=400.0,
        configuration_hash="hash1",
        experiment_id="EXP-V0",
        started_at="2026-09-13T10:00:00Z",
        ended_at="2026-09-13T10:00:01Z",
    )
    # V0 has iteration 1, V1 has iteration 2
    v1_run2 = WorkloadRun(
        run_id="RUN-V1-02",
        workload_id="startup_01",
        workload_version="1.0",
        iteration=2,
        status=RunStatus.SUCCESS,
        duration_ms=410.0,
        configuration_hash="hash1",
        experiment_id="EXP-V1",
        started_at="2026-09-13T11:00:00Z",
        ended_at="2026-09-13T11:00:01Z",
    )

    hashes = {"startup_01": "hash1"}
    pairs = matcher.match_runs(
        comparison_id="CMP-001",
        v0_runs=[v0_run1],
        v1_runs=[v1_run2],
        v0_workload_hashes=hashes,
        v1_workload_hashes=hashes,
    )

    assert len(pairs) == 2
    p1 = next(p for p in pairs if p.iteration == 1)
    p2 = next(p for p in pairs if p.iteration == 2)

    assert p1.pair_status == PairStatus.UNMATCHED_V1_MISSING
    assert p2.pair_status == PairStatus.UNMATCHED_V0_MISSING


def test_match_runs_failed_run():
    matcher = WorkloadRunMatcher()
    v0_run = WorkloadRun(
        run_id="RUN-V0-01",
        workload_id="scroll_01",
        workload_version="1.0",
        iteration=1,
        status=RunStatus.SUCCESS,
        duration_ms=500.0,
        configuration_hash="hash1",
        experiment_id="EXP-V0",
        started_at="2026-09-13T10:00:00Z",
        ended_at="2026-09-13T10:00:01Z",
    )
    v1_run = WorkloadRun(
        run_id="RUN-V1-01",
        workload_id="scroll_01",
        workload_version="1.0",
        iteration=1,
        status=RunStatus.FAILED,
        duration_ms=100.0,
        configuration_hash="hash1",
        experiment_id="EXP-V1",
        started_at="2026-09-13T11:00:00Z",
        ended_at="2026-09-13T11:00:01Z",
    )

    hashes = {"scroll_01": "hash1"}
    pairs = matcher.match_runs(
        comparison_id="CMP-001",
        v0_runs=[v0_run],
        v1_runs=[v1_run],
        v0_workload_hashes=hashes,
        v1_workload_hashes=hashes,
    )

    assert len(pairs) == 1
    assert pairs[0].pair_status == PairStatus.INVALID
    assert "One or both runs invalid" in pairs[0].mismatch_reason
