"""Persistence and store for Phase 8 AI Analyst explanations."""

import json
import logging
from pathlib import Path
from typing import Optional

from hexnil.explain.models import EvidenceExplanation

logger = logging.getLogger("hexnil.explain.store")


class ExplanationStore:
    """Manages reading and writing explanation artifacts under comparison directories."""

    def __init__(self, comparisons_dir: Path):
        self.comparisons_dir = comparisons_dir

    def get_explanation_dir(self, comparison_id: str) -> Path:
        """Return directory path for explanations associated with a comparison."""
        return self.comparisons_dir / comparison_id / "explanation"

    def get_explanation_file(self, comparison_id: str) -> Path:
        """Return file path for the master explanation record."""
        return self.get_explanation_dir(comparison_id) / "explanation.json"

    def has_explanation(self, comparison_id: str) -> bool:
        """Check whether an explanation file exists."""
        f = self.get_explanation_file(comparison_id)
        return f.is_file() and f.exists()

    def save_explanation(self, explanation: EvidenceExplanation) -> Path:
        """Persist an EvidenceExplanation record to disk."""
        exp_dir = self.get_explanation_dir(explanation.comparison_id)
        exp_dir.mkdir(parents=True, exist_ok=True)
        out_file = self.get_explanation_file(explanation.comparison_id)
        out_file.write_text(explanation.model_dump_json(indent=2), encoding="utf-8")
        logger.info("Persisted explanation '%s' to %s", explanation.explanation_id, out_file)
        return out_file

    def load_explanation(self, comparison_id: str) -> Optional[EvidenceExplanation]:
        """Load an EvidenceExplanation record from disk."""
        out_file = self.get_explanation_file(comparison_id)
        if not out_file.exists():
            return None
        try:
            data = json.loads(out_file.read_text(encoding="utf-8"))
            return EvidenceExplanation.model_validate(data)
        except Exception as exc:
            logger.warning("Failed to parse explanation file %s: %s", out_file, exc)
            return None
