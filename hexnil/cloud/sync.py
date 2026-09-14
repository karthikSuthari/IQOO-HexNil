"""Fleet synchronization orchestrator connecting local Hexnil engine to Supabase."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from hexnil.cloud.client import SupabaseFleetClient
from hexnil.experiments.store import ExperimentStore

logger = logging.getLogger("hexnil.cloud.sync")


class FleetSyncManager:
    """Orchestrates syncing telemetry, baseline records, and reports with Supabase."""

    def __init__(
        self,
        store: ExperimentStore,
        client: Optional[SupabaseFleetClient] = None,
    ):
        self.store = store
        self.client = client or SupabaseFleetClient()

    def push_local_experiment(self, experiment_id: str) -> Dict[str, Any]:
        """Push a locally recorded experiment and its telemetry to Supabase."""
        record = self.store.load(experiment_id)
        if not record:
            raise ValueError(f"Experiment record not found in local store: {experiment_id}")

        device_meta = record.device
        device_id = device_meta.serial or f"{device_meta.manufacturer}_{device_meta.model}".replace(" ", "_")

        # 1. Register device
        device_payload = {
            "device_id": device_id,
            "manufacturer": device_meta.manufacturer,
            "model": device_meta.model,
            "codename": device_meta.codename,
            "abi": device_meta.abi,
            "android_version": device_meta.android_version,
            "sdk_int": device_meta.sdk,
            "build_id": device_meta.build_id,
            "build_fingerprint": device_meta.build_fingerprint,
        }
        self.client.register_device(device_payload)

        # 2. Upload experiment
        baseline_type = "V0"
        if "v1" in experiment_id.lower():
            baseline_type = "V1"

        exp_dir = self.store.get_experiment_dir(experiment_id)
        
        # Load software and environment if present
        apk_sha256 = None
        software_file = exp_dir / "software.json"
        if software_file.exists():
            try:
                sw_data = json.loads(software_file.read_text(encoding="utf-8"))
                apk_sha256 = sw_data.get("apk_sha256")
            except Exception:
                pass

        env_data = {}
        env_file = exp_dir / "environment.json"
        if env_file.exists():
            try:
                env_data = json.loads(env_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        created_at = getattr(record, "created_at", None) or "2026-09-14T00:00:00Z"

        exp_payload = {
            "experiment_id": experiment_id,
            "device_id": device_id,
            "baseline_type": baseline_type,
            "status": "completed",
            "apk_sha256": apk_sha256,
            "metadata": {
                "created_at": created_at,
                "environment": env_data,
            },
        }

        self.client.upload_experiment(exp_payload)

        # 3. Upload telemetry samples if available
        samples_to_upload: List[Dict[str, Any]] = []

        for stream_file in [exp_dir / "telemetry" / "android.jsonl", exp_dir / "telemetry" / "adb.jsonl"]:
            if stream_file.exists():
                for line in stream_file.read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        try:
                            item = json.loads(line)
                            m = item.get("metric", {})
                            samples_to_upload.append({
                                "device_id": device_id,
                                "experiment_id": experiment_id,
                                "workload_id": item.get("workload", {}).get("id", "general"),
                                "metric_name": m.get("name", "unknown"),
                                "metric_value": float(m["value"]) if isinstance(m.get("value"), (int, float)) else None,
                                "unit": m.get("unit"),
                                "capability": item.get("capability", "UNIVERSAL"),
                            })
                        except Exception:
                            continue

        if samples_to_upload:
            # Upload in batches of 100
            for i in range(0, len(samples_to_upload), 100):
                self.client.upload_telemetry_batch(samples_to_upload[i : i + 100])

        return {
            "experiment_id": experiment_id,
            "device_id": device_id,
            "samples_uploaded": len(samples_to_upload),
        }

    def push_device_report_and_issues(
        self,
        device_id: str,
        comparison_id: str,
        v0_build_id: str,
        v1_build_id: str,
        verdict: str,
        coverage: str,
        summary_text: str,
        evidence_dossier: Dict[str, Any],
        issues: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Publish an evaluation report and its classified regressions to Supabase for this device."""
        report_id = f"REPORT-{comparison_id}-{device_id}"

        # Count regressions
        regressions_count = sum(1 for i in issues if "regression" in i.get("category", "").lower())
        anomalies_count = sum(1 for i in issues if i.get("pre_existing", False))

        report_payload = {
            "report_id": report_id,
            "device_id": device_id,
            "comparison_id": comparison_id,
            "v0_build_id": v0_build_id,
            "v1_build_id": v1_build_id,
            "verdict": verdict,
            "coverage": coverage,
            "total_regressions": regressions_count,
            "total_anomalies": anomalies_count,
            "summary_text": summary_text,
            "evidence_dossier": evidence_dossier,
        }
        self.client.publish_device_report(report_payload)

        # Prepare issues with foreign key
        for issue in issues:
            issue["device_id"] = device_id
            issue["report_id"] = report_id

        self.client.publish_issue_classifications(issues)

        return {
            "report_id": report_id,
            "device_id": device_id,
            "verdict": verdict,
            "total_issues": len(issues),
        }

    def push_final_evidence_report(
        self,
        report_data: Dict[str, Any],
        device_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Push a Phase 12 FinalEvidenceReport object or dict directly to Supabase."""
        dev_id = device_id or report_data.get("device_serial") or "unknown_device"
        comp_id = report_data.get("comparison_id") or report_data.get("session_id") or "CMP-LOCAL"
        
        pre_os = report_data.get("pre_update_os_state", {})
        post_os = report_data.get("post_update_os_state", {})
        v0_build = pre_os.get("build_id", "v0") if isinstance(pre_os, dict) else getattr(pre_os, "build_id", "v0")
        v1_build = post_os.get("build_id", "v1") if isinstance(post_os, dict) else getattr(post_os, "build_id", "v1")

        issues_raw = []
        # Combine regressions, fixed, and persisted issues
        for cat_key in ["new_regressions", "persisted_issues", "fixed_issues", "insufficient_evidence_items"]:
            for item in report_data.get(cat_key, []):
                if hasattr(item, "model_dump"):
                    issues_raw.append(item.model_dump())
                elif isinstance(item, dict):
                    issues_raw.append(item)

        issues: List[Dict[str, Any]] = []
        for raw in issues_raw:
            issues.append({
                "classification_id": raw.get("classification_id", f"ISSUE-{raw.get('metric_name', 'metric')}"),
                "device_id": dev_id,
                "metric_name": raw.get("metric_name", "unknown"),
                "display_name": raw.get("metric_name", "").replace("_", " ").title(),
                "category": raw.get("category", "NEW_REGRESSION"),
                "severity": raw.get("post_update_severity", "MEDIUM"),
                "effect_size": raw.get("effect_size"),
                "percent_delta": raw.get("percent_delta"),
                "pre_existing": raw.get("pre_update_anomaly_existed", False),
                "explanation": raw.get("explanation", ""),
            })

        return self.push_device_report_and_issues(
            device_id=dev_id,
            comparison_id=comp_id,
            v0_build_id=v0_build,
            v1_build_id=v1_build,
            verdict=report_data.get("overall_verdict", "INSUFFICIENT_DATA"),
            coverage=f"{len(issues)} metrics analyzed",
            summary_text=report_data.get("executive_summary", ""),
            evidence_dossier={
                "recommendations": report_data.get("recommendations", []),
                "prediction_summary": report_data.get("ml_prediction_summary", ""),
            },
            issues=issues,
        )

    def pull_device_telemetry(
        self,
        device_id: str,
        experiment_id: Optional[str] = None,
        limit: int = 2000,
    ) -> Dict[str, Any]:
        """Pull telemetry samples for a device from Supabase and save to local store."""
        samples = self.client.get_telemetry_samples(device_id, experiment_id, limit=limit)
        if not samples:
            return {"device_id": device_id, "samples_fetched": 0, "saved_paths": []}

        # Group samples by experiment_id
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for s in samples:
            exp_id = s.get("experiment_id") or f"EXP-PULL-{device_id[:8]}"
            grouped.setdefault(exp_id, []).append(s)

        saved_files = []
        for exp_id, exp_samples in grouped.items():
            exp_dir = self.store.ensure_experiment_dir(exp_id)
            telemetry_file = exp_dir / "telemetry" / "cloud_pulled.jsonl"
            with open(telemetry_file, "w", encoding="utf-8") as f:
                for s in exp_samples:
                    f.write(json.dumps(s) + "\n")
            saved_files.append(str(telemetry_file))

        return {
            "device_id": device_id,
            "samples_fetched": len(samples),
            "experiments_count": len(grouped),
            "saved_paths": saved_files,
        }

