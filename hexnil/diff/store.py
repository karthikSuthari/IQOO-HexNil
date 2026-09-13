"""Local storage and persistence for Phase 5 differential experiments."""

import datetime
import json
import logging
from pathlib import Path
import re
from typing import List, Optional, Set

from hexnil.diff.models import (
    ComparisonQualityReport,
    ComparisonRecord,
    ComparisonRunPair,
)
from hexnil.exceptions import ExperimentPersistenceError

logger = logging.getLogger("hexnil.diff.store")

CMP_ID_PATTERN = re.compile(r"^CMP-(\d{8})-(\d{3,})$")


def get_existing_comparison_ids(store_dir: Path) -> Set[str]:
    """Retrieve all existing comparison IDs stored in directory."""
    if not store_dir.exists():
        return set()
    ids = set()
    for item in store_dir.glob("CMP-*"):
        if item.is_dir() and CMP_ID_PATTERN.match(item.name):
            ids.add(item.name)
    return ids


def generate_comparison_id(
    store_dir: Path,
    target_date: Optional[datetime.date] = None,
) -> str:
    """Generate a unique deterministic comparison ID: CMP-YYYYMMDD-001."""
    date_obj = target_date or datetime.date.today()
    date_str = date_obj.strftime("%Y%m%d")

    existing = get_existing_comparison_ids(store_dir)
    highest_seq = 0
    for cid in existing:
        match = CMP_ID_PATTERN.match(cid)
        if match:
            item_date, seq_str = match.groups()
            if item_date == date_str:
                seq = int(seq_str)
                if seq > highest_seq:
                    highest_seq = seq

    new_seq = highest_seq + 1
    return f"CMP-{date_str}-{new_seq:03d}"


class ComparisonStore:
    """Manages persistence for V0 -> V1 differential comparisons and paired evidence."""

    def __init__(self, comparisons_dir: Path):
        self.comparisons_dir = comparisons_dir
        self.comparisons_dir.mkdir(parents=True, exist_ok=True)

    def generate_comparison_id(self) -> str:
        """Generate next sequential comparison ID."""
        return generate_comparison_id(self.comparisons_dir)

    def get_comparison_dir(self, comparison_id: str) -> Path:
        """Get the directory path for a comparison."""
        return self.comparisons_dir / comparison_id

    def ensure_comparison_dir(self, comparison_id: str) -> Path:
        """Ensure the comparison directory and subfolders exist."""
        cmp_dir = self.get_comparison_dir(comparison_id)
        cmp_dir.mkdir(parents=True, exist_ok=True)
        (cmp_dir / "v1_telemetry").mkdir(parents=True, exist_ok=True)
        (cmp_dir / "v1_artifacts").mkdir(parents=True, exist_ok=True)
        (cmp_dir / "v1_workload_runs").mkdir(parents=True, exist_ok=True)
        return cmp_dir

    def save_comparison(self, record: ComparisonRecord) -> Path:
        """Persist master ComparisonRecord and decomposed artifacts."""
        cmp_id = record.comparison_id
        cmp_dir = self.ensure_comparison_dir(cmp_id)

        try:
            # 1. Master comparison.json
            cmp_file = cmp_dir / "comparison.json"
            cmp_file.write_text(record.model_dump_json(indent=2), encoding="utf-8")

            # 2. v0_reference.json
            v0_ref = {
                "v0_experiment_id": record.v0_experiment_id,
                "v0_software": record.v0_software.model_dump(),
                "device_serial": record.device.serial,
            }
            (cmp_dir / "v0_reference.json").write_text(json.dumps(v0_ref, indent=2), encoding="utf-8")

            # 3. v1_software.json
            (cmp_dir / "v1_software.json").write_text(record.v1_software.model_dump_json(indent=2), encoding="utf-8")

            # 4. environment_comparison.json
            (cmp_dir / "environment_comparison.json").write_text(
                record.environment_comparison.model_dump_json(indent=2), encoding="utf-8"
            )

            # 5. matched_pairs.json
            pairs_data = [p.model_dump() for p in record.run_pairs]
            (cmp_dir / "matched_pairs.json").write_text(json.dumps(pairs_data, indent=2), encoding="utf-8")

            logger.info("Persisted differential comparison record: %s", cmp_id)
            return cmp_file
        except Exception as exc:
            raise ExperimentPersistenceError(str(cmp_dir), str(exc)) from exc

    def load_comparison(self, comparison_id: str) -> ComparisonRecord:
        """Load and validate master ComparisonRecord."""
        cmp_dir = self.get_comparison_dir(comparison_id)
        cmp_file = cmp_dir / "comparison.json"
        if not cmp_file.exists():
            raise ExperimentPersistenceError(
                str(cmp_file),
                f"Comparison record '{comparison_id}' does not exist.",
                suggestion="Run 'python -m hexnil diff list' to view available comparisons.",
            )
        try:
            content = cmp_file.read_text(encoding="utf-8")
            return ComparisonRecord.model_validate_json(content)
        except Exception as exc:
            raise ExperimentPersistenceError(str(cmp_file), f"Corrupted comparison JSON: {exc}") from exc

    def load_comparison_pairs(self, comparison_id: str) -> List[ComparisonRunPair]:
        """Load matched pairs from matched_pairs.json."""
        cmp_dir = self.get_comparison_dir(comparison_id)
        pairs_file = cmp_dir / "matched_pairs.json"
        if not pairs_file.exists():
            return []
        try:
            data = json.loads(pairs_file.read_text(encoding="utf-8"))
            return [ComparisonRunPair.model_validate(p) for p in data]
        except Exception as exc:
            logger.warning("Could not read matched pairs in %s: %s", pairs_file, exc)
            return []

    def load_comparison_quality(self, comparison_id: str) -> Optional[ComparisonQualityReport]:
        """Load quality report from quality.json."""
        cmp_dir = self.get_comparison_dir(comparison_id)
        q_file = cmp_dir / "quality.json"
        if not q_file.exists():
            return None
        try:
            return ComparisonQualityReport.model_validate_json(q_file.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("Could not read comparison quality in %s: %s", q_file, exc)
            return None

    def list_all(self) -> List[ComparisonRecord]:
        """List all valid comparisons sorted by ID descending."""
        records: List[ComparisonRecord] = []
        for d in self.comparisons_dir.glob("CMP-*"):
            if d.is_dir():
                cmp_file = d / "comparison.json"
                if cmp_file.is_file():
                    try:
                        records.append(ComparisonRecord.model_validate_json(cmp_file.read_text(encoding="utf-8")))
                    except Exception as exc:
                        logger.warning("Skipping invalid comparison in %s: %s", d.name, exc)
        records.sort(key=lambda r: r.comparison_id, reverse=True)
        return records
