"""Unit tests for WorkloadRegistry discovery and validation."""

import pytest
from hexnil.workloads.models import StepAction, WorkloadDefinition, WorkloadStep
from hexnil.workloads.registry import WorkloadNotFoundError, WorkloadRegistry


def test_registry_discovery():
    registry = WorkloadRegistry()
    workloads = registry.list_workloads()
    ids = [w.workload_id for w in workloads]

    assert "startup_01" in ids
    assert "cpu_01" in ids
    assert "memory_01" in ids
    assert "scroll_01" in ids
    assert "video_power_01" in ids


def test_registry_get_success_and_not_found():
    registry = WorkloadRegistry()
    cpu_wl = registry.get("cpu_01")
    assert cpu_wl.workload_id == "cpu_01"
    assert cpu_wl.version == "1.0.0"
    assert len(cpu_wl.steps) == 3

    with pytest.raises(WorkloadNotFoundError) as exc_info:
        registry.get("nonexistent_workload_999")
    assert "not found" in str(exc_info.value)


def test_registry_validation_success_and_errors():
    registry = WorkloadRegistry()
    valid, errors = registry.validate("startup_01")
    assert valid is True
    assert errors == []

    # Programmatic invalid workload: empty steps
    bad_wl = WorkloadDefinition(
        workload_id="bad_wl",
        version="1.0.0",
        description="Bad workload",
        steps=[],
    )
    registry.register(bad_wl)
    valid, errors = registry.validate("bad_wl")
    assert valid is False
    assert any("at least one step" in e for e in errors)
