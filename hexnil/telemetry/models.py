"""Universal telemetry data models for Hexnil Phase 2."""

from enum import Enum
from typing import Any, Dict, Optional, Union
from pydantic import BaseModel, ConfigDict, Field

from hexnil.device.models import DeviceMetadata


class CapabilityStatus(str, Enum):
    """Signal collection capability classifications."""

    UNIVERSAL = "UNIVERSAL"
    CONDITIONAL = "CONDITIONAL"
    UNSUPPORTED = "UNSUPPORTED"


class MetricValue(BaseModel):
    """Container for a single telemetry metric measurement.

    Never uses fake placeholders (e.g. -1, 999) for missing data.
    """

    name: str
    value: Optional[Union[float, int, str, bool]] = None
    unit: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


class WorkloadIdentity(BaseModel):
    """Identifies the executed workload and iteration."""

    id: str = "baseline_idle"
    iteration: int = 1

    model_config = ConfigDict(extra="ignore")


class SoftwareIdentity(BaseModel):
    """Application and software package metadata."""

    package: str = "com.example.iqoo_hexnil"
    version_name: Optional[str] = "1.0"
    version_code: Optional[int] = 1

    model_config = ConfigDict(extra="ignore")


class TelemetryRecord(BaseModel):
    """Unified telemetry record representing a single timestamped measurement."""

    experiment_id: str
    timestamp: str
    device: DeviceMetadata
    software: SoftwareIdentity = Field(default_factory=SoftwareIdentity)
    workload: WorkloadIdentity = Field(default_factory=WorkloadIdentity)
    metric: MetricValue
    source: str  # 'android_app', 'adb', 'benchmark'
    capability: CapabilityStatus
    reason: Optional[str] = None

    model_config = ConfigDict(extra="ignore")

    def to_jsonl_line(self) -> str:
        """Format record as a single-line JSON string suitable for JSONL."""
        return self.model_dump_json()
