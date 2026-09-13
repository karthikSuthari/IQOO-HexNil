"""Baseline quality evaluation and auditing."""

import logging
from typing import List

from hexnil.baseline.models import QualityReport, V0SoftwareIdentity
from hexnil.telemetry.models import TelemetryRecord
from hexnil.workloads.models import RunStatus, WorkloadRun

logger = logging.getLogger("hexnil.baseline.quality")


def evaluate_baseline_quality(
    experiment_id: str,
    device_serial: str,
    device_model: str,
    v0_software: V0SoftwareIdentity,
    workloads_requested: List[str],
    iterations_requested_per_workload: int,
    runs: List[WorkloadRun],
    telemetry_records: List[TelemetryRecord],
    artifacts: List[str],
    contamination_flags: List[str],
) -> QualityReport:
    """Audit baseline execution completeness, evidence coverage, and contamination."""
    total_requested = len(workloads_requested) * iterations_requested_per_workload
    total_completed = len(runs)

    valid_runs = [r for r in runs if r.status == RunStatus.SUCCESS]
    invalid_runs = [r for r in runs if r.status == RunStatus.INVALID]
    failed_runs = [r for r in runs if r.status in (RunStatus.FAILED, RunStatus.TIMEOUT)]
    precond_failed_runs = [r for r in runs if r.status == RunStatus.PRECONDITION_FAILED]

    valid_workload_ids = {r.workload_id for r in valid_runs}
    workloads_covered = sum(1 for w in workloads_requested if w in valid_workload_ids)
    evidence_coverage = f"{workloads_covered}/{len(workloads_requested)} workloads validated with evidence"

    # Check for additional contamination triggers
    flags = list(contamination_flags)
    if precond_failed_runs:
        flags.append(f"{len(precond_failed_runs)} run(s) failed preconditions")
    if failed_runs:
        flags.append(f"{len(failed_runs)} run(s) failed during execution")
    if total_completed < total_requested:
        flags.append(f"Incomplete execution: {total_completed}/{total_requested} iterations completed")

    # Determine summary verdict
    if contamination_flags or any("build fingerprint mismatch" in f.lower() for f in flags):
        verdict = "CONTAMINATED_BASELINE"
        is_clean = False
    elif workloads_covered < len(workloads_requested) or len(valid_runs) == 0:
        verdict = "INSUFFICIENT_DATA"
        is_clean = False
    elif len(valid_runs) == total_requested and not precond_failed_runs and not failed_runs:
        verdict = "TRUSTED_V0_BASELINE"
        is_clean = True
    else:
        # Some runs were valid, but some had failures
        verdict = "PARTIAL_V0_BASELINE"
        is_clean = False

    return QualityReport(
        experiment_id=experiment_id,
        baseline_type="V0",
        device_serial=device_serial,
        device_model=device_model,
        v0_software=v0_software.model_dump(),
        workloads_requested=workloads_requested,
        iterations_requested_per_workload=iterations_requested_per_workload,
        total_iterations_requested=total_requested,
        total_runs_completed=total_completed,
        valid_runs_count=len(valid_runs),
        invalid_runs_count=len(invalid_runs),
        failed_runs_count=len(failed_runs),
        precondition_failures_count=len(precond_failed_runs),
        telemetry_records_count=len(telemetry_records),
        artifacts_count=len(artifacts),
        evidence_coverage=evidence_coverage,
        contamination_flags=flags,
        is_clean_baseline=is_clean,
        summary_verdict=verdict,
    )
