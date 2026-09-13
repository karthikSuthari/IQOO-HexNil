"""Host-side ADB telemetry collectors for Hexnil Phase 2."""

import datetime
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from hexnil.device.adb import AdbClient
from hexnil.device.models import DeviceMetadata
from hexnil.telemetry.models import (
    CapabilityStatus,
    MetricValue,
    SoftwareIdentity,
    TelemetryRecord,
    WorkloadIdentity,
)

logger = logging.getLogger("hexnil.telemetry.adb")


def now_iso() -> str:
    """Current UTC timestamp formatted as ISO-8601."""
    return (
        datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
    )


class BaseAdbCollector:
    """Base class for ADB-derived host telemetry collectors."""

    def __init__(self, adb_client: AdbClient):
        self.adb = adb_client

    def build_record(
        self,
        experiment_id: str,
        device: DeviceMetadata,
        software: SoftwareIdentity,
        workload: WorkloadIdentity,
        name: str,
        value: Optional[float | int | str | bool],
        unit: Optional[str],
        capability: CapabilityStatus,
        reason: Optional[str] = None,
    ) -> TelemetryRecord:
        return TelemetryRecord(
            experiment_id=experiment_id,
            timestamp=now_iso(),
            device=device,
            software=software,
            workload=workload,
            metric=MetricValue(name=name, value=value, unit=unit),
            source="adb",
            capability=capability,
            reason=reason,
        )


class AdbLogcatCollector(BaseAdbCollector):
    """Captures bounded logcat logs and persists raw artifact."""

    def collect(
        self,
        serial: str,
        experiment_id: str,
        device: DeviceMetadata,
        software: SoftwareIdentity,
        workload: WorkloadIdentity,
        artifacts_dir: Path,
        max_lines: int = 200,
    ) -> List[TelemetryRecord]:
        records: List[TelemetryRecord] = []
        artifact_path = artifacts_dir / "logcat.txt"

        try:
            raw_log = self.adb.run_serial_cmd(
                serial, ["logcat", "-d", "-t", str(max_lines)], timeout=10.0, check=False
            )
            artifact_path.write_text(raw_log, encoding="utf-8")
            line_count = len(raw_log.splitlines())

            records.append(
                self.build_record(
                    experiment_id=experiment_id,
                    device=device,
                    software=software,
                    workload=workload,
                    name="adb_logcat_lines",
                    value=line_count,
                    unit="lines",
                    capability=CapabilityStatus.UNIVERSAL,
                )
            )
        except Exception as exc:
            logger.warning("Logcat collection failed on %s: %s", serial, exc)
            records.append(
                self.build_record(
                    experiment_id=experiment_id,
                    device=device,
                    software=software,
                    workload=workload,
                    name="adb_logcat_lines",
                    value=None,
                    unit="lines",
                    capability=CapabilityStatus.UNSUPPORTED,
                    reason=f"Logcat capture failed: {exc}",
                )
            )

        return records


class AdbMeminfoCollector(BaseAdbCollector):
    """Collects process memory statistics via 'dumpsys meminfo <package>'."""

    def parse_meminfo(self, raw_output: str) -> Dict[str, int]:
        """Parse key memory metrics from dumpsys meminfo output."""
        metrics: Dict[str, int] = {}
        # Match lines like: Native Heap  26127   26076   ...
        patterns = {
            "native_heap_pss_kb": r"Native Heap\s+(\d+)",
            "dalvik_heap_pss_kb": r"Dalvik Heap\s+(\d+)",
            "total_pss_kb": r"TOTAL PSS:\s+(\d+)|TOTAL\s+(\d+)",
        }
        for metric_name, regex in patterns.items():
            match = re.search(regex, raw_output)
            if match:
                val = next((g for g in match.groups() if g is not None), None)
                if val:
                    metrics[metric_name] = int(val)
        return metrics

    def collect(
        self,
        serial: str,
        experiment_id: str,
        device: DeviceMetadata,
        software: SoftwareIdentity,
        workload: WorkloadIdentity,
        artifacts_dir: Path,
    ) -> List[TelemetryRecord]:
        records: List[TelemetryRecord] = []
        artifact_path = artifacts_dir / "dumpsys_meminfo.txt"

        try:
            raw_mem = self.adb.run_serial_cmd(
                serial, ["shell", "dumpsys", "meminfo", software.package], timeout=10.0, check=False
            )
            artifact_path.write_text(raw_mem, encoding="utf-8")

            parsed = self.parse_meminfo(raw_mem)
            if not parsed:
                records.append(
                    self.build_record(
                        experiment_id=experiment_id,
                        device=device,
                        software=software,
                        workload=workload,
                        name="adb_meminfo_total_pss_kb",
                        value=None,
                        unit="kilobytes",
                        capability=CapabilityStatus.CONDITIONAL,
                        reason="Process not active or meminfo table not populated yet",
                    )
                )
            else:
                for name, val in parsed.items():
                    records.append(
                        self.build_record(
                            experiment_id=experiment_id,
                            device=device,
                            software=software,
                            workload=workload,
                            name=f"adb_mem_{name}",
                            value=val,
                            unit="kilobytes",
                            capability=CapabilityStatus.UNIVERSAL,
                        )
                    )
        except Exception as exc:
            logger.warning("dumpsys meminfo failed on %s: %s", serial, exc)
            records.append(
                self.build_record(
                    experiment_id=experiment_id,
                    device=device,
                    software=software,
                    workload=workload,
                    name="adb_meminfo_total_pss_kb",
                    value=None,
                    unit="kilobytes",
                    capability=CapabilityStatus.UNSUPPORTED,
                    reason=f"dumpsys meminfo error: {exc}",
                )
            )

        return records


class AdbGfxinfoCollector(BaseAdbCollector):
    """Collects graphics frame timing & jank statistics via 'dumpsys gfxinfo <package>'."""

    def parse_gfxinfo(self, raw_output: str) -> Dict[str, float | int]:
        """Parse frame metrics from dumpsys gfxinfo."""
        metrics: Dict[str, float | int] = {}

        total_match = re.search(r"Total frames rendered:\s+(\d+)", raw_output)
        if total_match:
            metrics["total_frames"] = int(total_match.group(1))

        janky_match = re.search(r"Janky frames:\s+(\d+)\s*\(([\d\.]+)%\)", raw_output)
        if janky_match:
            metrics["janky_frames"] = int(janky_match.group(1))
            metrics["janky_percentage"] = float(janky_match.group(2))

        p50_match = re.search(r"50th percentile:\s+(\d+)ms", raw_output)
        if p50_match:
            metrics["p50_ms"] = int(p50_match.group(1))

        p90_match = re.search(r"90th percentile:\s+(\d+)ms", raw_output)
        if p90_match:
            metrics["p90_ms"] = int(p90_match.group(1))

        p95_match = re.search(r"95th percentile:\s+(\d+)ms", raw_output)
        if p95_match:
            metrics["p95_ms"] = int(p95_match.group(1))

        p99_match = re.search(r"99th percentile:\s+(\d+)ms", raw_output)
        if p99_match:
            metrics["p99_ms"] = int(p99_match.group(1))

        return metrics

    def collect(
        self,
        serial: str,
        experiment_id: str,
        device: DeviceMetadata,
        software: SoftwareIdentity,
        workload: WorkloadIdentity,
        artifacts_dir: Path,
    ) -> List[TelemetryRecord]:
        records: List[TelemetryRecord] = []
        artifact_path = artifacts_dir / "dumpsys_gfxinfo.txt"

        try:
            raw_gfx = self.adb.run_serial_cmd(
                serial, ["shell", "dumpsys", "gfxinfo", software.package], timeout=10.0, check=False
            )
            artifact_path.write_text(raw_gfx, encoding="utf-8")

            parsed = self.parse_gfxinfo(raw_gfx)
            if not parsed:
                records.append(
                    self.build_record(
                        experiment_id=experiment_id,
                        device=device,
                        software=software,
                        workload=workload,
                        name="adb_gfx_total_frames",
                        value=None,
                        unit="frames",
                        capability=CapabilityStatus.CONDITIONAL,
                        reason="No gfxinfo frame stats recorded yet for package",
                    )
                )
            else:
                for name, val in parsed.items():
                    unit = "percent" if "percent" in name else ("ms" if "ms" in name else "frames")
                    records.append(
                        self.build_record(
                            experiment_id=experiment_id,
                            device=device,
                            software=software,
                            workload=workload,
                            name=f"adb_gfx_{name}",
                            value=val,
                            unit=unit,
                            capability=CapabilityStatus.UNIVERSAL,
                        )
                    )
        except Exception as exc:
            logger.warning("dumpsys gfxinfo failed on %s: %s", serial, exc)
            records.append(
                self.build_record(
                    experiment_id=experiment_id,
                    device=device,
                    software=software,
                    workload=workload,
                    name="adb_gfx_total_frames",
                    value=None,
                    unit="frames",
                    capability=CapabilityStatus.UNSUPPORTED,
                    reason=f"dumpsys gfxinfo error: {exc}",
                )
            )

        return records


class AdbThermalCollector(BaseAdbCollector):
    """Collects hardware temperatures and thermal status via 'dumpsys thermalservice'."""

    def parse_thermal(self, raw_output: str) -> Dict[str, float]:
        """Parse HAL thermal temperatures from dumpsys thermalservice."""
        temps: Dict[str, float] = {}
        # Parse Temperature{mValue=34.603, mType=0, mName=CPU, mStatus=0}
        pattern = re.compile(r"Temperature\{mValue=([\d\.\-]+),\s*mType=\d+,\s*mName=([a-zA-Z0-9_\-]+)")
        for line in raw_output.splitlines():
            match = pattern.search(line)
            if match:
                val = float(match.group(1))
                name = match.group(2).lower()
                temps[name] = val
        return temps

    def collect(
        self,
        serial: str,
        experiment_id: str,
        device: DeviceMetadata,
        software: SoftwareIdentity,
        workload: WorkloadIdentity,
        artifacts_dir: Path,
    ) -> List[TelemetryRecord]:
        records: List[TelemetryRecord] = []
        artifact_path = artifacts_dir / "dumpsys_thermalservice.txt"

        try:
            raw_thermal = self.adb.run_serial_cmd(
                serial, ["shell", "dumpsys", "thermalservice"], timeout=10.0, check=False
            )
            artifact_path.write_text(raw_thermal, encoding="utf-8")

            parsed = self.parse_thermal(raw_thermal)
            if not parsed:
                records.append(
                    self.build_record(
                        experiment_id=experiment_id,
                        device=device,
                        software=software,
                        workload=workload,
                        name="adb_thermal_cpu_celsius",
                        value=None,
                        unit="celsius",
                        capability=CapabilityStatus.CONDITIONAL,
                        reason="Thermalservice HAL does not expose component temperatures",
                    )
                )
            else:
                for comp, temp_val in parsed.items():
                    records.append(
                        self.build_record(
                            experiment_id=experiment_id,
                            device=device,
                            software=software,
                            workload=workload,
                            name=f"adb_thermal_{comp}_celsius",
                            value=temp_val,
                            unit="celsius",
                            capability=CapabilityStatus.UNIVERSAL,
                        )
                    )
        except Exception as exc:
            logger.warning("dumpsys thermalservice failed on %s: %s", serial, exc)
            records.append(
                self.build_record(
                    experiment_id=experiment_id,
                    device=device,
                    software=software,
                    workload=workload,
                    name="adb_thermal_cpu_celsius",
                    value=None,
                    unit="celsius",
                    capability=CapabilityStatus.UNSUPPORTED,
                    reason=f"dumpsys thermalservice error: {exc}",
                )
            )

        return records


class AdbBatterystatsCollector(BaseAdbCollector):
    """Collects battery discharge proxies and state via 'dumpsys batterystats'."""

    def collect(
        self,
        serial: str,
        experiment_id: str,
        device: DeviceMetadata,
        software: SoftwareIdentity,
        workload: WorkloadIdentity,
        artifacts_dir: Path,
    ) -> List[TelemetryRecord]:
        records: List[TelemetryRecord] = []
        artifact_path = artifacts_dir / "dumpsys_batterystats.txt"

        try:
            raw_bat = self.adb.run_serial_cmd(
                serial, ["shell", "dumpsys", "batterystats", "--charged", software.package], timeout=10.0, check=False
            )
            artifact_path.write_text(raw_bat, encoding="utf-8")

            # Extract capacity if present (e.g. Capacity: 5000, Computed drain: ...)
            records.append(
                self.build_record(
                    experiment_id=experiment_id,
                    device=device,
                    software=software,
                    workload=workload,
                    name="adb_batterystats_snapshot_bytes",
                    value=len(raw_bat),
                    unit="bytes",
                    capability=CapabilityStatus.UNIVERSAL,
                )
            )
        except Exception as exc:
            logger.warning("dumpsys batterystats failed on %s: %s", serial, exc)
            records.append(
                self.build_record(
                    experiment_id=experiment_id,
                    device=device,
                    software=software,
                    workload=workload,
                    name="adb_batterystats_snapshot_bytes",
                    value=None,
                    unit="bytes",
                    capability=CapabilityStatus.UNSUPPORTED,
                    reason=f"dumpsys batterystats error: {exc}",
                )
            )

        return records


class AdbPerfettoCollector(BaseAdbCollector):
    """Probes Perfetto capability and captures bounded trace when supported."""

    def collect(
        self,
        serial: str,
        experiment_id: str,
        device: DeviceMetadata,
        software: SoftwareIdentity,
        workload: WorkloadIdentity,
        artifacts_dir: Path,
        duration_seconds: int = 2,
    ) -> List[TelemetryRecord]:
        records: List[TelemetryRecord] = []
        which_out = self.adb.run_serial_cmd(serial, ["shell", "which", "perfetto"], check=False).strip()

        if not which_out or "not found" in which_out.lower():
            records.append(
                self.build_record(
                    experiment_id=experiment_id,
                    device=device,
                    software=software,
                    workload=workload,
                    name="adb_perfetto_trace_status",
                    value=None,
                    unit=None,
                    capability=CapabilityStatus.UNSUPPORTED,
                    reason="Perfetto executable not present on Android system",
                )
            )
            return records

        # Perfetto binary exists on device
        trace_file = artifacts_dir / "perfetto_trace.pftrace"
        device_tmp_trace = f"/data/local/tmp/hexnil_{experiment_id}.pftrace"

        try:
            cmd = [
                "shell",
                "perfetto",
                "-o",
                device_tmp_trace,
                "-t",
                f"{duration_seconds}s",
                "sched",
                "freq",
                "idle",
                "am",
            ]
            self.adb.run_serial_cmd(serial, cmd, timeout=duration_seconds + 5.0, check=False)
            # Pull trace to artifacts directory
            self.adb.run_serial_cmd(serial, ["pull", device_tmp_trace, str(trace_file)], timeout=10.0, check=False)
            # Clean up temp file on device
            self.adb.run_serial_cmd(serial, ["shell", "rm", "-f", device_tmp_trace], check=False)

            if trace_file.exists() and trace_file.stat().st_size > 0:
                records.append(
                    self.build_record(
                        experiment_id=experiment_id,
                        device=device,
                        software=software,
                        workload=workload,
                        name="adb_perfetto_trace_bytes",
                        value=trace_file.stat().st_size,
                        unit="bytes",
                        capability=CapabilityStatus.UNIVERSAL,
                    )
                )
            else:
                records.append(
                    self.build_record(
                        experiment_id=experiment_id,
                        device=device,
                        software=software,
                        workload=workload,
                        name="adb_perfetto_trace_bytes",
                        value=None,
                        unit="bytes",
                        capability=CapabilityStatus.CONDITIONAL,
                        reason="Perfetto trace completed but returned 0 bytes (SELinux or config restricted)",
                    )
                )
        except Exception as exc:
            logger.warning("Perfetto trace capture failed on %s: %s", serial, exc)
            records.append(
                self.build_record(
                    experiment_id=experiment_id,
                    device=device,
                    software=software,
                    workload=workload,
                    name="adb_perfetto_trace_bytes",
                    value=None,
                    unit="bytes",
                    capability=CapabilityStatus.CONDITIONAL,
                    reason=f"Perfetto capture error: {exc}",
                )
            )

        return records
