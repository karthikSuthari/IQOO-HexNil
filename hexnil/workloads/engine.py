"""Deterministic workload execution engine with monotonic timing."""

import datetime
import logging
import time
from typing import Any, Dict, List, Optional
import uuid

from hexnil.device.adb import AdbClient
from hexnil.device.models import ExperimentRecord
from hexnil.experiments.store import ExperimentStore
from hexnil.telemetry.bridge import TelemetryBridge
from hexnil.workloads.models import (
    PreconditionStatus,
    RunStatus,
    StepAction,
    StepResult,
    WorkloadDefinition,
    WorkloadRun,
    WorkloadStep,
)
from hexnil.workloads.preconditions import PreconditionEvaluator

logger = logging.getLogger("hexnil.workloads.engine")


class WorkloadExecutionEngine:
    """Executes versioned declarative workloads deterministically."""

    def __init__(
        self,
        adb: AdbClient,
        store: ExperimentStore,
        bridge: Optional[TelemetryBridge] = None,
    ):
        self.adb = adb
        self.store = store
        self.bridge = bridge or TelemetryBridge(adb, store)
        self.evaluator = PreconditionEvaluator(adb)

    def generate_run_id(self, iteration: int) -> str:
        """Generate a unique run ID."""
        now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H%M%S")
        rand_suffix = uuid.uuid4().hex[:4].upper()
        return f"RUN-{now_str}-{iteration:03d}-{rand_suffix}"

    def execute(
        self,
        serial: str,
        experiment_record: ExperimentRecord,
        workload: WorkloadDefinition,
        iterations: int = 1,
        package_name: str = "com.example.iqoo_hexnil",
    ) -> List[WorkloadRun]:
        """Execute a workload across one or more repeated iterations."""
        exp_id = experiment_record.experiment_id
        config_hash = workload.compute_hash()
        runs: List[WorkloadRun] = []

        logger.info(
            "Starting execution of workload '%s' (v%s, hash: %s) for %d iteration(s)",
            workload.workload_id,
            workload.version,
            config_hash,
            iterations,
        )

        for i in range(1, iterations + 1):
            run = self.execute_single_iteration(
                serial=serial,
                experiment_record=experiment_record,
                workload=workload,
                iteration=i,
                config_hash=config_hash,
                package_name=package_name,
            )
            # Persist run
            self.store.save_workload_run(exp_id, run)
            runs.append(run)

        return runs

    def execute_single_iteration(
        self,
        serial: str,
        experiment_record: ExperimentRecord,
        workload: WorkloadDefinition,
        iteration: int,
        config_hash: str,
        package_name: str = "com.example.iqoo_hexnil",
    ) -> WorkloadRun:
        """Execute a single deterministic workload iteration with monotonic timing."""
        exp_id = experiment_record.experiment_id
        run_id = self.generate_run_id(iteration)

        # Monotonic clock for run duration
        run_start_ns = time.perf_counter_ns()
        run_start_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # 1. Evaluate Preconditions
        preconditions_results = self.evaluator.evaluate_all(
            serial=serial,
            preconditions=workload.preconditions,
            package_name=package_name,
        )

        preconditions_failed = any(
            r.status in (PreconditionStatus.NOT_SATISFIED, PreconditionStatus.ERROR)
            for r in preconditions_results.values()
        )

        if preconditions_failed:
            run_end_ns = time.perf_counter_ns()
            duration_ms = (run_end_ns - run_start_ns) / 1_000_000.0
            run_end_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

            logger.warning("Preconditions failed for workload %s, run %s", workload.workload_id, run_id)
            return WorkloadRun(
                experiment_id=exp_id,
                run_id=run_id,
                workload_id=workload.workload_id,
                workload_version=workload.version,
                configuration_hash=config_hash,
                iteration=iteration,
                started_at=run_start_iso,
                ended_at=run_end_iso,
                duration_ms=round(duration_ms, 3),
                status=RunStatus.PRECONDITION_FAILED,
                preconditions=preconditions_results,
                steps=[],
                error_reason="One or more declared preconditions were not satisfied",
            )

        # 2. Execute Steps
        step_results: List[StepResult] = []
        overall_status = RunStatus.SUCCESS
        error_reason: Optional[str] = None
        artifacts_collected: List[str] = []
        telemetry_records_count = 0

        for step in workload.steps:
            step_result = self._execute_step(
                serial=serial,
                experiment_record=experiment_record,
                step=step,
                run_id=run_id,
                iteration=iteration,
                package_name=package_name,
            )
            step_results.append(step_result)

            if "artifacts" in step_result.details:
                artifacts_collected.extend(step_result.details["artifacts"])
            if "telemetry_count" in step_result.details:
                telemetry_records_count += step_result.details["telemetry_count"]

            if step_result.status != RunStatus.SUCCESS:
                overall_status = step_result.status
                error_reason = step_result.error
                logger.error("Step %s failed with status %s: %s", step.step_id, step_result.status, step_result.error)
                break

        run_end_ns = time.perf_counter_ns()
        duration_ms = (run_end_ns - run_start_ns) / 1_000_000.0
        run_end_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # 3. Check Duration Limits
        if overall_status == RunStatus.SUCCESS and workload.duration_limits:
            limits = workload.duration_limits
            if limits.max_ms is not None and duration_ms > limits.max_ms:
                overall_status = RunStatus.INVALID
                error_reason = f"Execution duration ({duration_ms:.1f} ms) exceeded maximum limit ({limits.max_ms} ms)"
            elif limits.min_ms is not None and duration_ms < limits.min_ms:
                overall_status = RunStatus.INVALID
                error_reason = f"Execution duration ({duration_ms:.1f} ms) below minimum limit ({limits.min_ms} ms)"

        return WorkloadRun(
            experiment_id=exp_id,
            run_id=run_id,
            workload_id=workload.workload_id,
            workload_version=workload.version,
            configuration_hash=config_hash,
            iteration=iteration,
            started_at=run_start_iso,
            ended_at=run_end_iso,
            duration_ms=round(duration_ms, 3),
            status=overall_status,
            preconditions=preconditions_results,
            steps=step_results,
            telemetry_count=telemetry_records_count,
            artifacts=artifacts_collected,
            error_reason=error_reason,
        )

    def _execute_step(
        self,
        serial: str,
        experiment_record: ExperimentRecord,
        step: WorkloadStep,
        run_id: str,
        iteration: int,
        package_name: str,
    ) -> StepResult:
        """Execute a single workload step with monotonic duration timing."""
        start_ns = time.perf_counter_ns()
        start_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        status = RunStatus.SUCCESS
        error: Optional[str] = None
        details: Dict[str, Any] = {}

        try:
            if step.action == StepAction.LAUNCH_APP:
                activity = step.parameters.get("activity", ".MainActivity")
                component = f"{package_name}/{activity}" if not activity.startswith(package_name) else activity
                cmd = [
                    "shell",
                    "am",
                    "start",
                    "-n",
                    component,
                    "-a",
                    "com.example.iqoo_hexnil.ACTION_RUN_WORKLOAD",
                    "--es",
                    "experiment_id",
                    experiment_record.experiment_id,
                    "--es",
                    "run_id",
                    run_id,
                    "--ei",
                    "iteration",
                    str(iteration),
                ]
                self.adb.run_serial_cmd(serial, cmd, check=True)
                time.sleep(1.0)  # Stabilize initial window

            elif step.action == StepAction.STOP_APP:
                pkg = step.parameters.get("package", package_name)
                self.adb.run_serial_cmd(serial, ["shell", "am", "force-stop", pkg], check=True)

            elif step.action == StepAction.WAIT:
                duration = step.parameters.get("duration_ms", 1000) / 1000.0
                time.sleep(duration)

            elif step.action == StepAction.WAIT_FOR_IDLE:
                time.sleep(0.5)

            elif step.action == StepAction.SCROLL:
                swipes = step.parameters.get("scroll_swipes", 3)
                swipe_dur = step.parameters.get("swipe_duration_ms", 300)
                # Deterministic swipe coordinates: middle-bottom to middle-top
                for _ in range(swipes):
                    self.adb.run_serial_cmd(
                        serial,
                        ["shell", "input", "swipe", "500", "1500", "500", "700", str(swipe_dur)],
                        check=False,
                    )
                    time.sleep(0.4)

            elif step.action in (StepAction.COMPUTE_WORK, StepAction.MEMORY_WORK, StepAction.LOCAL_MEDIA_PLAYBACK):
                # Trigger on-device action via intent
                action_name = step.action.value
                cmd = [
                    "shell",
                    "am",
                    "start",
                    "-n",
                    f"{package_name}/.MainActivity",
                    "-a",
                    "com.example.iqoo_hexnil.ACTION_RUN_WORKLOAD",
                    "--es",
                    "experiment_id",
                    experiment_record.experiment_id,
                    "--es",
                    "run_id",
                    run_id,
                    "--es",
                    "workload_action",
                    action_name,
                    "--ei",
                    "operations_count",
                    str(step.parameters.get("operations_count", 5000)),
                ]
                self.adb.run_serial_cmd(serial, cmd, check=True)
                # Wait for execution to complete
                wait_dur = step.parameters.get("playback_duration_ms") or 2000
                time.sleep((wait_dur / 1000.0) + 1.0)

            elif step.action == StepAction.COLLECT_SNAPSHOT:
                # Integrate Phase 2 Universal Telemetry snapshot
                android_records, adb_records, summary = self.bridge.collect_all(
                    serial=serial,
                    experiment_record=experiment_record,
                    workload_id=step.parameters.get("workload_id", "workload_step"),
                    package_name=package_name,
                )
                details["telemetry_count"] = len(android_records) + len(adb_records)
                details["artifacts"] = summary.artifacts

            else:
                status = RunStatus.UNSUPPORTED
                error = f"Unsupported step action: {step.action}"

        except Exception as exc:
            status = RunStatus.FAILED
            error = str(exc)

        end_ns = time.perf_counter_ns()
        duration_ms = (end_ns - start_ns) / 1_000_000.0
        end_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        return StepResult(
            step_id=step.step_id,
            action=step.action,
            status=status,
            started_at=start_iso,
            ended_at=end_iso,
            duration_ms=round(duration_ms, 3),
            error=error,
            details=details,
        )
