"""Hexnil command-line interface for Phase 1 Android Device Foundation."""

import argparse
import datetime
import json
import logging
import sys
from pathlib import Path
from typing import Optional

from hexnil.config import HexnilConfig
from hexnil.device.adb import AdbClient
from hexnil.device.discovery import DeviceDiscovery
from hexnil.device.metadata import MetadataCollector
from hexnil.device.models import ExperimentRecord
from hexnil.exceptions import HexnilError
from hexnil.experiments.ids import generate_experiment_id
from hexnil.experiments.store import ExperimentStore

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


def handle_device_status(args: argparse.Namespace, config: HexnilConfig) -> int:
    """Execute device selection, health check, metadata collection, and persistence."""
    adb_client = AdbClient(
        adb_path=args.adb_path or config.adb_path,
        default_timeout=config.adb_timeout_seconds,
    )
    discovery = DeviceDiscovery(adb_client)

    # 1. Discover and select device
    target_device = discovery.select_device(target_serial=args.serial)

    # 2. Collect metadata & perform serial-targeted health check
    collector = MetadataCollector(adb_client)
    metadata, adb_status, warnings = collector.collect(target_device.serial)

    # 3. Generate unique experiment ID and timestamp
    store = ExperimentStore(config.data_dir)
    experiment_id = generate_experiment_id(config.data_dir)
    created_at = (
        datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
    )

    # 4. Construct record
    record = ExperimentRecord(
        experiment_id=experiment_id,
        created_at=created_at,
        device=metadata,
        adb=adb_status,
        phase="01_android_device_foundation",
        status="ready",
        warnings=warnings,
    )

    # 5. Persist record locally
    saved_path = store.save(record)

    # 6. Output result
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
        print(
            json.dumps(
                [d.model_dump() for d in devices],
                indent=2,
            )
        )
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
        print(
            json.dumps(
                [r.model_dump() for r in records],
                indent=2,
            )
        )
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

    # 'device' command group
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

    # 'device status'
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

    # 'device list'
    list_parser = device_subparsers.add_parser(
        "list", help="List all detected Android devices"
    )
    list_parser.add_argument(
        "--json",
        action="store_true",
        help="Output devices as JSON.",
    )

    # 'experiment' command group
    exp_parser = subparsers.add_parser(
        "experiment", help="Experiment history and records"
    )
    exp_subparsers = exp_parser.add_subparsers(
        dest="subcommand", help="Experiment subcommands"
    )

    # 'experiment list'
    exp_list_parser = exp_subparsers.add_parser("list", help="List saved experiments")
    exp_list_parser.add_argument(
        "--json",
        action="store_true",
        help="Output records as JSON.",
    )

    # 'experiment show'
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
        # Default 'device' with no subcommand: treat as 'device status'
        if args.command == "device":
            if args.subcommand in (None, "status"):
                return handle_device_status(args, config)
            elif args.subcommand == "list":
                return handle_device_list(args, config)
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
