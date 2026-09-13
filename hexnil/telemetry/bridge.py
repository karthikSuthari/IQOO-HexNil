"""Host-device telemetry bridge and orchestrator for Phase 2."""

import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from hexnil.device.adb import AdbClient
from hexnil.device.models import DeviceMetadata, ExperimentRecord
from hexnil.experiments.store import ExperimentStore
from hexnil.telemetry.adb_collectors import (
    AdbBatterystatsCollector,
    AdbGfxinfoCollector,
    AdbLogcatCollector,
    AdbMeminfoCollector,
    AdbPerfettoCollector,
    AdbThermalCollector,
)
from hexnil.telemetry.models import (
    CapabilityStatus,
    SoftwareIdentity,
    TelemetryRecord,
    WorkloadIdentity,
)

logger = logging.getLogger("hexnil.telemetry.bridge")


class TelemetrySummary(BaseModel):
    """Aggregated summary of collected telemetry evidence."""

    experiment_id: str
    device_model: str
    device_serial: str
    android_version: str
    total_records: int
    universal_count: int
    conditional_count: int
    unsupported_count: int
    artifacts: List[str] = Field(default_factory=list)
    categories: Dict[str, str] = Field(default_factory=dict)


class TelemetryBridge:
    """Coordinates on-device and host-side telemetry collection."""

    def __init__(self, adb_client: AdbClient, store: ExperimentStore):
        self.adb = adb_client
        self.store = store

    def trigger_on_device_workload(
        self,
        serial: str,
        experiment_id: str,
        workload_id: str = "startup_basic",
        timeout: float = 15.0,
    ) -> bool:
        """Trigger Android app to run a deterministic workload and collect on-device telemetry."""
        # Launch activity with experiment parameters
        cmd = [
            "shell",
            "am",
            "start",
            "-n",
            "com.example.iqoo_hexnil/.MainActivity",
            "-a",
            "com.example.iqoo_hexnil.ACTION_RUN_WORKLOAD",
            "--es",
            "experiment_id",
            experiment_id,
            "--es",
            "workload_id",
            workload_id,
        ]
        self.adb.run_serial_cmd(serial, cmd, timeout=10.0, check=False)

        # Allow workload to execute and flush records
        time.sleep(2.0)
        return True

    def pull_on_device_telemetry(
        self, serial: str, package_name: str = "com.example.iqoo_hexnil"
    ) -> List[TelemetryRecord]:
        """Retrieve telemetry.jsonl from on-device application storage."""
        records: List[TelemetryRecord] = []

        # Attempt safe run-as read first (debuggable app)
        cmd = ["shell", "run-as", package_name, "cat", "files/telemetry.jsonl"]
        raw_content = self.adb.run_serial_cmd(serial, cmd, check=False).strip()

        # Fallback to external files dir if run-as was empty
        if not raw_content or "No such file" in raw_content:
            ext_cmd = [
                "shell",
                "cat",
                f"/sdcard/Android/data/{package_name}/files/telemetry.jsonl",
            ]
            raw_content = self.adb.run_serial_cmd(serial, ext_cmd, check=False).strip()

        if not raw_content or "No such file" in raw_content:
            logger.info("No on-device telemetry file found yet on device %s", serial)
            return records

        for line in raw_content.splitlines():
            line_str = line.strip()
            if not line_str:
                continue
            try:
                record = TelemetryRecord.model_validate_json(line_str)
                records.append(record)
            except Exception as exc:
                logger.warning("Skipping unparseable on-device telemetry line: %s", exc)

        return records

    def collect_all(
        self,
        serial: str,
        experiment_record: ExperimentRecord,
        workload_id: str = "startup_basic",
        package_name: str = "com.example.iqoo_hexnil",
    ) -> Tuple[List[TelemetryRecord], List[TelemetryRecord], TelemetrySummary]:
        """Execute full Phase 2 universal telemetry collection.

        1. Triggers and pulls on-device telemetry
        2. Executes modular host ADB collectors
        3. Persists records to experiment directory (telemetry/android.jsonl, telemetry/adb.jsonl)
        4. Saves raw artifacts to artifacts/
        5. Computes summary metrics
        """
        exp_id = experiment_record.experiment_id
        dev = experiment_record.device
        software = SoftwareIdentity(package=package_name)
        workload = WorkloadIdentity(id=workload_id, iteration=1)

        # Ensure experiment directory structure
        exp_dir = self.store.ensure_experiment_dir(exp_id)
        artifacts_dir = exp_dir / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        # 1. On-device workload execution & telemetry retrieval
        self.trigger_on_device_workload(serial, exp_id, workload_id=workload_id)
        android_records = self.pull_on_device_telemetry(serial, package_name)

        # 2. Host ADB collectors
        adb_records: List[TelemetryRecord] = []

        collectors = [
            AdbLogcatCollector(self.adb),
            AdbMeminfoCollector(self.adb),
            AdbGfxinfoCollector(self.adb),
            AdbThermalCollector(self.adb),
            AdbBatterystatsCollector(self.adb),
            AdbPerfettoCollector(self.adb),
        ]

        for collector in collectors:
            try:
                col_records = collector.collect(
                    serial=serial,
                    experiment_id=exp_id,
                    device=dev,
                    software=software,
                    workload=workload,
                    artifacts_dir=artifacts_dir,
                )
                adb_records.extend(col_records)
            except Exception as exc:
                logger.warning("Collector %s encountered error: %s", collector.__class__.__name__, exc)

        # 3. Persist JSONL records into experiment folder
        if android_records:
            self.store.append_telemetry(exp_id, android_records, filename="android.jsonl")
        if adb_records:
            self.store.append_telemetry(exp_id, adb_records, filename="adb.jsonl")

        # 4. Gather artifacts
        artifact_names = [f.name for f in artifacts_dir.iterdir() if f.is_file()]

        # 5. Build summary
        all_records = android_records + adb_records
        u_count = sum(1 for r in all_records if r.capability == CapabilityStatus.UNIVERSAL)
        c_count = sum(1 for r in all_records if r.capability == CapabilityStatus.CONDITIONAL)
        unsup_count = sum(1 for r in all_records if r.capability == CapabilityStatus.UNSUPPORTED)

        summary = TelemetrySummary(
            experiment_id=exp_id,
            device_model=f"{dev.manufacturer or ''} {dev.model or ''}".strip(),
            device_serial=dev.serial,
            android_version=dev.android_version or "unknown",
            total_records=len(all_records),
            universal_count=u_count,
            conditional_count=c_count,
            unsupported_count=unsup_count,
            artifacts=artifact_names,
        )

        return android_records, adb_records, summary
