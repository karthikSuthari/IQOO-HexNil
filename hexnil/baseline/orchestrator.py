"""Phase 4 V0 Baseline Experiment Orchestrator."""

import datetime
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from hexnil.baseline.environment import capture_environment_snapshot
from hexnil.baseline.extractor import BaselineMetricExtractor
from hexnil.baseline.identity import capture_v0_software_identity
from hexnil.baseline.models import (
    BaselineMetricSummary,
    EnvironmentSnapshot,
    ProvenanceRecord,
    QualityReport,
    StabilizationPolicy,
    UncertaintyEstimate,
    V0SoftwareIdentity,
    WorkloadProvenance,
)
from hexnil.baseline.quality import evaluate_baseline_quality
from hexnil.baseline.stabilizer import DeviceStabilizer
from hexnil.device.adb import AdbClient
from hexnil.device.models import AdbStatus, DeviceMetadata, ExperimentRecord
from hexnil.experiments.store import ExperimentStore
from hexnil.telemetry.bridge import TelemetryBridge
from hexnil.telemetry.models import TelemetryRecord
from hexnil.workloads.engine import WorkloadExecutionEngine
from hexnil.workloads.models import RunStatus, WorkloadDefinition, WorkloadRun
from hexnil.workloads.registry import WorkloadRegistry

logger = logging.getLogger("hexnil.baseline.orchestrator")

DEFAULT_BASELINE_WORKLOAD_SUITE = [
    "startup_01",
    "cpu_01",
    "memory_01",
    "scroll_01",
    "video_power_01",
]


class BaselineExperimentOrchestrator:
    """Orchestrates creation, execution, and statistical summarization of V0 baseline experiments."""

    def __init__(
        self,
        adb: AdbClient,
        store: ExperimentStore,
        registry: Optional[WorkloadRegistry] = None,
        engine: Optional[WorkloadExecutionEngine] = None,
        bridge: Optional[TelemetryBridge] = None,
    ):
        self.adb = adb
        self.store = store
        self.registry = registry or WorkloadRegistry()
        self.bridge = bridge or TelemetryBridge(adb, store)
        self.engine = engine or WorkloadExecutionEngine(adb, store, self.bridge)
        self.stabilizer = DeviceStabilizer(adb)
        self.extractor = BaselineMetricExtractor()

    def run_baseline_experiment(
        self,
        serial: str,
        iterations: int = 5,
        workload_ids: Optional[List[str]] = None,
        stabilization_policy: Optional[StabilizationPolicy] = None,
        package_name: str = "com.example.iqoo_hexnil",
    ) -> QualityReport:
        """Run a complete, trusted V0 baseline experiment."""
        policy = stabilization_policy or StabilizationPolicy()
        target_suite = workload_ids or DEFAULT_BASELINE_WORKLOAD_SUITE
        contamination_flags: List[str] = []

        # 1. Capture Device & OS Identity
        props = self.adb.get_all_props(serial)
        device_meta = DeviceMetadata(
            serial=serial,
            manufacturer=props.get("ro.product.manufacturer"),
            model=props.get("ro.product.model"),
            codename=props.get("ro.product.device"),
            android_version=props.get("ro.build.version.release"),
            sdk=int(props["ro.build.version.sdk"]) if props.get("ro.build.version.sdk") else None,
            build_id=props.get("ro.build.id"),
            build_fingerprint=props.get("ro.build.fingerprint"),
            abi=props.get("ro.product.cpu.abi"),
        )
        initial_fingerprint = device_meta.build_fingerprint or "unknown"

        # 2. Capture V0 Software Identity
        v0_software = capture_v0_software_identity(self.adb, serial, package_name)

        # 3. Create Phase 4 Experiment Record
        exp_id = self.store.generate_experiment_id()
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        exp_record = ExperimentRecord(
            experiment_id=exp_id,
            created_at=now_iso,
            device=device_meta,
            adb=AdbStatus(state="device", connected=True),
            phase="04_v0_baseline",
            status="running",
        )
        self.store.save(exp_record)
        exp_dir = self.store.ensure_experiment_dir(exp_id)

        # 4. Capture Environment Snapshot & Pre-run Stabilization
        env_snapshot = capture_environment_snapshot(self.adb, serial, package_name)
        stabilization_res = self.stabilizer.stabilize(serial, policy, package_name)
        if not stabilization_res.success:
            contamination_flags.append(
                f"Initial stabilization incomplete: {', '.join(stabilization_res.limitations)}"
            )

        # 5. Load and Validate Workload Definitions
        workload_defs: List[WorkloadDefinition] = []
        for wid in target_suite:
            w_def = self.registry.get(wid)
            workload_defs.append(w_def)

        # Persist software.json, environment.json, workloads.json
        (exp_dir / "software.json").write_text(v0_software.model_dump_json(indent=2), encoding="utf-8")
        (exp_dir / "environment.json").write_text(env_snapshot.model_dump_json(indent=2), encoding="utf-8")
        workloads_data = [
            {
                "workload_id": w.workload_id,
                "version": w.version,
                "configuration_hash": w.compute_hash(),
                "description": w.description,
                "preconditions": w.preconditions,
            }
            for w in workload_defs
        ]
        (exp_dir / "workloads.json").write_text(json.dumps(workloads_data, indent=2), encoding="utf-8")

        # 6. Execute Workload Suite in Deterministic Order
        all_runs: List[WorkloadRun] = []
        all_artifacts: List[str] = []

        for w_def in workload_defs:
            logger.info("Executing workload '%s' for %d iteration(s)", w_def.workload_id, iterations)
            # Execute iterations for this workload
            w_runs = self.engine.execute(
                serial=serial,
                experiment_record=exp_record,
                workload=w_def,
                iterations=iterations,
                package_name=package_name,
            )
            all_runs.extend(w_runs)
            for r in w_runs:
                all_artifacts.extend(r.artifacts)

            # Check build fingerprint continuity between workloads
            current_props = self.adb.get_all_props(serial)
            current_fp = current_props.get("ro.build.fingerprint") or "unknown"
            if current_fp != initial_fingerprint:
                contamination_flags.append(
                    f"Build fingerprint mismatch during baseline execution: {initial_fingerprint} -> {current_fp}"
                )

        # 7. Collect all Telemetry Records
        telemetry_records = self.store.load_telemetry(exp_id)

        # 8. Baseline Metric Extraction & Statistical Summaries
        summaries, uncertainties = self.extractor.extract_metrics(all_runs, telemetry_records)

        # 9. Evaluate Baseline Quality
        dev_display = f"{device_meta.manufacturer or ''} {device_meta.model or ''}".strip()
        quality_report = evaluate_baseline_quality(
            experiment_id=exp_id,
            device_serial=serial,
            device_model=dev_display,
            v0_software=v0_software,
            workloads_requested=target_suite,
            iterations_requested_per_workload=iterations,
            runs=all_runs,
            telemetry_records=telemetry_records,
            artifacts=all_artifacts,
            contamination_flags=contamination_flags,
        )

        # 10. Construct Provenance & Integrity Hashes
        workload_provenance: Dict[str, WorkloadProvenance] = {}
        for w_def in workload_defs:
            matching_runs = [r for r in all_runs if r.workload_id == w_def.workload_id]
            valid_ids = [r.run_id for r in matching_runs if r.status == RunStatus.SUCCESS]
            all_ids = [r.run_id for r in matching_runs]
            workload_provenance[w_def.workload_id] = WorkloadProvenance(
                workload_id=w_def.workload_id,
                workload_version=w_def.version,
                configuration_hash=w_def.compute_hash(),
                run_ids=all_ids,
                valid_run_ids=valid_ids,
                telemetry_files=["telemetry/android.jsonl", "telemetry/adb.jsonl"],
            )

        # Calculate artifact hashes
        artifact_hashes: Dict[str, str] = {}
        artifacts_dir = exp_dir / "artifacts"
        if artifacts_dir.exists():
            for art_file in artifacts_dir.glob("*"):
                if art_file.is_file():
                    content = art_file.read_bytes()
                    artifact_hashes[f"artifacts/{art_file.name}"] = hashlib.sha256(content).hexdigest()

        telemetry_dir = exp_dir / "telemetry"
        if telemetry_dir.exists():
            for tel_file in telemetry_dir.glob("*.jsonl"):
                if tel_file.is_file():
                    content = tel_file.read_bytes()
                    artifact_hashes[f"telemetry/{tel_file.name}"] = hashlib.sha256(content).hexdigest()

        provenance = ProvenanceRecord(
            experiment_id=exp_id,
            analysis_version="1.0.0",
            created_at=now_iso,
            device_serial=serial,
            build_fingerprint=initial_fingerprint,
            apk_sha256=v0_software.apk_sha256,
            workloads=workload_provenance,
            artifact_hashes=artifact_hashes,
        )

        # 11. Persist Baseline Directory
        baseline_dir = exp_dir / "baseline"
        baseline_dir.mkdir(parents=True, exist_ok=True)

        # Format metrics.json with summaries and uncertainty estimates
        metrics_output = {
            "experiment_id": exp_id,
            "analysis_version": "1.0.0",
            "computed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "workloads": {},
        }
        for wid in summaries:
            metrics_output["workloads"][wid] = {}
            for mname, s_obj in summaries[wid].items():
                u_obj = uncertainties.get(wid, {}).get(mname)
                metrics_output["workloads"][wid][mname] = {
                    "summary": s_obj.model_dump(),
                    "uncertainty": u_obj.model_dump() if u_obj else None,
                }

        (baseline_dir / "metrics.json").write_text(json.dumps(metrics_output, indent=2), encoding="utf-8")
        (baseline_dir / "quality.json").write_text(quality_report.model_dump_json(indent=2), encoding="utf-8")
        (baseline_dir / "provenance.json").write_text(provenance.model_dump_json(indent=2), encoding="utf-8")

        # 12. Update final ExperimentRecord status
        exp_record.status = "completed" if quality_report.is_clean_baseline else "contaminated"
        self.store.save(exp_record)

        logger.info(
            "V0 Baseline Experiment %s finished with verdict: %s",
            exp_id,
            quality_report.summary_verdict,
        )
        return quality_report
