"""Domain models for Phase 3 Deterministic Workload Engine."""

import hashlib
import json
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class PreconditionStatus(str, Enum):
    """Evaluation status of a workload precondition."""

    SATISFIED = "SATISFIED"
    NOT_SATISFIED = "NOT_SATISFIED"
    NOT_SUPPORTED = "NOT_SUPPORTED"
    ERROR = "ERROR"


class PreconditionDefinition(BaseModel):
    """Specification of a single required precondition."""

    name: str
    expected_value: Any
    required: bool = True
    description: Optional[str] = None


class PreconditionResult(BaseModel):
    """Outcome of evaluating a single precondition."""

    name: str
    status: PreconditionStatus
    expected_value: Any
    actual_value: Any = None
    message: Optional[str] = None


class StepAction(str, Enum):
    """Permitted workload execution actions. Arbitrary shell commands are prohibited."""

    LAUNCH_APP = "launch_app"
    STOP_APP = "stop_app"
    WAIT = "wait"
    WAIT_FOR_IDLE = "wait_for_idle"
    SCROLL = "scroll"
    COMPUTE_WORK = "compute_work"
    MEMORY_WORK = "memory_work"
    LOCAL_MEDIA_PLAYBACK = "local_media_playback"
    COLLECT_SNAPSHOT = "collect_snapshot"


class WorkloadStep(BaseModel):
    """An individual discrete step in a workload execution sequence."""

    step_id: str
    action: StepAction
    parameters: Dict[str, Any] = Field(default_factory=dict)
    timeout_ms: Optional[int] = None
    description: Optional[str] = None


class DurationLimits(BaseModel):
    """Optional boundaries on acceptable execution duration."""

    min_ms: Optional[float] = None
    max_ms: Optional[float] = None


class WorkloadDefinition(BaseModel):
    """Declarative, versioned workload definition."""

    workload_id: str
    version: str
    description: str
    configuration: Dict[str, Any] = Field(default_factory=dict)
    preconditions: Dict[str, Any] = Field(default_factory=dict)
    steps: List[WorkloadStep] = Field(default_factory=list)
    duration_limits: Optional[DurationLimits] = None

    @field_validator("workload_id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        clean = v.strip().lower()
        if not clean:
            raise ValueError("workload_id cannot be empty")
        return clean

    def canonical_json(self) -> str:
        """Produce deterministic, canonical JSON representation of configuration."""
        # Only the configuration dictionary defines the workload parameter hash.
        # It must NOT include volatile runtime state (timestamps, run IDs).
        return json.dumps(
            self.configuration,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )

    def compute_hash(self) -> str:
        """Compute stable SHA-256 hash of the canonical configuration."""
        payload = self.canonical_json().encode("utf-8")
        return hashlib.sha256(payload).hexdigest()[:16]


class RunStatus(str, Enum):
    """Execution status of a workload run."""

    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PRECONDITION_FAILED = "PRECONDITION_FAILED"
    TIMEOUT = "TIMEOUT"
    UNSUPPORTED = "UNSUPPORTED"
    INVALID = "INVALID"


class StepResult(BaseModel):
    """Result of executing an individual workload step."""

    step_id: str
    action: StepAction
    status: RunStatus
    started_at: str
    ended_at: str
    duration_ms: float
    error: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class WorkloadRun(BaseModel):
    """Record of a single workload execution linked to an experiment."""

    experiment_id: str
    run_id: str
    workload_id: str
    workload_version: str
    configuration_hash: str
    iteration: int = 1
    started_at: str
    ended_at: str
    duration_ms: float
    status: RunStatus
    preconditions: Dict[str, PreconditionResult] = Field(default_factory=dict)
    steps: List[StepResult] = Field(default_factory=list)
    telemetry_count: int = 0
    artifacts: List[str] = Field(default_factory=list)
    error_reason: Optional[str] = None
