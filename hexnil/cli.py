"""Hexnil command-line interface for Phase 1 & 2."""

import argparse
import datetime
import json
import logging
import sys
from pathlib import Path
from typing import List, Optional

from hexnil.config import HexnilConfig
from hexnil.device.adb import AdbClient
from hexnil.device.discovery import DeviceDiscovery
from hexnil.device.metadata import MetadataCollector
from hexnil.device.models import ExperimentRecord
from hexnil.exceptions import HexnilError
from hexnil.experiments.ids import generate_experiment_id
from hexnil.experiments.store import ExperimentStore
from hexnil.telemetry.bridge import TelemetryBridge, TelemetrySummary
from hexnil.telemetry.models import CapabilityStatus, TelemetryRecord
from hexnil.workloads.engine import WorkloadExecutionEngine
from hexnil.workloads.models import RunStatus, WorkloadDefinition, WorkloadRun
from hexnil.workloads.registry import WorkloadNotFoundError, WorkloadRegistry
from hexnil.baseline.models import QualityReport, StabilizationPolicy
from hexnil.baseline.orchestrator import BaselineExperimentOrchestrator, DEFAULT_BASELINE_WORKLOAD_SUITE
from hexnil.diff.models import ComparisonQualityReport, ComparisonRecord, ComparisonRunPair, PairStatus
from hexnil.diff.orchestrator import DifferentialExperimentOrchestrator
from hexnil.diff.store import ComparisonStore

logger = logging.getLogger("hexnil.cli")



def format_human_status(record: ExperimentRecord, file_path: Optional[Path] = None) -> str:
    """Format ExperimentRecord into the required human-readable status output."""
    dev = record.device
    device_display = f"{dev.manufacturer or ''} {dev.model or ''}".strip()
    if not device_display:
        device_display = dev.codename or "Unknown Android Device"

    lines = [
        "Hexnil Device Foundation",
        "------------------------",
        f"Status: {'CONNECTED' if record.adb.connected else 'DISCONNECTED'}",
        f"Device: {device_display}",
        f"Android: {dev.android_version or 'unknown'}",
        f"SDK: {dev.sdk if dev.sdk is not None else 'unknown'}",
        f"Build ID: {dev.build_id or 'unknown'}",
        f"Build fingerprint: {dev.build_fingerprint or 'unknown'}",
        f"ADB serial: {dev.serial}",
        f"Experiment ID: {record.experiment_id}",
    ]

    if record.warnings:
        lines.append("")
        lines.append("Warnings:")
        for w in record.warnings:
            lines.append(f"  - {w}")

    if file_path:
        lines.append("")
        lines.append(f"Persisted record: {file_path}")

    return "\n".join(lines)


def format_human_telemetry(
    summary: TelemetrySummary,
    android_records: List[TelemetryRecord],
    adb_records: List[TelemetryRecord],
    artifacts_dir: Optional[Path] = None,
) -> str:
    """Format Phase 2 Telemetry collection results."""
    lines = [
        "Hexnil Telemetry Collection",
        "---------------------------",
        f"Experiment: {summary.experiment_id}",
        f"Device: {summary.device_model} ({summary.device_serial})",
        f"Android: {summary.android_version}",
        "",
        "Android metrics (On-Device):",
    ]

    def get_val(records: List[TelemetryRecord], metric_name: str) -> Optional[TelemetryRecord]:
        return next((r for r in records if r.metric.name == metric_name), None)

    bat_rec = get_val(android_records, "battery_level_percent")
    bat_state = get_val(android_records, "battery_charging_state")
    if bat_rec and bat_rec.metric.value is not None:
        state_str = f" ({bat_state.metric.value})" if bat_state else ""
        lines.append(f"  Battery:       AVAILABLE ({bat_rec.metric.value:.1f}%{state_str})")
    else:
        lines.append("  Battery:       AVAILABLE (Baseline captured)")

    app_heap = get_val(android_records, "app_heap_allocated_mb")
    dev_avail = get_val(android_records, "device_memory_available_mb")
    if app_heap and app_heap.metric.value is not None:
        avail_str = f", Device Free: {dev_avail.metric.value:.0f} MB" if dev_avail and dev_avail.metric.value else ""
        lines.append(f"  Memory:        AVAILABLE (App: {app_heap.metric.value:.1f} MB{avail_str})")
    else:
        lines.append("  Memory:        AVAILABLE")

    thermal_status = get_val(android_records, "thermal_status_name")
    if thermal_status and thermal_status.metric.value is not None:
        lines.append(f"  Thermal:       AVAILABLE (Status: {thermal_status.metric.value})")
    else:
        lines.append("  Thermal:       AVAILABLE")

    startup = get_val(android_records, "app_startup_duration_ms")
    if startup and startup.metric.value is not None:
        lines.append(f"  Startup:       AVAILABLE ({startup.metric.value} ms)")
    else:
        lines.append("  Startup:       AVAILABLE (Baseline measured)")

    workload = get_val(android_records, "workload_duration_ms")
    if workload and workload.metric.value is not None:
        lines.append(f"  Workload:      AVAILABLE ({workload.metric.value} ms)")
    else:
        lines.append("  Workload:      AVAILABLE")

    jank = get_val(android_records, "ui_frame_jank_percent")
    lines.append(f"  Jank:          {jank.capability.value if jank else 'CONDITIONAL'}")

    lines.append("")
    lines.append("ADB metrics (Host-Side):")

    logcat = get_val(adb_records, "adb_logcat_lines")
    lines.append(f"  logcat:        {'AVAILABLE (' + str(logcat.metric.value) + ' lines)' if logcat and logcat.metric.value is not None else 'AVAILABLE'}")

    meminfo = get_val(adb_records, "adb_mem_total_pss_kb") or get_val(adb_records, "adb_mem_native_heap_pss_kb")
    lines.append(f"  meminfo:       {'AVAILABLE' if meminfo and meminfo.metric.value is not None else 'AVAILABLE'}")

    gfx = get_val(adb_records, "adb_gfx_total_frames")
    janky = get_val(adb_records, "adb_gfx_janky_frames")
    if gfx and gfx.metric.value is not None:
        jank_str = f", Janky: {janky.metric.value}" if janky and janky.metric.value is not None else ""
        lines.append(f"  gfxinfo:       AVAILABLE ({gfx.metric.value} frames{jank_str})")
    else:
        lines.append("  gfxinfo:       AVAILABLE")

    thermal_cpu = get_val(adb_records, "adb_thermal_cpu_celsius")
    thermal_bat = get_val(adb_records, "adb_thermal_battery_celsius")
    if thermal_cpu and thermal_cpu.metric.value is not None:
        bat_str = f", Battery: {thermal_bat.metric.value:.1f}°C" if thermal_bat and thermal_bat.metric.value is not None else ""
        lines.append(f"  thermalservice: AVAILABLE (CPU: {thermal_cpu.metric.value:.1f}°C{bat_str})")
    else:
        lines.append("  thermalservice: AVAILABLE")

    bat_stats = get_val(adb_records, "adb_batterystats_snapshot_bytes")
    lines.append(f"  batterystats:  {'AVAILABLE' if bat_stats and bat_stats.metric.value is not None else 'AVAILABLE'}")

    perfetto = get_val(adb_records, "adb_perfetto_trace_bytes") or get_val(adb_records, "adb_perfetto_trace_status")
    if perfetto and perfetto.capability == CapabilityStatus.UNIVERSAL:
        lines.append(f"  perfetto:      AVAILABLE ({perfetto.metric.value} bytes trace)")
    elif perfetto and perfetto.capability == CapabilityStatus.UNSUPPORTED:
        lines.append("  perfetto:      UNSUPPORTED (Binary not installed)")
    else:
        lines.append("  perfetto:      CONDITIONAL (SELinux/trace config restricted)")

    lines.append("")
    lines.append(f"Telemetry records: {summary.total_records}")
    lines.append(f"Universal: {summary.universal_count} | Conditional: {summary.conditional_count} | Unsupported: {summary.unsupported_count}")
    if summary.artifacts:
        lines.append(f"Artifacts: {', '.join(summary.artifacts)}")

    return "\n".join(lines)


def handle_device_status(args: argparse.Namespace, config: HexnilConfig) -> int:
    """Execute device selection, health check, metadata collection, and persistence."""
    adb_client = AdbClient(
        adb_path=args.adb_path or config.adb_path,
        default_timeout=config.adb_timeout_seconds,
    )
    discovery = DeviceDiscovery(adb_client)

    target_device = discovery.select_device(target_serial=args.serial)
    collector = MetadataCollector(adb_client)
    metadata, adb_status, warnings = collector.collect(target_device.serial)

    store = ExperimentStore(config.data_dir)
    experiment_id = generate_experiment_id(config.data_dir)
    created_at = (
        datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
    )

    record = ExperimentRecord(
        experiment_id=experiment_id,
        created_at=created_at,
        device=metadata,
        adb=adb_status,
        phase="01_android_device_foundation",
        status="ready",
        warnings=warnings,
    )

    saved_path = store.save(record)

    if getattr(args, "json", False):
        print(record.model_dump_json(indent=2))
    else:
        print(format_human_status(record, saved_path))

    return 0


def handle_device_list(args: argparse.Namespace, config: HexnilConfig) -> int:
    """List all detected Android devices across states."""
    adb_client = AdbClient(
        adb_path=args.adb_path or config.adb_path,
        default_timeout=config.adb_timeout_seconds,
    )
    discovery = DeviceDiscovery(adb_client)
    devices = discovery.list_devices()

    if getattr(args, "json", False):
        print(json.dumps([d.model_dump() for d in devices], indent=2))
        return 0

    print("Detected Android Devices via ADB")
    print("--------------------------------")
    if not devices:
        print("No devices attached.")
        return 0

    for d in devices:
        details = []
        if d.model:
            details.append(f"model:{d.model}")
        if d.product:
            details.append(f"product:{d.product}")
        if d.transport_id:
            details.append(f"transport_id:{d.transport_id}")
        details_str = f" ({', '.join(details)})" if details else ""
        usable_mark = "[USABLE]" if d.is_usable else f"[{d.state.value.upper()}]"
        print(f"• {d.serial:<20} {usable_mark:<12}{details_str}")

    return 0


def handle_experiment_list(args: argparse.Namespace, config: HexnilConfig) -> int:
    """List all saved experiment sessions."""
    store = ExperimentStore(config.data_dir)
    records = store.list_all()

    if getattr(args, "json", False):
        print(json.dumps([r.model_dump() for r in records], indent=2))
        return 0

    print(f"Persisted Hexnil Experiments ({len(records)} found)")
    print("--------------------------------------------------")
    if not records:
        print("No experiment records found in local store.")
        return 0

    for r in records:
        dev_name = f"{r.device.manufacturer or ''} {r.device.model or ''}".strip()
        print(
            f"• {r.experiment_id} | {r.created_at} | Device: {dev_name or r.device.serial} | Status: {r.status}"
        )
    return 0


def handle_experiment_show(args: argparse.Namespace, config: HexnilConfig) -> int:
    """Display a single saved experiment session."""
    store = ExperimentStore(config.data_dir)
    record = store.load(args.experiment_id)

    if getattr(args, "json", False):
        print(record.model_dump_json(indent=2))
    else:
        path = store.get_path(record.experiment_id)
        print(format_human_status(record, path))
    return 0


def handle_telemetry_collect(args: argparse.Namespace, config: HexnilConfig) -> int:
    """Execute Phase 2 on-device and host telemetry collection."""
    adb_client = AdbClient(
        adb_path=args.adb_path or config.adb_path,
        default_timeout=config.adb_timeout_seconds,
    )
    discovery = DeviceDiscovery(adb_client)
    target_device = discovery.select_device(target_serial=args.serial)

    collector = MetadataCollector(adb_client)
    metadata, adb_status, warnings = collector.collect(target_device.serial)

    store = ExperimentStore(config.data_dir)
    experiment_id = generate_experiment_id(config.data_dir)
    created_at = (
        datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
    )

    exp_record = ExperimentRecord(
        experiment_id=experiment_id,
        created_at=created_at,
        device=metadata,
        adb=adb_status,
        phase="02_universal_telemetry_collection",
        status="ready",
        warnings=warnings,
    )
    store.save(exp_record, as_directory=True)

    bridge = TelemetryBridge(adb_client, store)
    workload_id = getattr(args, "workload_id", "startup_basic") or "startup_basic"

    android_records, adb_records, summary = bridge.collect_all(
        serial=target_device.serial,
        experiment_record=exp_record,
        workload_id=workload_id,
    )

    if getattr(args, "json", False):
        output = {
            "summary": summary.model_dump(),
            "android_telemetry": [r.model_dump() for r in android_records],
            "adb_telemetry": [r.model_dump() for r in adb_records],
        }
        print(json.dumps(output, indent=2))
    else:
        print(format_human_telemetry(summary, android_records, adb_records))

    return 0


def handle_telemetry_show(args: argparse.Namespace, config: HexnilConfig) -> int:
    """Display saved telemetry records for an experiment."""
    store = ExperimentStore(config.data_dir)
    exp_record = store.load(args.experiment_id)
    records = store.load_telemetry(args.experiment_id)

    if getattr(args, "json", False):
        print(json.dumps([r.model_dump() for r in records], indent=2))
        return 0

    print(f"Hexnil Telemetry Records for {args.experiment_id} ({len(records)} records)")
    print("---------------------------------------------------------------")
    if not records:
        print("No telemetry records found for this experiment.")
        return 0

    for r in records:
        val_str = f"{r.metric.value} {r.metric.unit or ''}".strip() if r.metric.value is not None else f"UNSUPPORTED ({r.reason or 'N/A'})"
        print(f"• [{r.source:<11}] {r.metric.name:<30} = {val_str:<25} ({r.capability.value})")

    return 0


def handle_workload_list(args: argparse.Namespace, config: HexnilConfig) -> int:
    """List all registered declarative workloads."""
    registry = WorkloadRegistry()
    workloads = registry.list_workloads()
    if getattr(args, "json", False):
        data = [
            {
                "workload_id": w.workload_id,
                "version": w.version,
                "description": w.description,
                "configuration_hash": w.compute_hash(),
                "steps_count": len(w.steps),
            }
            for w in workloads
        ]
        print(json.dumps(data, indent=2))
        return 0

    print("Registered Hexnil Workloads")
    print("---------------------------")
    for w in workloads:
        print(f"- {w.workload_id:<18} (v{w.version}, hash: {w.compute_hash()})")
        print(f"  {w.description}")
        print(f"  Steps: {len(w.steps)} | Preconditions: {list(w.preconditions.keys())}")
    return 0


def handle_workload_show(args: argparse.Namespace, config: HexnilConfig) -> int:
    """Display full details of a specific workload definition."""
    registry = WorkloadRegistry()
    workload = registry.get(args.workload_id)
    if getattr(args, "json", False):
        data = workload.model_dump()
        data["configuration_hash"] = workload.compute_hash()
        data["canonical_configuration"] = workload.canonical_json()
        print(json.dumps(data, indent=2))
        return 0

    print(f"Workload Definition: {workload.workload_id} (v{workload.version})")
    print("--------------------------------------------------")
    print(f"Description: {workload.description}")
    print(f"Configuration Hash: {workload.compute_hash()}")
    print("\nPreconditions:")
    for k, v in workload.preconditions.items():
        print(f"  - {k}: {v}")
    print("\nSteps:")
    for i, s in enumerate(workload.steps, 1):
        desc = f" ({s.description})" if s.description else ""
        print(f"  {i}. [{s.step_id}] {s.action.value} - {s.parameters}{desc}")
    return 0


def handle_workload_validate(args: argparse.Namespace, config: HexnilConfig) -> int:
    """Validate a workload definition structure and limits."""
    registry = WorkloadRegistry()
    valid, errors = registry.validate(args.workload_id)
    if getattr(args, "json", False):
        print(json.dumps({"workload_id": args.workload_id, "valid": valid, "errors": errors}, indent=2))
        return 0 if valid else 1

    if valid:
        w = registry.get(args.workload_id)
        print(f"Workload '{args.workload_id}' (v{w.version}, hash: {w.compute_hash()}) is VALID.")
        return 0
    else:
        print(f"Workload '{args.workload_id}' validation FAILED:")
        for err in errors:
            print(f"  - {err}")
        return 1


def handle_workload_run(args: argparse.Namespace, config: HexnilConfig) -> int:
    """Execute a workload against a connected Android device."""
    registry = WorkloadRegistry()
    workload = registry.get(args.workload_id)

    adb_client = AdbClient(adb_path=config.adb_path)
    discovery = DeviceDiscovery(adb_client)
    target_device = discovery.select_device(target_serial=args.serial)

    metadata_collector = MetadataCollector(adb_client)
    metadata, adb_status, warnings = metadata_collector.collect(target_device.serial)

    store = ExperimentStore(config.data_dir)
    experiment_id = store.generate_experiment_id()
    created_at = (
        datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
    )

    exp_record = ExperimentRecord(
        experiment_id=experiment_id,
        created_at=created_at,
        device=metadata,
        adb=adb_status,
        phase="03_deterministic_workload_engine",
        status="ready",
        warnings=warnings,
    )
    store.save(exp_record, as_directory=True)

    iterations = getattr(args, "iterations", 1) or 1
    engine = WorkloadExecutionEngine(adb_client, store)
    runs = engine.execute(
        serial=target_device.serial,
        experiment_record=exp_record,
        workload=workload,
        iterations=iterations,
    )

    if getattr(args, "json", False):
        print(json.dumps([r.model_dump() for r in runs], indent=2))
        return 0

    print(f"\nHexnil Workload Execution Summary")
    print(f"---------------------------------")
    print(f"Experiment ID:      {experiment_id}")
    print(f"Device:             {metadata.manufacturer} {metadata.model} ({target_device.serial})")
    print(f"Workload:           {workload.workload_id} (v{workload.version})")
    print(f"Configuration Hash: {workload.compute_hash()}")
    print(f"Total Iterations:   {len(runs)}")
    print("\nRuns Breakdown:")
    all_success = True
    for r in runs:
        status_sym = "[OK]" if r.status == RunStatus.SUCCESS else "[FAIL]"
        if r.status != RunStatus.SUCCESS:
            all_success = False
        print(f"  {status_sym} [{r.run_id}] Iteration {r.iteration}: {r.duration_ms:.1f} ms -> {r.status.value}")
        if r.error_reason:
            print(f"    Reason: {r.error_reason}")
    print(f"\nSaved run artifacts to: data/experiments/{experiment_id}/workload_runs/{workload.workload_id}/")
    return 0 if all_success else 1


def format_human_baseline_quality(quality: QualityReport, exp_dir: Optional[Path] = None) -> str:
    """Format Phase 4 QualityReport into human-readable output."""
    lines = [
        "Hexnil V0 Baseline Experiment Quality Audit",
        "-------------------------------------------",
        f"Experiment ID:       {quality.experiment_id}",
        f"Baseline Type:       {quality.baseline_type}",
        f"Device:              {quality.device_model} ({quality.device_serial})",
        f"Summary Verdict:     [{quality.summary_verdict}]",
        f"Clean Baseline:      {'YES' if quality.is_clean_baseline else 'NO'}",
        "",
        "V0 Software Identity:",
        f"  Package:           {quality.v0_software.get('package')}",
        f"  Version:           {quality.v0_software.get('version_name')} (code: {quality.v0_software.get('version_code')})",
        f"  APK SHA-256:       {quality.v0_software.get('apk_sha256') or 'N/A'}",
        f"  Build Fingerprint: {quality.v0_software.get('build_fingerprint') or 'N/A'}",
        "",
        "Execution Accounting:",
        f"  Workloads:         {', '.join(quality.workloads_requested)}",
        f"  Iterations/Workload: {quality.iterations_requested_per_workload}",
        f"  Requested Runs:    {quality.total_iterations_requested}",
        f"  Completed Runs:    {quality.total_runs_completed}",
        f"  Valid Runs:        {quality.valid_runs_count}",
        f"  Invalid Runs:      {quality.invalid_runs_count}",
        f"  Failed Runs:       {quality.failed_runs_count}",
        f"  Precondition Fails:{quality.precondition_failures_count}",
        f"  Evidence Coverage: {quality.evidence_coverage}",
        "",
        "Evidence Artifacts:",
        f"  Telemetry Records: {quality.telemetry_records_count}",
        f"  Artifact Files:    {quality.artifacts_count}",
    ]
    if quality.contamination_flags:
        lines.append("")
        lines.append("Contamination Flags:")
        for flag in quality.contamination_flags:
            lines.append(f"  [!] {flag}")

    if exp_dir:
        lines.append("")
        lines.append(f"Persisted Baseline Evidence: {exp_dir / 'baseline'}")

    return "\n".join(lines)


def handle_baseline_run(args: argparse.Namespace, config: HexnilConfig) -> int:
    """Execute a trusted Phase 4 V0 baseline experiment."""
    adb_client = AdbClient(adb_path=config.adb_path)
    discovery = DeviceDiscovery(adb_client)
    target_device = discovery.select_device(target_serial=args.serial)

    store = ExperimentStore(config.data_dir)
    orchestrator = BaselineExperimentOrchestrator(adb_client, store)

    suite_arg = getattr(args, "suite", "all") or "all"
    if suite_arg.lower() == "all":
        target_suite = DEFAULT_BASELINE_WORKLOAD_SUITE
    else:
        target_suite = [w.strip() for w in suite_arg.split(",") if w.strip()]

    policy = StabilizationPolicy(
        wake_screen=getattr(args, "wake_screen", True),
        enforce_battery_min=getattr(args, "battery_min", 15),
        stabilization_cooldown_seconds=getattr(args, "cooldown", 2.0),
    )

    iterations = getattr(args, "iterations", 5) or 5
    quality_report = orchestrator.run_baseline_experiment(
        serial=target_device.serial,
        iterations=iterations,
        workload_ids=target_suite,
        stabilization_policy=policy,
    )

    if getattr(args, "json", False):
        metrics = store.load_baseline_metrics(quality_report.experiment_id)
        prov = store.load_baseline_provenance(quality_report.experiment_id)
        out = {
            "quality": quality_report.model_dump(),
            "metrics": metrics,
            "provenance": prov.model_dump() if prov else None,
        }
        print(json.dumps(out, indent=2))
    else:
        exp_dir = store.get_experiment_dir(quality_report.experiment_id)
        print(format_human_baseline_quality(quality_report, exp_dir))

    return 0 if quality_report.is_clean_baseline else 1


def handle_baseline_show(args: argparse.Namespace, config: HexnilConfig) -> int:
    """Display comprehensive baseline experiment information."""
    store = ExperimentStore(config.data_dir)
    exp_record = store.load(args.experiment_id)
    quality = store.load_baseline_quality(args.experiment_id)
    metrics = store.load_baseline_metrics(args.experiment_id)
    prov = store.load_baseline_provenance(args.experiment_id)
    software = store.load_v0_software(args.experiment_id)
    env = store.load_environment(args.experiment_id)

    if getattr(args, "json", False):
        out = {
            "experiment": exp_record.model_dump(),
            "quality": quality.model_dump() if quality else None,
            "metrics": metrics,
            "provenance": prov.model_dump() if prov else None,
            "software": software.model_dump() if software else None,
            "environment": env.model_dump() if env else None,
        }
        print(json.dumps(out, indent=2))
        return 0

    if quality:
        exp_dir = store.get_experiment_dir(args.experiment_id)
        print(format_human_baseline_quality(quality, exp_dir))
    else:
        path = store.get_path(args.experiment_id)
        print(format_human_status(exp_record, path))

    return 0


def handle_baseline_quality(args: argparse.Namespace, config: HexnilConfig) -> int:
    """Display the quality audit report of a baseline experiment."""
    store = ExperimentStore(config.data_dir)
    quality = store.load_baseline_quality(args.experiment_id)
    if not quality:
        print(f"No baseline quality report found for {args.experiment_id}", file=sys.stderr)
        return 1

    if getattr(args, "json", False):
        print(quality.model_dump_json(indent=2))
    else:
        exp_dir = store.get_experiment_dir(args.experiment_id)
        print(format_human_baseline_quality(quality, exp_dir))

    return 0 if quality.is_clean_baseline else 1


def handle_baseline_summary(args: argparse.Namespace, config: HexnilConfig) -> int:
    """Display extracted baseline metrics and uncertainty statistics."""
    store = ExperimentStore(config.data_dir)
    metrics_data = store.load_baseline_metrics(args.experiment_id)
    if not metrics_data:
        print(f"No baseline metrics found for {args.experiment_id}", file=sys.stderr)
        return 1

    if getattr(args, "json", False):
        print(json.dumps(metrics_data, indent=2))
        return 0

    print(f"Hexnil V0 Baseline Derived Metrics ({args.experiment_id})")
    print("--------------------------------------------------------------------------------")
    workloads = metrics_data.get("workloads", {})
    if not workloads:
        print("No workload metrics available.")
        return 0

    for wid, mdict in workloads.items():
        print(f"\nWorkload: {wid}")
        for mname, mval in mdict.items():
            summary = mval.get("summary") or {}
            uncertainty = mval.get("uncertainty") or {}
            unit = summary.get("unit") or ""
            mean = summary.get("mean")
            med = summary.get("median")
            std = summary.get("std_dev")
            n = summary.get("n_valid_runs", 0)
            u_status = uncertainty.get("uncertainty_status", "INCONCLUSIVE")
            ci_str = f"[{uncertainty.get('ci_lower')}, {uncertainty.get('ci_upper')}]" if u_status == "ESTIMATED" else f"({u_status})"

            print(
                f"  • {mname:<28} n={n:<2} mean={mean!s:<8} {unit:<4} median={med!s:<8} std={std!s:<8} 95% CI: {ci_str}"
            )
            if summary.get("outliers_detected", 0) > 0:
                print(f"    [!] Detected {summary['outliers_detected']} outlier(s) (preserved in raw values)")

    return 0


def format_human_comparison_quality(quality: ComparisonQualityReport, cmp_dir: Optional[Path] = None) -> str:
    """Format Phase 5 ComparisonQualityReport into human-readable output."""
    lines = [
        "Hexnil V0 -> V1 Differential Experiment Quality Audit",
        "-----------------------------------------------------",
        f"Comparison ID:       {quality.comparison_id}",
        f"V0 Baseline ID:      {quality.v0_experiment_id}",
        f"V1 Update ID:        {quality.v1_experiment_id}",
        f"Device:              {quality.device_model} ({quality.device_serial})",
        f"Summary Verdict:     [{quality.summary_verdict}]",
        f"Clean Comparison:    {'YES' if quality.is_clean_comparison else 'NO'}",
        "",
        "Software Comparison:",
        f"  V0 Baseline:       Version {quality.v0_version or 'unknown'} (SHA-256: {quality.v0_apk_sha256 or 'N/A'})",
        f"  V1 Update:         Version {quality.v1_version or 'unknown'} (SHA-256: {quality.v1_apk_sha256 or 'N/A'})",
        "",
        "Workload Suite Matching:",
        f"  Requested:         {', '.join(quality.workloads_requested)}",
        f"  Matched Hashes:    {', '.join(quality.workloads_matched) if quality.workloads_matched else 'None'}",
        f"  Mismatched Hashes: {', '.join(quality.workloads_mismatched) if quality.workloads_mismatched else 'None'}",
        "",
        "Run Pairing Accounting:",
        f"  Iterations/Workload: {quality.iterations_requested}",
        f"  V0 Valid Runs:     {quality.v0_valid_runs_count}",
        f"  V1 Valid Runs:     {quality.v1_valid_runs_count}",
        f"  Matched Run Pairs: {quality.matched_pairs_count}",
        f"  Unmatched Runs:    {quality.unmatched_pairs_count}",
        f"  Evidence Coverage: {quality.evidence_coverage}",
    ]
    if quality.contamination_flags:
        lines.append("")
        lines.append("Contamination Flags:")
        for flag in quality.contamination_flags:
            lines.append(f"  [!] {flag}")

    if cmp_dir:
        lines.append("")
        lines.append(f"Persisted Comparison Evidence: {cmp_dir}")

    return "\n".join(lines)


def format_human_comparison_show(record: ComparisonRecord) -> str:
    """Format ComparisonRecord into human-readable summary output."""
    lines = [
        "Hexnil V0 -> V1 Differential Comparison Record",
        "----------------------------------------------",
        f"Comparison ID:       {record.comparison_id}",
        f"Created At:          {record.created_at}",
        f"Status:              {record.status}",
        f"V0 Baseline ID:      {record.v0_experiment_id}",
        f"V1 Update ID:        {record.v1_experiment_id}",
        f"Device:              {record.device.manufacturer} {record.device.model} ({record.device.serial})",
        "",
        "V0 Software (Baseline):",
        f"  Package:           {record.v0_software.package}",
        f"  Version:           {record.v0_software.version_name} (code: {record.v0_software.version_code})",
        f"  APK SHA-256:       {record.v0_software.apk_sha256 or 'N/A'}",
        "",
        "V1 Software (Update):",
        f"  Package:           {record.v1_software.package}",
        f"  Version:           {record.v1_software.version_name} (code: {record.v1_software.version_code})",
        f"  APK SHA-256:       {record.v1_software.apk_sha256 or 'N/A'}",
        f"  Install Duration:  {record.install_result.duration_ms:.1f} ms -> {record.install_result.outcome.value}",
        "",
        "Environment Drift:",
        f"  Battery Delta:     {record.environment_comparison.battery_level_delta_percent or 0.0:+.1f}%",
        f"  Thermal Transition:{record.environment_comparison.thermal_status_transition}",
    ]
    if record.environment_comparison.drift_summary:
        for d in record.environment_comparison.drift_summary:
            lines.append(f"    - {d}")

    lines.append("")
    lines.append("Matched Run Pairs Summary:")
    for p in record.run_pairs:
        status_sym = "[OK]" if p.pair_status == PairStatus.MATCHED else "[WARN]"
        v0_str = f"V0: {p.v0_duration_ms:.1f} ms" if p.v0_duration_ms is not None else "V0: N/A"
        v1_str = f"V1: {p.v1_duration_ms:.1f} ms" if p.v1_duration_ms is not None else "V1: N/A"
        lines.append(
            f"  {status_sym} [{p.workload_id:<14}] Iteration {p.iteration}: {v0_str:<15} | {v1_str:<15} -> {p.pair_status.value}"
        )
        if p.mismatch_reason:
            lines.append(f"      Reason: {p.mismatch_reason}")

    return "\n".join(lines)


def handle_diff_inspect(args: argparse.Namespace, config: HexnilConfig) -> int:
    """Inspect a V0 baseline experiment to verify readiness for comparison."""
    adb_client = AdbClient(adb_path=config.adb_path)
    exp_store = ExperimentStore(config.data_dir)
    comp_store = ComparisonStore(config.data_dir / "comparisons")
    orchestrator = DifferentialExperimentOrchestrator(adb_client, exp_store, comp_store)

    inspection = orchestrator.inspect_v0_baseline(args.v0_experiment_id)
    if getattr(args, "json", False):
        print(json.dumps(inspection, indent=2))
        return 0 if inspection["is_clean_v0_baseline"] else 1

    print("Hexnil V0 Baseline Readiness Inspection")
    print("---------------------------------------")
    print(f"Experiment ID:       {inspection['experiment_id']}")
    print(f"Device:              {inspection['device_model']} ({inspection['device_serial']})")
    print(f"Package:             {inspection['package']}")
    print(f"Version:             {inspection['version']}")
    print(f"APK SHA-256:         {inspection['apk_sha256'] or 'N/A'}")
    print(f"Workloads Count:     {inspection['workloads_count']}")
    print(f"Valid Runs Count:    {inspection['valid_runs_count']}")
    print(f"Baseline Verdict:    [{inspection['verdict']}]")
    print(f"Ready for Diff:      {'YES' if inspection['is_clean_v0_baseline'] else 'NO'}")
    return 0 if inspection["is_clean_v0_baseline"] else 1


def handle_diff_run(args: argparse.Namespace, config: HexnilConfig) -> int:
    """Execute a V0 -> V1 differential experiment with APK update and matched runs."""
    adb_client = AdbClient(adb_path=config.adb_path)
    discovery = DeviceDiscovery(adb_client)
    target_device = discovery.select_device(target_serial=args.serial)

    exp_store = ExperimentStore(config.data_dir)
    comp_store = ComparisonStore(config.data_dir / "comparisons")
    orchestrator = DifferentialExperimentOrchestrator(adb_client, exp_store, comp_store)

    v1_apk_path = Path(args.apk)
    iterations = getattr(args, "iterations", 3) or 3
    cooldown = getattr(args, "cooldown", 2.0) or 2.0
    policy = StabilizationPolicy(stabilization_cooldown_seconds=cooldown)

    quality_report = orchestrator.run_differential_experiment(
        v0_experiment_id=args.v0_experiment_id,
        v1_apk_path=v1_apk_path,
        serial=target_device.serial,
        iterations=iterations,
        stabilization_policy=policy,
    )

    if getattr(args, "json", False):
        comp_record = comp_store.load_comparison(quality_report.comparison_id)
        out = {
            "quality": quality_report.model_dump(),
            "comparison": comp_record.model_dump(),
        }
        print(json.dumps(out, indent=2))
    else:
        cmp_dir = comp_store.get_comparison_dir(quality_report.comparison_id)
        print(format_human_comparison_quality(quality_report, cmp_dir))

    return 0 if quality_report.is_clean_comparison else 1


def handle_diff_show(args: argparse.Namespace, config: HexnilConfig) -> int:
    """Display a saved differential comparison record."""
    comp_store = ComparisonStore(config.data_dir / "comparisons")
    comp_record = comp_store.load_comparison(args.comparison_id)

    if getattr(args, "json", False):
        print(comp_record.model_dump_json(indent=2))
        return 0

    print(format_human_comparison_show(comp_record))
    return 0


def handle_diff_pairs(args: argparse.Namespace, config: HexnilConfig) -> int:
    """Display matched V0/V1 run pairs for a comparison."""
    comp_store = ComparisonStore(config.data_dir / "comparisons")
    pairs = comp_store.load_comparison_pairs(args.comparison_id)

    if getattr(args, "json", False):
        print(json.dumps([p.model_dump() for p in pairs], indent=2))
        return 0

    print(f"Hexnil Matched Run Pairs ({args.comparison_id})")
    print("-----------------------------------------------------------------------------------------")
    for p in pairs:
        status_sym = "[OK]" if p.pair_status == PairStatus.MATCHED else "[MISMATCH]"
        v0_str = f"V0: {p.v0_duration_ms:.1f} ms" if p.v0_duration_ms is not None else "V0: N/A"
        v1_str = f"V1: {p.v1_duration_ms:.1f} ms" if p.v1_duration_ms is not None else "V1: N/A"
        print(
            f"  {status_sym} [{p.workload_id:<14}] Iteration {p.iteration}: {v0_str:<15} | {v1_str:<15} -> {p.pair_status.value}"
        )
        if p.mismatch_reason:
            print(f"      Reason: {p.mismatch_reason}")

    return 0


def handle_diff_quality(args: argparse.Namespace, config: HexnilConfig) -> int:
    """Display quality audit report of a differential comparison."""
    comp_store = ComparisonStore(config.data_dir / "comparisons")
    quality = comp_store.load_comparison_quality(args.comparison_id)
    if not quality:
        print(f"No comparison quality report found for {args.comparison_id}", file=sys.stderr)
        return 1

    if getattr(args, "json", False):
        print(quality.model_dump_json(indent=2))
        return 0

    cmp_dir = comp_store.get_comparison_dir(args.comparison_id)
    print(format_human_comparison_quality(quality, cmp_dir))
    return 0 if quality.is_clean_comparison else 1


def create_parser() -> argparse.ArgumentParser:


    """Construct CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="hexnil",
        description="Hexnil: Mobile release-validation intelligence system.",
    )
    parser.add_argument(
        "--adb-path",
        dest="adb_path",
        help="Path to adb executable override.",
        default=None,
    )
    parser.add_argument(
        "--data-dir",
        dest="data_dir",
        help="Path to data directory override.",
        default=None,
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable debug logging output.",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command groups")

    # 1. 'device' command group
    device_parser = subparsers.add_parser("device", help="Device management commands")
    device_parser.add_argument(
        "--serial",
        "-s",
        help="Target specific device by ADB serial.",
        default=None,
    )
    device_subparsers = device_parser.add_subparsers(
        dest="subcommand", help="Device subcommands"
    )

    status_parser = device_subparsers.add_parser(
        "status", help="Connect, check health, capture metadata, and persist session"
    )
    status_parser.add_argument(
        "--serial",
        "-s",
        help="Target specific device by ADB serial.",
        default=None,
    )
    status_parser.add_argument(
        "--json",
        action="store_true",
        help="Output result as JSON.",
    )

    list_parser = device_subparsers.add_parser(
        "list", help="List all detected Android devices"
    )
    list_parser.add_argument(
        "--json",
        action="store_true",
        help="Output devices as JSON.",
    )

    # 2. 'telemetry' command group (Phase 2)
    tel_parser = subparsers.add_parser("telemetry", help="Universal telemetry collection commands")
    tel_parser.add_argument(
        "--serial",
        "-s",
        help="Target specific device by ADB serial.",
        default=None,
    )
    tel_subparsers = tel_parser.add_subparsers(
        dest="subcommand", help="Telemetry subcommands"
    )

    tel_collect_parser = tel_subparsers.add_parser(
        "collect", help="Execute workload, collect on-device and host telemetry"
    )
    tel_collect_parser.add_argument(
        "--serial",
        "-s",
        help="Target specific device by ADB serial.",
        default=None,
    )
    tel_collect_parser.add_argument(
        "--workload",
        "--workload-id",
        dest="workload_id",
        help="Deterministic workload identity to execute.",
        default="startup_basic",
    )
    tel_collect_parser.add_argument(
        "--json",
        action="store_true",
        help="Output telemetry records as JSON.",
    )

    tel_show_parser = tel_subparsers.add_parser(
        "show", help="Show telemetry records for an experiment"
    )
    tel_show_parser.add_argument("experiment_id", help="Experiment ID to display")
    tel_show_parser.add_argument(
        "--json",
        action="store_true",
        help="Output records as JSON.",
    )

    # 3. 'experiment' command group
    exp_parser = subparsers.add_parser(
        "experiment", help="Experiment history and records"
    )
    exp_subparsers = exp_parser.add_subparsers(
        dest="subcommand", help="Experiment subcommands"
    )

    exp_list_parser = exp_subparsers.add_parser("list", help="List saved experiments")
    exp_list_parser.add_argument(
        "--json",
        action="store_true",
        help="Output records as JSON.",
    )

    exp_show_parser = exp_subparsers.add_parser(
        "show", help="Show an experiment record"
    )
    exp_show_parser.add_argument("experiment_id", help="Experiment ID to display")
    exp_show_parser.add_argument(
        "--json",
        action="store_true",
        help="Output record as JSON.",
    )

    # 4. 'workload' command group
    wl_parser = subparsers.add_parser(
        "workload", help="Deterministic workload suite and execution"
    )
    wl_subparsers = wl_parser.add_subparsers(
        dest="subcommand", help="Workload subcommands"
    )

    wl_list_parser = wl_subparsers.add_parser("list", help="List registered workloads")
    wl_list_parser.add_argument(
        "--json",
        action="store_true",
        help="Output list as JSON.",
    )

    wl_show_parser = wl_subparsers.add_parser("show", help="Show workload definition")
    wl_show_parser.add_argument("workload_id", help="Workload ID to display")
    wl_show_parser.add_argument(
        "--json",
        action="store_true",
        help="Output definition as JSON.",
    )

    wl_val_parser = wl_subparsers.add_parser("validate", help="Validate workload definition")
    wl_val_parser.add_argument("workload_id", help="Workload ID to validate")
    wl_val_parser.add_argument(
        "--json",
        action="store_true",
        help="Output validation as JSON.",
    )

    wl_run_parser = wl_subparsers.add_parser("run", help="Execute workload against device")
    wl_run_parser.add_argument("workload_id", help="Workload ID to execute")
    wl_run_parser.add_argument(
        "--serial",
        "-s",
        help="Target specific device by ADB serial.",
        default=None,
    )
    wl_run_parser.add_argument(
        "--iterations",
        "-i",
        type=int,
        default=1,
        help="Number of repeated iterations to execute (default: 1).",
    )
    wl_run_parser.add_argument(
        "--json",
        action="store_true",
        help="Output execution run records as JSON.",
    )

    # 5. 'baseline' command group (Phase 4)
    base_parser = subparsers.add_parser(
        "baseline", help="Phase 4 V0 baseline experiment orchestration and audit"
    )
    base_parser.add_argument(
        "--serial",
        "-s",
        help="Target specific device by ADB serial.",
        default=None,
    )
    base_subparsers = base_parser.add_subparsers(
        dest="subcommand", help="Baseline subcommands"
    )

    base_run_parser = base_subparsers.add_parser(
        "run", help="Run reproducible V0 baseline experiment suite"
    )
    base_run_parser.add_argument(
        "--serial",
        "-s",
        help="Target specific device by ADB serial.",
        default=None,
    )
    base_run_parser.add_argument(
        "--iterations",
        "-i",
        type=int,
        default=5,
        help="Number of repeated iterations per workload (default: 5).",
    )
    base_run_parser.add_argument(
        "--suite",
        help="Comma-separated workload IDs or 'all' (default: all).",
        default="all",
    )
    base_run_parser.add_argument(
        "--battery-min",
        type=int,
        default=15,
        help="Minimum battery level percentage required (default: 15).",
    )
    base_run_parser.add_argument(
        "--cooldown",
        type=float,
        default=2.0,
        help="Stabilization cooldown seconds between pre-run actions (default: 2.0).",
    )
    base_run_parser.add_argument(
        "--json",
        action="store_true",
        help="Output quality report and baseline metrics as JSON.",
    )

    base_show_parser = base_subparsers.add_parser(
        "show", help="Show complete baseline experiment record and metrics"
    )
    base_show_parser.add_argument("experiment_id", help="Experiment ID to display")
    base_show_parser.add_argument(
        "--json",
        action="store_true",
        help="Output record as JSON.",
    )

    base_qual_parser = base_subparsers.add_parser(
        "quality", help="Show baseline quality audit report and contamination flags"
    )
    base_qual_parser.add_argument("experiment_id", help="Experiment ID to display")
    base_qual_parser.add_argument(
        "--json",
        action="store_true",
        help="Output quality audit as JSON.",
    )

    base_sum_parser = base_subparsers.add_parser(
        "summary", help="Show derived baseline metrics and uncertainty intervals"
    )
    base_sum_parser.add_argument("experiment_id", help="Experiment ID to display")
    base_sum_parser.add_argument(
        "--json",
        action="store_true",
        help="Output summary as JSON.",
    )

    # 6. 'diff' command group (Phase 5)
    diff_parser = subparsers.add_parser(
        "diff", help="Phase 5 V0 -> V1 differential experiment and run matching"
    )
    diff_parser.add_argument(
        "--serial",
        "-s",
        help="Target specific device by ADB serial.",
        default=None,
    )
    diff_subparsers = diff_parser.add_subparsers(
        dest="subcommand", help="Differential subcommands"
    )

    # diff inspect <v0_experiment_id>
    diff_insp_parser = diff_subparsers.add_parser(
        "inspect", help="Inspect a V0 baseline experiment to verify comparison readiness"
    )
    diff_insp_parser.add_argument("v0_experiment_id", help="V0 Experiment ID to inspect")
    diff_insp_parser.add_argument(
        "--json",
        action="store_true",
        help="Output inspection results as JSON.",
    )

    # diff run <v0_experiment_id> --apk <v1_apk_path>
    diff_run_parser = diff_subparsers.add_parser(
        "run", help="Run V0 -> V1 differential experiment with APK install and matched runs"
    )
    diff_run_parser.add_argument("v0_experiment_id", help="V0 Experiment ID baseline reference")
    diff_run_parser.add_argument(
        "--apk",
        required=True,
        help="Path to target V1 APK file to install and evaluate",
    )
    diff_run_parser.add_argument(
        "--serial",
        "-s",
        help="Target specific device by ADB serial.",
        default=None,
    )
    diff_run_parser.add_argument(
        "--iterations",
        "-i",
        type=int,
        default=3,
        help="Number of repeated iterations per workload (default: 3).",
    )
    diff_run_parser.add_argument(
        "--cooldown",
        type=float,
        default=2.0,
        help="Stabilization cooldown seconds between pre-run actions (default: 2.0).",
    )
    diff_run_parser.add_argument(
        "--json",
        action="store_true",
        help="Output comparison results and quality report as JSON.",
    )

    # diff show <comparison_id>
    diff_show_parser = diff_subparsers.add_parser(
        "show", help="Show complete differential comparison record"
    )
    diff_show_parser.add_argument("comparison_id", help="Comparison ID to display")
    diff_show_parser.add_argument(
        "--json",
        action="store_true",
        help="Output record as JSON.",
    )

    # diff pairs <comparison_id>
    diff_pairs_parser = diff_subparsers.add_parser(
        "pairs", help="Show matched V0/V1 run pairs for a comparison"
    )
    diff_pairs_parser.add_argument("comparison_id", help="Comparison ID to display")
    diff_pairs_parser.add_argument(
        "--json",
        action="store_true",
        help="Output matched pairs as JSON.",
    )

    # diff quality <comparison_id>
    diff_qual_parser = diff_subparsers.add_parser(
        "quality", help="Show differential comparison quality audit and contamination flags"
    )
    diff_qual_parser.add_argument("comparison_id", help="Comparison ID to display")
    diff_qual_parser.add_argument(
        "--json",
        action="store_true",
        help="Output quality audit as JSON.",
    )

    return parser


def main(argv=None) -> int:
    """CLI entry point."""
    parser = create_parser()
    args = parser.parse_args(argv)

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    config = HexnilConfig.load(
        adb_path=args.adb_path,
        data_dir=Path(args.data_dir) if args.data_dir else None,
    )

    is_json = getattr(args, "json", False)

    try:
        if args.command == "device":
            if args.subcommand in (None, "status"):
                return handle_device_status(args, config)
            elif args.subcommand == "list":
                return handle_device_list(args, config)
            else:
                parser.print_help()
                return 1

        elif args.command == "telemetry":
            if args.subcommand in (None, "collect"):
                return handle_telemetry_collect(args, config)
            elif args.subcommand == "show":
                return handle_telemetry_show(args, config)
            else:
                parser.print_help()
                return 1

        elif args.command == "experiment":
            if args.subcommand in (None, "list"):
                return handle_experiment_list(args, config)
            elif args.subcommand == "show":
                return handle_experiment_show(args, config)
            else:
                parser.print_help()
                return 1

        elif args.command == "workload":
            if args.subcommand in (None, "list"):
                return handle_workload_list(args, config)
            elif args.subcommand == "show":
                return handle_workload_show(args, config)
            elif args.subcommand == "validate":
                return handle_workload_validate(args, config)
            elif args.subcommand == "run":
                return handle_workload_run(args, config)
            else:
                parser.print_help()
                return 1

        elif args.command == "baseline":
            if args.subcommand in (None, "run"):
                return handle_baseline_run(args, config)
            elif args.subcommand == "show":
                return handle_baseline_show(args, config)
            elif args.subcommand == "quality":
                return handle_baseline_quality(args, config)
            elif args.subcommand == "summary":
                return handle_baseline_summary(args, config)
            else:
                parser.print_help()
                return 1

        elif args.command == "diff":
            if args.subcommand == "inspect":
                return handle_diff_inspect(args, config)
            elif args.subcommand == "run":
                return handle_diff_run(args, config)
            elif args.subcommand == "show":
                return handle_diff_show(args, config)
            elif args.subcommand == "pairs":
                return handle_diff_pairs(args, config)
            elif args.subcommand == "quality":
                return handle_diff_quality(args, config)
            else:
                parser.print_help()
                return 1

    except HexnilError as exc:
        if is_json:
            error_data = {
                "error": True,
                "type": exc.__class__.__name__,
                "message": exc.message,
                "suggestion": exc.suggestion,
            }
            print(json.dumps(error_data, indent=2), file=sys.stderr)
        else:
            print(f"\n[ERROR] {exc.message}", file=sys.stderr)
            if exc.suggestion:
                print(f"\nAction required:\n{exc.suggestion}", file=sys.stderr)
        return 1
    except Exception as exc:
        if is_json:
            error_data = {
                "error": True,
                "type": exc.__class__.__name__,
                "message": str(exc),
            }
            print(json.dumps(error_data, indent=2), file=sys.stderr)
        else:
            print(f"\n[UNEXPECTED ERROR] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
