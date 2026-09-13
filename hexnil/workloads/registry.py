"""Workload registry for discovering, loading, and validating workloads."""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from hexnil.workloads.models import WorkloadDefinition

logger = logging.getLogger("hexnil.workloads.registry")

DEFAULT_DEFINITIONS_DIR = Path(__file__).parent / "definitions"


class WorkloadNotFoundError(Exception):
    """Raised when a requested workload ID is not found in the registry."""

    def __init__(self, workload_id: str, available: List[str]):
        super().__init__(
            f"Workload '{workload_id}' not found. Available workloads: {', '.join(available)}"
        )
        self.workload_id = workload_id
        self.available = available


class WorkloadRegistry:
    """Discovers, loads, and validates declarative workload definitions."""

    def __init__(self, definitions_dir: Optional[Path] = None):
        self.definitions_dir = definitions_dir or DEFAULT_DEFINITIONS_DIR
        self._in_memory: Dict[str, WorkloadDefinition] = {}

    def register(self, definition: WorkloadDefinition) -> None:
        """Register a workload definition programmatically."""
        self._in_memory[definition.workload_id] = definition

    def list_workloads(self) -> List[WorkloadDefinition]:
        """List all available workload definitions sorted by workload_id."""
        workloads: Dict[str, WorkloadDefinition] = dict(self._in_memory)

        if self.definitions_dir.exists() and self.definitions_dir.is_dir():
            for file_path in self.definitions_dir.glob("*.json"):
                try:
                    content = file_path.read_text(encoding="utf-8")
                    data = json.loads(content)
                    definition = WorkloadDefinition.model_validate(data)
                    if definition.workload_id not in workloads:
                        workloads[definition.workload_id] = definition
                except Exception as exc:
                    logger.warning("Failed to parse workload file %s: %s", file_path.name, exc)

        return sorted(workloads.values(), key=lambda w: w.workload_id)

    def get(self, workload_id: str) -> WorkloadDefinition:
        """Retrieve a workload definition by ID."""
        clean_id = workload_id.strip().lower()
        if clean_id in self._in_memory:
            return self._in_memory[clean_id]

        target_file = self.definitions_dir / f"{clean_id}.json"
        if target_file.exists() and target_file.is_file():
            try:
                content = target_file.read_text(encoding="utf-8")
                data = json.loads(content)
                return WorkloadDefinition.model_validate(data)
            except Exception as exc:
                raise ValueError(f"Failed to load workload '{clean_id}' from {target_file}: {exc}") from exc

        # Also scan directory in case filename differs from workload_id
        all_workloads = self.list_workloads()
        for w in all_workloads:
            if w.workload_id == clean_id:
                return w

        available = [w.workload_id for w in all_workloads]
        raise WorkloadNotFoundError(clean_id, available)

    def validate(self, workload_id: str) -> Tuple[bool, List[str]]:
        """Validate a workload definition, checking steps, actions, and bounds."""
        errors: List[str] = []
        try:
            definition = self.get(workload_id)
        except Exception as exc:
            return False, [str(exc)]

        if not definition.steps:
            errors.append(f"Workload '{workload_id}' must define at least one step.")

        step_ids = set()
        for step in definition.steps:
            if step.step_id in step_ids:
                errors.append(f"Duplicate step ID '{step.step_id}' in workload '{workload_id}'.")
            step_ids.add(step.step_id)

        if definition.duration_limits:
            limits = definition.duration_limits
            if limits.min_ms is not None and limits.max_ms is not None:
                if limits.min_ms > limits.max_ms:
                    errors.append(f"min_ms ({limits.min_ms}) exceeds max_ms ({limits.max_ms}).")

        return len(errors) == 0, errors
