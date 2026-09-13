"""Unit tests for Phase 3 Workload domain models and configuration hashing."""

import pytest
from hexnil.workloads.models import (
    DurationLimits,
    PreconditionStatus,
    RunStatus,
    StepAction,
    StepResult,
    WorkloadDefinition,
    WorkloadRun,
    WorkloadStep,
)


def test_workload_definition_canonical_hash():
    # Construct definition with arbitrary key ordering
    def1 = WorkloadDefinition(
        workload_id="test_workload",
        version="1.0.0",
        description="Test workload 1",
        configuration={
            "z_param": 100,
            "a_param": "alpha",
            "nested": {"beta": 2, "alpha": 1},
        },
        steps=[
            WorkloadStep(step_id="step_1", action=StepAction.WAIT, parameters={"duration_ms": 100})
        ],
    )

    # Identical config constructed with different insertion order
    def2 = WorkloadDefinition(
        workload_id="test_workload",
        version="1.0.0",
        description="Test workload 1 with different description",
        configuration={
            "nested": {"alpha": 1, "beta": 2},
            "a_param": "alpha",
            "z_param": 100,
        },
        steps=[
            WorkloadStep(step_id="step_1", action=StepAction.WAIT, parameters={"duration_ms": 100})
        ],
    )

    # Both must produce identical canonical JSON and identical configuration hash
    assert def1.canonical_json() == def2.canonical_json()
    assert def1.compute_hash() == def2.compute_hash()
    assert len(def1.compute_hash()) == 16


def test_workload_hash_sensitivity():
    base_def = WorkloadDefinition(
        workload_id="test_workload",
        version="1.0.0",
        description="Base workload",
        configuration={"operations": 5000, "seed": "seed_val"},
    )

    modified_def = WorkloadDefinition(
        workload_id="test_workload",
        version="1.0.0",
        description="Modified workload",
        configuration={"operations": 5001, "seed": "seed_val"},
    )

    assert base_def.compute_hash() != modified_def.compute_hash()


def test_workload_run_serialization():
    run = WorkloadRun(
        experiment_id="EXP-20260913-001",
        run_id="RUN-20260913-120000-001-A1B2",
        workload_id="cpu_01",
        workload_version="1.0.0",
        configuration_hash="6e7f4490bb4eef72",
        iteration=1,
        started_at="2026-09-13T12:00:00Z",
        ended_at="2026-09-13T12:00:01Z",
        duration_ms=1024.5,
        status=RunStatus.SUCCESS,
        steps=[
            StepResult(
                step_id="compute_1",
                action=StepAction.COMPUTE_WORK,
                status=RunStatus.SUCCESS,
                started_at="2026-09-13T12:00:00.100Z",
                ended_at="2026-09-13T12:00:01.000Z",
                duration_ms=900.0,
            )
        ],
        telemetry_count=42,
        artifacts=["logcat.txt"],
    )

    json_str = run.model_dump_json()
    reloaded = WorkloadRun.model_validate_json(json_str)

    assert reloaded.experiment_id == "EXP-20260913-001"
    assert reloaded.run_id == "RUN-20260913-120000-001-A1B2"
    assert reloaded.configuration_hash == "6e7f4490bb4eef72"
    assert reloaded.duration_ms == 1024.5
    assert reloaded.status == RunStatus.SUCCESS
    assert len(reloaded.steps) == 1
    assert reloaded.steps[0].action == StepAction.COMPUTE_WORK
