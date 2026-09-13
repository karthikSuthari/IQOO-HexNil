"""Deterministic and unique experiment/session ID generation."""

import datetime
import re
from pathlib import Path
from typing import Optional, Set

ID_PATTERN = re.compile(r"^EXP-(\d{8})-(\d{3,})$")


def get_existing_ids(store_dir: Path) -> Set[str]:
    """Retrieve all existing experiment IDs stored in the directory."""
    if not store_dir.exists():
        return set()
    ids = set()
    # Check flat JSON files
    for item in store_dir.glob("EXP-*.json"):
        exp_id = item.stem
        if ID_PATTERN.match(exp_id):
            ids.add(exp_id)
    # Check directory-based experiments
    for item in store_dir.glob("EXP-*"):
        if item.is_dir() and ID_PATTERN.match(item.name):
            ids.add(item.name)
    return ids


def generate_experiment_id(
    store_dir: Path,
    target_date: Optional[datetime.date] = None,
) -> str:
    """Generate a unique deterministic experiment ID: EXP-YYYYMMDD-001.

    If records for the target date already exist in store_dir, increments
    the sequence number (e.g. 002, 003).
    """
    date_obj = target_date or datetime.date.today()
    date_str = date_obj.strftime("%Y%m%d")

    existing_ids = get_existing_ids(store_dir)
    highest_seq = 0

    for exp_id in existing_ids:
        match = ID_PATTERN.match(exp_id)
        if match:
            item_date, seq_str = match.groups()
            if item_date == date_str:
                seq = int(seq_str)
                if seq > highest_seq:
                    highest_seq = seq

    new_seq = highest_seq + 1
    return f"EXP-{date_str}-{new_seq:03d}"
