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
