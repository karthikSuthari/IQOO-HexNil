"""Local experiment store for persisting and retrieving Phase 1 records."""

import json
import logging
from pathlib import Path
from typing import List, Optional

from hexnil.device.models import ExperimentRecord
from hexnil.exceptions import ExperimentPersistenceError

logger = logging.getLogger("hexnil.store")


class ExperimentStore:
    """Manages local JSON persistence for Hexnil experiments."""

    def __init__(self, store_dir: Path):
        self.store_dir = store_dir
        self.store_dir.mkdir(parents=True, exist_ok=True)

    def get_path(self, experiment_id: str) -> Path:
        """Get file path for a given experiment ID."""
        return self.store_dir / f"{experiment_id}.json"

    def save(self, record: ExperimentRecord) -> Path:
        """Persist an experiment record to disk atomically as formatted JSON."""
        target_path = self.get_path(record.experiment_id)
        temp_path = self.store_dir / f".{record.experiment_id}.tmp"

        try:
            # Format JSON with 2-space indentation
            json_content = record.model_dump_json(indent=2)
            temp_path.write_text(json_content, encoding="utf-8")
            temp_path.replace(target_path)
            logger.info("Persisted experiment record to: %s", target_path)
            return target_path
        except Exception as exc:
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
            raise ExperimentPersistenceError(str(target_path), str(exc)) from exc

    def load(self, experiment_id: str) -> ExperimentRecord:
        """Load and validate an experiment record from disk."""
        target_path = self.get_path(experiment_id)
        if not target_path.exists():
            raise ExperimentPersistenceError(
                str(target_path),
                f"Experiment record '{experiment_id}' does not exist.",
                suggestion="Run 'python -m hexnil experiment list' to see available records.",
            )

        try:
            content = target_path.read_text(encoding="utf-8")
            return ExperimentRecord.model_validate_json(content)
        except Exception as exc:
            raise ExperimentPersistenceError(
                str(target_path),
                f"Corrupted or invalid experiment JSON: {exc}",
                suggestion="Verify the file contents or create a new experiment session.",
            ) from exc

    def list_all(self) -> List[ExperimentRecord]:
        """List all valid experiment records sorted by ID descending."""
        records: List[ExperimentRecord] = []
        for file_path in self.store_dir.glob("EXP-*.json"):
            try:
                content = file_path.read_text(encoding="utf-8")
                records.append(ExperimentRecord.model_validate_json(content))
            except Exception as exc:
                logger.warning("Skipping invalid record %s: %s", file_path.name, exc)

        records.sort(key=lambda r: r.experiment_id, reverse=True)
        return records
