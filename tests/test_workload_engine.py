"""Unit tests for WorkloadExecutionEngine."""

from unittest.mock import MagicMock, patch
import pytest

from hexnil.device.models import AdbStatus, DeviceMetadata, ExperimentRecord
from hexnil.experiments.store import ExperimentStore
from hexnil.workloads.engine import WorkloadExecutionEngine
from hexnil.workloads.models import (
    PreconditionResult,
    PreconditionStatus,
    RunStatus,
    StepAction,
    WorkloadDefinition,
    WorkloadStep,
)


def test_workload_engine_single_iteration_success(tmp_path):
    mock_adb = MagicMock()
    mock_adb.run_serial_cmd.return_value = ""

    store = ExperimentStore(tmp_path)
    mock_bridge = MagicMock()
    mock_bridge.collect_all.return_value = ([], [], MagicMock(artifacts=["test_logcat.txt"]))

    engine = WorkloadExecutionEngine(mock_adb, store, bridge=mock_bridge)
    # Stub evaluator to always return SATISFIED
    engine.evaluator.evaluate_all = MagicMock(return_value={
        "screen_on": PreconditionResult(
            name="screen_on", status=PreconditionStatus.SATISFIED, expected_value=True
        )
    })

    workload = WorkloadDefinition(
        workload_id="test_engine_wl",
        version="1.0.0",
        description="Engine test",
        configuration={"key": "val"},
        preconditions={"screen_on": True},
        steps=[
            WorkloadStep(step_id="step_wait", action=StepAction.WAIT, parameters={"duration_ms": 10}),
            WorkloadStep(step_id="step_snap", action=StepAction.COLLECT_SNAPSHOT, parameters={}),
        ],
    )

    exp_rec = ExperimentRecord(
        experiment_id="EXP-20260913-001",
        created_at="2026-09-13T12:00:00Z",
        device=DeviceMetadata(serial="SERIAL_TEST"),
        adb=AdbStatus(state="device", connected=True),
    )

    runs = engine.execute(
        serial="SERIAL_TEST",
        experiment_record=exp_rec,
        workload=workload,
        iterations=2,
    )

    assert len(runs) == 2
    # Check iteration 1
    assert runs[0].iteration == 1
    assert runs[0].status == RunStatus.SUCCESS
    assert runs[0].duration_ms > 0
    assert runs[0].workload_id == "test_engine_wl"
    assert runs[0].configuration_hash == workload.compute_hash()
    assert len(runs[0].steps) == 2

    # Check iteration 2 has unique run_id but same configuration_hash
    assert runs[1].iteration == 2
    assert runs[1].run_id != runs[0].run_id
    assert runs[1].configuration_hash == runs[0].configuration_hash

    # Verify runs were persisted to store
    saved_runs = store.list_workload_runs("EXP-20260913-001", "test_engine_wl")
    assert len(saved_runs) == 2


def test_workload_engine_precondition_failure(tmp_path):
    mock_adb = MagicMock()
    store = ExperimentStore(tmp_path)
    engine = WorkloadExecutionEngine(mock_adb, store)

    engine.evaluator.evaluate_all = MagicMock(return_value={
        "battery_min_percent": PreconditionResult(
            name="battery_min_percent",
            status=PreconditionStatus.NOT_SATISFIED,
            expected_value=50,
            actual_value=12,
            message="Battery too low",
        )
    })

    workload = WorkloadDefinition(
        workload_id="fail_precond_wl",
        version="1.0.0",
        description="Fail precond",
        preconditions={"battery_min_percent": 50},
        steps=[WorkloadStep(step_id="step1", action=StepAction.WAIT, parameters={})],
    )

    exp_rec = ExperimentRecord(
        experiment_id="EXP-20260913-002",
        created_at="2026-09-13T12:00:00Z",
        device=DeviceMetadata(serial="SERIAL_TEST"),
        adb=AdbStatus(state="device", connected=True),
    )

    runs = engine.execute(
        serial="SERIAL_TEST",
        experiment_record=exp_rec,
        workload=workload,
        iterations=1,
    )

    assert len(runs) == 1
    assert runs[0].status == RunStatus.PRECONDITION_FAILED
    assert "preconditions" in runs[0].error_reason.lower()
    assert len(runs[0].steps) == 0  # Steps must not have run
