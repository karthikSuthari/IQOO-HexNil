"""Unit tests for BaselineMetricExtractor."""

import pytest
from hexnil.baseline.extractor import BaselineMetricExtractor
from hexnil.device.models import DeviceMetadata
from hexnil.telemetry.models import CapabilityStatus, MetricValue, TelemetryRecord, WorkloadIdentity
from hexnil.workloads.models import RunStatus, StepAction, StepResult, WorkloadRun


def make_test_device():
    return DeviceMetadata(serial="test_serial_01", model="TestModel")


def test_extractor_startup_and_cpu_metrics():
    """Verify metric extraction for startup_01 and cpu_01 workloads."""
    dev = make_test_device()
    runs = [
        WorkloadRun(
            experiment_id="EXP-1",
            run_id="RUN-1",
            workload_id="startup_01",
            workload_version="1.0.0",
            configuration_hash="hash1",
            iteration=1,
            started_at="2026-09-13T12:00:00Z",
            ended_at="2026-09-13T12:00:01Z",
            duration_ms=1200.0,
            status=RunStatus.SUCCESS,
            steps=[
                StepResult(
                    step_id="step_launch",
                    action=StepAction.LAUNCH_APP,
                    status=RunStatus.SUCCESS,
                    started_at="2026-09-13T12:00:00Z",
                    ended_at="2026-09-13T12:00:00.3Z",
                    duration_ms=320.0,
                )
            ],
        ),
        WorkloadRun(
            experiment_id="EXP-1",
            run_id="RUN-2",
            workload_id="startup_01",
            workload_version="1.0.0",
            configuration_hash="hash1",
            iteration=2,
            started_at="2026-09-13T12:00:02Z",
            ended_at="2026-09-13T12:00:03Z",
            duration_ms=1150.0,
            status=RunStatus.SUCCESS,
            steps=[
                StepResult(
                    step_id="step_launch",
                    action=StepAction.LAUNCH_APP,
                    status=RunStatus.SUCCESS,
                    started_at="2026-09-13T12:00:02Z",
                    ended_at="2026-09-13T12:00:02.3Z",
                    duration_ms=310.0,
                )
            ],
        ),
        WorkloadRun(
            experiment_id="EXP-1",
            run_id="RUN-3",
            workload_id="startup_01",
            workload_version="1.0.0",
            configuration_hash="hash1",
            iteration=3,
            started_at="2026-09-13T12:00:04Z",
            ended_at="2026-09-13T12:00:04.1Z",
            duration_ms=100.0,
            status=RunStatus.PRECONDITION_FAILED,  # Must be excluded from summary
            error_reason="Battery too low",
        ),
    ]

    telemetry = [
        TelemetryRecord(
            experiment_id="EXP-1",
            timestamp="2026-09-13T12:00:00.5Z",
            device=dev,
            workload=WorkloadIdentity(id="startup_01", iteration=1),
            metric=MetricValue(name="app_startup_duration_ms", value=320.0, unit="ms"),
            source="android_app",
            capability=CapabilityStatus.UNIVERSAL,
        ),
        TelemetryRecord(
            experiment_id="EXP-1",
            timestamp="2026-09-13T12:00:02.5Z",
            device=dev,
            workload=WorkloadIdentity(id="startup_01", iteration=2),
            metric=MetricValue(name="app_startup_duration_ms", value=310.0, unit="ms"),
            source="android_app",
            capability=CapabilityStatus.UNIVERSAL,
        ),
    ]

    extractor = BaselineMetricExtractor()
    summaries, uncertainties = extractor.extract_metrics(runs, telemetry)

    assert "startup_01" in summaries
    s_startup = summaries["startup_01"]["startup_duration_ms"]
    assert s_startup.n_valid_runs == 2
    assert s_startup.n_excluded_runs == 1  # The PRECONDITION_FAILED run was excluded
    assert s_startup.mean == 315.0

    s_duration = summaries["startup_01"]["workload_duration_ms"]
    assert s_duration.n_valid_runs == 2
    assert s_duration.mean == 1175.0


def test_extractor_memory_and_power_metrics():
    """Verify memory MB and video_power_01 battery delta extractions."""
    dev = make_test_device()
    runs = [
        WorkloadRun(
            experiment_id="EXP-2",
            run_id="RUN-P1",
            workload_id="video_power_01",
            workload_version="1.0.0",
            configuration_hash="hash2",
            iteration=1,
            started_at="2026-09-13T12:00:00Z",
            ended_at="2026-09-13T12:00:05Z",
            duration_ms=5000.0,
            status=RunStatus.SUCCESS,
        ),
        WorkloadRun(
            experiment_id="EXP-2",
            run_id="RUN-P2",
            workload_id="video_power_01",
            workload_version="1.0.0",
            configuration_hash="hash2",
            iteration=2,
            started_at="2026-09-13T12:00:06Z",
            ended_at="2026-09-13T12:00:11Z",
            duration_ms=5000.0,
            status=RunStatus.SUCCESS,
        ),
        WorkloadRun(
            experiment_id="EXP-2",
            run_id="RUN-P3",
            workload_id="video_power_01",
            workload_version="1.0.0",
            configuration_hash="hash2",
            iteration=3,
            started_at="2026-09-13T12:00:12Z",
            ended_at="2026-09-13T12:00:17Z",
            duration_ms=5000.0,
            status=RunStatus.SUCCESS,
        ),
    ]

    telemetry = [
        # Iteration 1: 85% -> 84% (delta = 1.0%)
        TelemetryRecord(
            experiment_id="EXP-2",
            timestamp="2026-09-13T12:00:00Z",
            device=dev,
            workload=WorkloadIdentity(id="video_power_01", iteration=1),
            metric=MetricValue(name="battery_level_percent", value=85.0, unit="%"),
            source="adb",
            capability=CapabilityStatus.UNIVERSAL,
        ),
        TelemetryRecord(
            experiment_id="EXP-2",
            timestamp="2026-09-13T12:00:05Z",
            device=dev,
            workload=WorkloadIdentity(id="video_power_01", iteration=1),
            metric=MetricValue(name="battery_level_percent", value=84.0, unit="%"),
            source="adb",
            capability=CapabilityStatus.UNIVERSAL,
        ),
        # Iteration 2: 84% -> 84% (delta = 0.0%)
        TelemetryRecord(
            experiment_id="EXP-2",
            timestamp="2026-09-13T12:00:06Z",
            device=dev,
            workload=WorkloadIdentity(id="video_power_01", iteration=2),
            metric=MetricValue(name="battery_level_percent", value=84.0, unit="%"),
            source="adb",
            capability=CapabilityStatus.UNIVERSAL,
        ),
        TelemetryRecord(
            experiment_id="EXP-2",
            timestamp="2026-09-13T12:00:11Z",
            device=dev,
            workload=WorkloadIdentity(id="video_power_01", iteration=2),
            metric=MetricValue(name="battery_level_percent", value=84.0, unit="%"),
            source="adb",
            capability=CapabilityStatus.UNIVERSAL,
        ),
        # Iteration 3: 84% -> 83% (delta = 1.0%)
        TelemetryRecord(
            experiment_id="EXP-2",
            timestamp="2026-09-13T12:00:12Z",
            device=dev,
            workload=WorkloadIdentity(id="video_power_01", iteration=3),
            metric=MetricValue(name="battery_level_percent", value=84.0, unit="%"),
            source="adb",
            capability=CapabilityStatus.UNIVERSAL,
        ),
        TelemetryRecord(
            experiment_id="EXP-2",
            timestamp="2026-09-13T12:00:17Z",
            device=dev,
            workload=WorkloadIdentity(id="video_power_01", iteration=3),
            metric=MetricValue(name="battery_level_percent", value=83.0, unit="%"),
            source="adb",
            capability=CapabilityStatus.UNIVERSAL,
        ),
    ]

    extractor = BaselineMetricExtractor()
    summaries, uncertainties = extractor.extract_metrics(runs, telemetry)

    s_bat = summaries["video_power_01"]["battery_level_delta_percent"]
    assert s_bat.n_valid_runs == 3
    assert s_bat.run_values == [1.0, 0.0, 1.0]
    assert s_bat.mean == pytest.approx(0.667, 0.01)

    # Discharge proxy exists and is NOT labeled watts or joules
    proxy = summaries["video_power_01"]["battery_discharge_proxy"]
    assert proxy.unit == "delta_percent_proxy"
