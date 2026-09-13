"""Differential Experiment Orchestrator coordinating V0 baseline and V1 update evidence."""

import datetime
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from hexnil.baseline.environment import capture_environment_snapshot
from hexnil.baseline.models import (
    ProvenanceRecord,
    StabilizationPolicy,
    WorkloadProvenance,
)
from hexnil.baseline.stabilizer import DeviceStabilizer
from hexnil.device.adb import AdbClient
from hexnil.device.models import AdbStatus, DeviceMetadata, ExperimentRecord
from hexnil.diff.environment import compare_environment_snapshots
from hexnil.diff.installer import ApkInstaller, capture_v1_software_identity
from hexnil.diff.matcher import WorkloadRunMatcher
from hexnil.diff.models import (
    ComparisonQualityReport,
    ComparisonRecord,
    ComparisonRunPair,
    InstallOutcome,
    InstallResult,
    PairStatus,
)
from hexnil.diff.quality import evaluate_comparison_quality
from hexnil.diff.store import ComparisonStore
from hexnil.exceptions import HexnilError
from hexnil.experiments.store import ExperimentStore
from hexnil.telemetry.bridge import TelemetryBridge
from hexnil.workloads.engine import WorkloadExecutionEngine
from hexnil.workloads.models import WorkloadDefinition, WorkloadRun
from hexnil.workloads.registry import WorkloadRegistry

logger = logging.getLogger("hexnil.diff.orchestrator")


class DifferentialExperimentOrchestrator:
    """Orchestrates V0 -> V1 differential experiments, update installation, and matched run pairing."""

    def __init__(
        self,
        adb: AdbClient,
        exp_store: ExperimentStore,
        comp_store: ComparisonStore,
        registry: Optional[WorkloadRegistry] = None,
        engine: Optional[WorkloadExecutionEngine] = None,
        bridge: Optional[TelemetryBridge] = None,
    ):
        self.adb = adb
        self.exp_store = exp_store
        self.comp_store = comp_store
        self.registry = registry or WorkloadRegistry()
        self.bridge = bridge or TelemetryBridge(adb, exp_store)
        self.engine = engine or WorkloadExecutionEngine(adb, exp_store, self.bridge)
        self.installer = ApkInstaller(adb)
        self.stabilizer = DeviceStabilizer(adb)
        self.matcher = WorkloadRunMatcher()

    def inspect_v0_baseline(self, v0_experiment_id: str) -> Dict[str, object]:
        """Inspect and validate readiness of a Phase 4 V0 baseline experiment."""
        v0_record = self.exp_store.load(v0_experiment_id)
        v0_quality = self.exp_store.load_baseline_quality(v0_experiment_id)
        v0_software = self.exp_store.load_v0_software(v0_experiment_id)
        v0_env = self.exp_store.load_environment(v0_experiment_id)
        v0_runs = self.exp_store.list_workload_runs(v0_experiment_id)

        exp_dir = self.exp_store.get_experiment_dir(v0_experiment_id)
        workloads_file = exp_dir / "workloads.json"
        v0_workloads = json.loads(workloads_file.read_text(encoding="utf-8")) if workloads_file.exists() else []

        is_valid = bool(v0_quality and v0_quality.is_clean_baseline and len(v0_runs) > 0)

        return {
            "experiment_id": v0_experiment_id,
            "device_serial": v0_record.device.serial,
            "device_model": f"{v0_record.device.manufacturer or ''} {v0_record.device.model or ''}".strip(),
            "package": v0_software.package if v0_software else "unknown",
            "version": v0_software.version_name if v0_software else "unknown",
            "apk_sha256": v0_software.apk_sha256 if v0_software else None,
            "build_fingerprint": v0_record.device.build_fingerprint,
            "workloads_count": len(v0_workloads),
            "valid_runs_count": len([r for r in v0_runs if r.status.value == "SUCCESS"]),
            "is_clean_v0_baseline": is_valid,
            "verdict": v0_quality.summary_verdict if v0_quality else "UNKNOWN",
        }

    def run_differential_experiment(
        self,
        v0_experiment_id: str,
        v1_apk_path: Path,
        serial: str,
        iterations: int = 3,
        stabilization_policy: Optional[StabilizationPolicy] = None,
        package_name: str = "com.example.iqoo_hexnil",
    ) -> ComparisonQualityReport:
        """Execute complete, controlled V0 -> V1 differential experiment."""
        policy = stabilization_policy or StabilizationPolicy()
        contamination_flags: List[str] = []

        # 1. Audit V0 Baseline Evidence (Read-Only)
        v0_inspection = self.inspect_v0_baseline(v0_experiment_id)
        if not v0_inspection["is_clean_v0_baseline"]:
            raise HexnilError(
                f"V0 experiment '{v0_experiment_id}' is not a trusted baseline (verdict: {v0_inspection['verdict']}).",
                suggestion="Run a clean baseline via 'python -m hexnil baseline run' before differential comparison.",
            )

        v0_record = self.exp_store.load(v0_experiment_id)
        v0_software = self.exp_store.load_v0_software(v0_experiment_id)
        v0_env = self.exp_store.load_environment(v0_experiment_id)
        v0_runs = self.exp_store.list_workload_runs(v0_experiment_id)

        # 2. Check Device Continuity
        if v0_record.device.serial != serial:
            contamination_flags.append(
                f"Device serial mismatch: V0 was measured on '{v0_record.device.serial}', but target is '{serial}'"
            )

        # 3. Load V0 Workloads & Configuration Hashes
        v0_exp_dir = self.exp_store.get_experiment_dir(v0_experiment_id)
        v0_workloads_file = v0_exp_dir / "workloads.json"
        if not v0_workloads_file.exists():
            raise HexnilError(f"Missing workloads.json in V0 baseline '{v0_experiment_id}'")

        v0_workloads_data = json.loads(v0_workloads_file.read_text(encoding="utf-8"))
        v0_hashes: Dict[str, str] = {w["workload_id"]: w["configuration_hash"] for w in v0_workloads_data}
        v0_suite = [w["workload_id"] for w in v0_workloads_data]

        # 4. Verify Workload Configuration Lock
        v1_defs: List[WorkloadDefinition] = [self.registry.get(wid) for wid in v0_suite]
        v1_hashes: Dict[str, str] = {w.workload_id: w.compute_hash() for w in v1_defs}

        matched_wids, mismatched_wids = self.matcher.verify_configuration_lock(v0_hashes, v1_hashes)
        if mismatched_wids:
            contamination_flags.append(
                f"Workload configuration hash mismatch on: {', '.join(mismatched_wids)}"
            )

        # 5. Install V1 Target APK Update
        install_res = self.installer.install_v1_update(serial, v1_apk_path)
        if not install_res.success:
            raise HexnilError(
                f"Failed to install V1 update APK: {install_res.error_message}",
                suggestion="Verify APK compatibility and signature matching with existing package.",
            )

        # 6. Verify Installed V1 Software Identity
        v1_software = capture_v1_software_identity(self.adb, serial, package_name)
        if v1_software.apk_sha256 != install_res.apk_sha256:
            logger.warning(
                "Installed APK SHA-256 on device (%s) differs from host package (%s)",
                v1_software.apk_sha256,
                install_res.apk_sha256,
            )

        # 7. Post-Update Device Stabilization & Environment Snapshot
        stabilization_res = self.stabilizer.stabilize(serial, policy, package_name)
        if not stabilization_res.success:
            contamination_flags.append(
                f"Post-update stabilization incomplete: {', '.join(stabilization_res.limitations)}"
            )

        v1_env = capture_environment_snapshot(self.adb, serial, package_name)
        env_comparison = compare_environment_snapshots(v0_env, v1_env) if v0_env else None

        # 8. Create V1 Experiment Record & Comparison ID
        v1_exp_id = self.exp_store.generate_experiment_id()
        comparison_id = self.comp_store.generate_comparison_id()
        cmp_dir = self.comp_store.ensure_comparison_dir(comparison_id)

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        v1_exp_record = ExperimentRecord(
            experiment_id=v1_exp_id,
            created_at=now_iso,
            device=v0_record.device,
            adb=AdbStatus(state="device", connected=True),
            phase="05_v0_v1_differential",
            status="running",
        )
        self.exp_store.save(v1_exp_record)

        # 9. Execute Matched Workload Suite on V1
        v1_runs: List[WorkloadRun] = []
        all_v1_artifacts: List[str] = []

        for w_def in v1_defs:
            if w_def.workload_id in mismatched_wids:
                logger.warning("Skipping execution of mismatched workload '%s'", w_def.workload_id)
                continue

            logger.info("Executing V1 workload '%s' for %d iteration(s)", w_def.workload_id, iterations)
            runs = self.engine.execute(
                serial=serial,
                experiment_record=v1_exp_record,
                workload=w_def,
                iterations=iterations,
                package_name=package_name,
            )
            v1_runs.extend(runs)
            for r in runs:
                all_v1_artifacts.extend(r.artifacts)

        # Copy V1 telemetry to comparison directory
        v1_exp_dir = self.exp_store.get_experiment_dir(v1_exp_id)
        if (v1_exp_dir / "telemetry").exists():
            for f in (v1_exp_dir / "telemetry").glob("*.jsonl"):
                (cmp_dir / "v1_telemetry" / f.name).write_bytes(f.read_bytes())

        # Copy V1 artifacts to comparison directory
        if (v1_exp_dir / "artifacts").exists():
            for f in (v1_exp_dir / "artifacts").glob("*"):
                if f.is_file():
                    (cmp_dir / "v1_artifacts" / f.name).write_bytes(f.read_bytes())

        # 10. Perform Run Pairing
        pairs = self.matcher.match_runs(
            comparison_id=comparison_id,
            v0_runs=v0_runs,
            v1_runs=v1_runs,
            v0_workload_hashes=v0_hashes,
            v1_workload_hashes=v1_hashes,
        )

        # 11. Evaluate Comparison Quality
        dev_display = f"{v0_record.device.manufacturer or ''} {v0_record.device.model or ''}".strip()
        quality_report = evaluate_comparison_quality(
            comparison_id=comparison_id,
            v0_experiment_id=v0_experiment_id,
            v1_experiment_id=v1_exp_id,
            device_serial=serial,
            device_model=dev_display,
            v0_version=v0_software.version_name if v0_software else None,
            v1_version=v1_software.version_name,
            v0_apk_sha256=v0_software.apk_sha256 if v0_software else None,
            v1_apk_sha256=v1_software.apk_sha256,
            workloads_requested=v0_suite,
            workloads_matched=matched_wids,
            workloads_mismatched=mismatched_wids,
            iterations_requested=iterations,
            v0_valid_runs_count=len([r for r in v0_runs if r.status.value == "SUCCESS"]),
            v1_valid_runs_count=len([r for r in v1_runs if r.status.value == "SUCCESS"]),
            pairs=pairs,
            contamination_flags=contamination_flags,
        )

        # 12. Provenance & Artifact Integrity Hashes
        artifact_hashes: Dict[str, str] = {}
        for f in (cmp_dir / "v1_artifacts").glob("*"):
            if f.is_file():
                artifact_hashes[f"v1_artifacts/{f.name}"] = hashlib.sha256(f.read_bytes()).hexdigest()
        for f in (cmp_dir / "v1_telemetry").glob("*.jsonl"):
            if f.is_file():
                artifact_hashes[f"v1_telemetry/{f.name}"] = hashlib.sha256(f.read_bytes()).hexdigest()

        provenance = ProvenanceRecord(
            experiment_id=comparison_id,
            analysis_version="1.0.0",
            created_at=now_iso,
            device_serial=serial,
            build_fingerprint=v0_record.device.build_fingerprint or "unknown",
            apk_sha256=v1_software.apk_sha256,
            workloads={},
            artifact_hashes=artifact_hashes,
        )

        # 13. Persist Master Comparison Record
        comp_record = ComparisonRecord(
            comparison_id=comparison_id,
            phase="05_v0_v1_differential",
            created_at=now_iso,
            v0_experiment_id=v0_experiment_id,
            v1_experiment_id=v1_exp_id,
            device=v0_record.device,
            v0_software=v0_software,
            v1_software=v1_software,
            workload_suite=v0_suite,
            environment_comparison=env_comparison,
            run_pairs=pairs,
            install_result=install_res,
            artifacts={"v1_artifacts": all_v1_artifacts},
            status="completed" if quality_report.is_clean_comparison else "contaminated",
        )
        self.comp_store.save_comparison(comp_record)

        (cmp_dir / "quality.json").write_text(quality_report.model_dump_json(indent=2), encoding="utf-8")
        (cmp_dir / "provenance.json").write_text(provenance.model_dump_json(indent=2), encoding="utf-8")

        # 14. Update and persist V1 experiment record & metadata
        v1_exp_record.status = "completed" if quality_report.is_clean_comparison else "contaminated"
        self.exp_store.save(v1_exp_record)
        (v1_exp_dir / "software.json").write_text(v1_software.model_dump_json(indent=2), encoding="utf-8")
        if v1_env:
            (v1_exp_dir / "environment.json").write_text(v1_env.model_dump_json(indent=2), encoding="utf-8")
        (v1_exp_dir / "workloads.json").write_text(
            json.dumps(
                [
                    {
                        "workload_id": w.workload_id,
                        "version": w.version,
                        "configuration_hash": w.compute_hash(),
                        "description": w.description,
                        "preconditions": w.preconditions,
                    }
                    for w in v1_defs
                ],
                indent=2,
            ),
            encoding="utf-8",
        )

        logger.info(
            "V0 -> V1 Differential Comparison %s finished with verdict: %s",
            comparison_id,
            quality_report.summary_verdict,
        )
        return quality_report
