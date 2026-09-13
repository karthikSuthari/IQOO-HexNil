"""Local experiment store for persisting and retrieving Phase 1 & 2 records."""

import json
import logging
from pathlib import Path
from typing import List, Optional, Set

from hexnil.device.models import ExperimentRecord
from hexnil.exceptions import ExperimentPersistenceError
from hexnil.telemetry.models import TelemetryRecord

logger = logging.getLogger("hexnil.store")


class ExperimentStore:
    """Manages local persistence for Hexnil experiments, telemetry, and artifacts."""

    def __init__(self, store_dir: Path):
        self.store_dir = store_dir
        self.store_dir.mkdir(parents=True, exist_ok=True)

    def get_experiment_dir(self, experiment_id: str) -> Path:
        """Get the directory path for an experiment."""
        return self.store_dir / experiment_id

    def ensure_experiment_dir(self, experiment_id: str) -> Path:
        """Ensure the experiment directory and its subfolders exist."""
        exp_dir = self.get_experiment_dir(experiment_id)
        exp_dir.mkdir(parents=True, exist_ok=True)
        (exp_dir / "telemetry").mkdir(parents=True, exist_ok=True)
        (exp_dir / "artifacts").mkdir(parents=True, exist_ok=True)
        return exp_dir

    def get_path(self, experiment_id: str) -> Path:
        """Get file path for an experiment's metadata.

        Prefers directory-based metadata.json, falls back to legacy flat .json.
        """
        dir_path = self.get_experiment_dir(experiment_id) / "metadata.json"
        if dir_path.exists():
            return dir_path
        return self.store_dir / f"{experiment_id}.json"

    def save(self, record: ExperimentRecord, as_directory: bool = True) -> Path:
        """Persist an experiment record to disk atomically as formatted JSON.

        If as_directory is True, stores in EXP-.../metadata.json (Phase 2 structure).
        Also writes legacy flat EXP-....json for backward compatibility.
        """
        exp_id = record.experiment_id
        json_content = record.model_dump_json(indent=2)

        try:
            # 1. Directory-based storage
            if as_directory:
                exp_dir = self.ensure_experiment_dir(exp_id)
                meta_path = exp_dir / "metadata.json"
                meta_temp = exp_dir / ".metadata.json.tmp"
                meta_temp.write_text(json_content, encoding="utf-8")
                meta_temp.replace(meta_path)

            # 2. Flat file for legacy backward compatibility
            flat_path = self.store_dir / f"{exp_id}.json"
            flat_temp = self.store_dir / f".{exp_id}.tmp"
            flat_temp.write_text(json_content, encoding="utf-8")
            flat_temp.replace(flat_path)

            logger.info("Persisted experiment record to: %s", exp_id)
            return self.get_path(exp_id)
        except Exception as exc:
            raise ExperimentPersistenceError(str(self.get_path(exp_id)), str(exc)) from exc

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

    def append_telemetry(
        self,
        experiment_id: str,
        records: List[TelemetryRecord],
        filename: Optional[str] = None,
        source: Optional[str] = None,
    ) -> Path:
        """Append telemetry records in JSONL format."""
        exp_dir = self.ensure_experiment_dir(experiment_id)
        telemetry_dir = exp_dir / "telemetry"
        chosen_file = filename or (f"{source}.jsonl" if source else "android.jsonl")
        if not chosen_file.endswith(".jsonl"):
            chosen_file = f"{chosen_file}.jsonl"
        target_file = telemetry_dir / chosen_file

        try:
            with target_file.open("a", encoding="utf-8") as f:
                for rec in records:
                    f.write(rec.to_jsonl_line() + "\n")
            logger.info("Appended %d records to %s", len(records), target_file)
            return target_file
        except Exception as exc:
            raise ExperimentPersistenceError(str(target_file), str(exc)) from exc

    def save_artifact(
        self,
        experiment_id: str,
        filename: str,
        content: str | bytes,
    ) -> Path:
        """Save raw artifact (e.g. logcat.txt, dumpsys.txt) under artifacts/."""
        exp_dir = self.ensure_experiment_dir(experiment_id)
        artifacts_dir = exp_dir / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        target_file = artifacts_dir / filename

        try:
            if isinstance(content, bytes):
                target_file.write_bytes(content)
            else:
                target_file.write_text(content, encoding="utf-8")
            logger.info("Saved artifact %s", target_file)
            return target_file
        except Exception as exc:
            raise ExperimentPersistenceError(str(target_file), str(exc)) from exc

    def load_telemetry(
        self,
        experiment_id: str,
        filename: Optional[str] = None,
        source: Optional[str] = None,
    ) -> List[TelemetryRecord]:
        """Load telemetry records from JSONL file(s)."""
        exp_dir = self.get_experiment_dir(experiment_id)
        telemetry_dir = exp_dir / "telemetry"

        if not telemetry_dir.exists():
            return []

        target_name = filename or (f"{source}.jsonl" if source else None)
        if target_name and not target_name.endswith(".jsonl"):
            target_name = f"{target_name}.jsonl"

        files_to_read = (
            [telemetry_dir / target_name] if target_name else list(telemetry_dir.glob("*.jsonl"))
        )
        records: List[TelemetryRecord] = []

        for f in files_to_read:
            if not f.is_file():
                continue
            for line in f.read_text(encoding="utf-8").splitlines():
                clean_line = line.strip()
                if clean_line:
                    try:
                        records.append(TelemetryRecord.model_validate_json(clean_line))
                    except Exception as exc:
                        logger.warning("Skipping corrupted telemetry line in %s: %s", f.name, exc)

        return records

    def list_all(self) -> List[ExperimentRecord]:
        """List all valid experiment records sorted by ID descending."""
        records: List[ExperimentRecord] = []
        seen_ids: Set[str] = set()

        # Check directories first
        for dir_path in self.store_dir.glob("EXP-*"):
            if dir_path.is_dir():
                meta_file = dir_path / "metadata.json"
                if meta_file.is_file():
                    try:
                        rec = ExperimentRecord.model_validate_json(meta_file.read_text(encoding="utf-8"))
                        records.append(rec)
                        seen_ids.add(rec.experiment_id)
                    except Exception as exc:
                        logger.warning("Skipping invalid record in %s: %s", dir_path.name, exc)

        # Check flat files
        for file_path in self.store_dir.glob("EXP-*.json"):
            exp_id = file_path.stem
            if exp_id not in seen_ids:
                try:
                    rec = ExperimentRecord.model_validate_json(file_path.read_text(encoding="utf-8"))
                    records.append(rec)
                    seen_ids.add(rec.experiment_id)
                except Exception as exc:
                    logger.warning("Skipping invalid record %s: %s", file_path.name, exc)

        records.sort(key=lambda r: r.experiment_id, reverse=True)
        return records
