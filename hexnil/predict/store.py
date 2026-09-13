"""Persistence and storage layer for Phase 7 prediction artifacts."""

import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from hexnil.exceptions import ExperimentPersistenceError
from hexnil.predict.models import PredictionQuality, ValidationPlan
from hexnil.predict.quality import audit_prediction_quality

logger = logging.getLogger("hexnil.predict.store")


class PredictionStore:
    """Manages persistence and retrieval of pre-update prediction plans and artifacts."""

    def __init__(self, predictions_base_dir: Path):
        self.predictions_base_dir = Path(predictions_base_dir)

    def get_plan_dir(self, plan_id: str) -> Path:
        """Get the storage directory for a specific validation plan."""
        return self.predictions_base_dir / plan_id

    def has_plan(self, plan_id: str) -> bool:
        """Check if a validation plan exists."""
        plan_file = self.get_plan_dir(plan_id) / "validation_plan.json"
        return plan_file.exists() and plan_file.is_file()

    def list_plans(self) -> List[str]:
        """List all persisted plan IDs in sorted order."""
        if not self.predictions_base_dir.exists() or not self.predictions_base_dir.is_dir():
            return []

        plans: List[str] = []
        for item in self.predictions_base_dir.iterdir():
            if item.is_dir() and (item / "validation_plan.json").exists():
                plans.append(item.name)
        return sorted(plans)

    def save_plan(
        self,
        plan: ValidationPlan,
        quality: Optional[PredictionQuality] = None,
    ) -> Path:
        """Persist master validation plan and decomposed files."""
        plan_dir = self.get_plan_dir(plan.plan_id)
        plan_dir.mkdir(parents=True, exist_ok=True)

        if quality is None:
            quality = audit_prediction_quality(plan)

        try:
            # 1. input.json
            input_data = {
                "plan_id": plan.plan_id,
                "raw_text": plan.source_release_notes_raw,
                "raw_text_hash": plan.source_release_notes_hash,
                "created_at": plan.created_at,
            }
            (plan_dir / "input.json").write_text(
                json.dumps(input_data, indent=2), encoding="utf-8"
            )

            # 2. claims.json
            claims_data = [c.model_dump() for c in plan.claims]
            (plan_dir / "claims.json").write_text(
                json.dumps(claims_data, indent=2), encoding="utf-8"
            )

            # 3. predictions.json
            pred_data = {
                "predictions": [p.model_dump() for p in plan.predictions],
                "prioritized_workloads": [pw.model_dump() for pw in plan.prioritized_workloads],
                "overall_risk_score": plan.overall_risk_score,
                "overall_risk_band": plan.overall_risk_band.value,
                "overall_path": plan.overall_path.value,
            }
            (plan_dir / "predictions.json").write_text(
                json.dumps(pred_data, indent=2), encoding="utf-8"
            )

            # 4. quality.json
            (plan_dir / "quality.json").write_text(
                quality.model_dump_json(indent=2), encoding="utf-8"
            )

            # 5. validation_plan.json (master document)
            master_plan_file = plan_dir / "validation_plan.json"
            master_plan_file.write_text(
                plan.model_dump_json(indent=2), encoding="utf-8"
            )

            # 6. provenance.json with file-level SHA-256 hashes
            file_hashes: Dict[str, str] = {}
            for fname in ("input.json", "claims.json", "predictions.json", "quality.json", "validation_plan.json"):
                fpath = plan_dir / fname
                if fpath.exists():
                    file_hashes[fname] = hashlib.sha256(fpath.read_bytes()).hexdigest()

            prov_data = {
                "plan_id": plan.plan_id,
                "created_at": plan.created_at,
                "file_hashes": file_hashes,
                "model_versions": plan.model_versions,
                "provenance": plan.provenance,
            }
            (plan_dir / "provenance.json").write_text(
                json.dumps(prov_data, indent=2), encoding="utf-8"
            )

            logger.info("Persisted validation plan %s to %s", plan.plan_id, plan_dir)
            return master_plan_file

        except Exception as exc:
            raise ExperimentPersistenceError(
                str(plan_dir),
                f"Failed to persist validation plan: {exc}",
            ) from exc

    def load_plan(self, plan_id: str) -> ValidationPlan:
        """Load and deserialize master ValidationPlan."""
        plan_dir = self.get_plan_dir(plan_id)
        plan_file = plan_dir / "validation_plan.json"

        if not plan_file.exists():
            raise ExperimentPersistenceError(
                str(plan_file),
                f"Validation plan '{plan_id}' does not exist.",
                suggestion=f"Run 'python -m hexnil predict analyze <INPUT>' to generate a plan.",
            )

        try:
            content = plan_file.read_text(encoding="utf-8")
            data = json.loads(content)
            return ValidationPlan.model_validate(data)
        except Exception as exc:
            raise ExperimentPersistenceError(
                str(plan_file),
                f"Failed to load validation plan '{plan_id}': {exc}",
            ) from exc

    def load_quality(self, plan_id: str) -> Optional[PredictionQuality]:
        """Load PredictionQuality report for a plan."""
        plan_dir = self.get_plan_dir(plan_id)
        quality_file = plan_dir / "quality.json"

        if not quality_file.exists():
            return None

        try:
            content = quality_file.read_text(encoding="utf-8")
            data = json.loads(content)
            return PredictionQuality.model_validate(data)
        except Exception:
            return None
