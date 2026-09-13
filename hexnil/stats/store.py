"""Persistence and storage layer for Phase 6 statistical comparison evidence."""

import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from hexnil.exceptions import ExperimentPersistenceError
from hexnil.stats.models import (
    MetricComparison,
    StatisticalAnalysisRecord,
    StatisticalQualityReport,
)

logger = logging.getLogger("hexnil.stats.store")


class StatisticalAnalysisStore:
    """Manages persistence and retrieval of statistical comparison records under comparison directories."""

    def __init__(self, comparisons_base_dir: Path):
        self.comparisons_base_dir = comparisons_base_dir

    def get_analysis_dir(self, comparison_id: str) -> Path:
        """Get the statistical analysis subfolder for a comparison."""
        return self.comparisons_base_dir / comparison_id / "statistical_analysis"

    def has_analysis(self, comparison_id: str) -> bool:
        """Check if an analysis record exists for the given comparison ID."""
        analysis_file = self.get_analysis_dir(comparison_id) / "analysis.json"
        return analysis_file.exists() and analysis_file.is_file()

    def save_analysis(self, record: StatisticalAnalysisRecord) -> Path:
        """Persist master StatisticalAnalysisRecord and decomposed files."""
        analysis_dir = self.get_analysis_dir(record.comparison_id)
        analysis_dir.mkdir(parents=True, exist_ok=True)

        try:
            # 1. Master analysis.json
            analysis_file = analysis_dir / "analysis.json"
            analysis_file.write_text(record.model_dump_json(indent=2), encoding="utf-8")

            # 2. metric_results.json
            metrics_data = [m.model_dump() for m in record.metric_results]
            (analysis_dir / "metric_results.json").write_text(
                json.dumps(metrics_data, indent=2), encoding="utf-8"
            )

            # 3. exclusions.json
            (analysis_dir / "exclusions.json").write_text(
                json.dumps(record.exclusions, indent=2), encoding="utf-8"
            )

            # 4. configuration.json
            config_data = {
                "analysis_version": record.analysis_version,
                "threshold_version": record.threshold_version,
                "multiple_comparison_policy": record.multiple_comparison_policy,
                "random_seed": record.random_seed,
            }
            (analysis_dir / "configuration.json").write_text(
                json.dumps(config_data, indent=2), encoding="utf-8"
            )

            # 5. Calculate provenance and file integrity hashes
            provenance_hashes: Dict[str, str] = {}
            for target_name in ("analysis.json", "metric_results.json", "exclusions.json", "configuration.json"):
                fpath = analysis_dir / target_name
                if fpath.exists():
                    provenance_hashes[target_name] = hashlib.sha256(fpath.read_bytes()).hexdigest()

            prov_data = {
                "analysis_id": record.analysis_id,
                "comparison_id": record.comparison_id,
                "created_at": record.created_at,
                "file_hashes": provenance_hashes,
                "input_provenance": record.provenance,
            }
            (analysis_dir / "provenance.json").write_text(
                json.dumps(prov_data, indent=2), encoding="utf-8"
            )

            logger.info("Persisted statistical analysis for %s to %s", record.comparison_id, analysis_dir)
            return analysis_file

        except Exception as exc:
            raise ExperimentPersistenceError(str(analysis_dir), f"Failed to persist statistical analysis: {exc}") from exc

    def load_analysis(self, comparison_id: str) -> StatisticalAnalysisRecord:
        """Load and validate master StatisticalAnalysisRecord."""
        analysis_dir = self.get_analysis_dir(comparison_id)
        analysis_file = analysis_dir / "analysis.json"

        if not analysis_file.exists():
            raise ExperimentPersistenceError(
                str(analysis_file),
                f"Statistical analysis record does not exist for comparison '{comparison_id}'.",
                suggestion=f"Run 'python -m hexnil stats analyze {comparison_id}' to generate analysis.",
            )

        try:
            content = analysis_file.read_text(encoding="utf-8")
            return StatisticalAnalysisRecord.model_validate_json(content)
        except Exception as exc:
            raise ExperimentPersistenceError(str(analysis_file), f"Corrupted analysis JSON: {exc}") from exc

    def load_metric_results(self, comparison_id: str) -> List[MetricComparison]:
        """Load list of MetricComparison objects from metric_results.json."""
        analysis_dir = self.get_analysis_dir(comparison_id)
        results_file = analysis_dir / "metric_results.json"

        if not results_file.exists():
            return []

        try:
            content = results_file.read_text(encoding="utf-8")
            data = json.loads(content)
            return [MetricComparison.model_validate(m) for m in data]
        except Exception as exc:
            logger.warning("Could not parse metric results in %s: %s", results_file, exc)
            return []
