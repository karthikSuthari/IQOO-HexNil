"""Master orchestrator for Phase 8 Evidence-Grounded AI Analyst."""

import datetime
import logging
from pathlib import Path
from typing import Optional

from hexnil.diff.models import ComparisonRecord
from hexnil.diff.store import ComparisonStore
from hexnil.exceptions import HexnilError
from hexnil.explain.cache import ExplanationCache
from hexnil.explain.client import GroqClient
from hexnil.explain.contract import build_evidence_package
from hexnil.explain.eligibility import validate_evidence_eligibility
from hexnil.explain.fallback import generate_deterministic_explanation
from hexnil.explain.models import (
    EvidenceEligibilityState,
    EvidenceExplanation,
    EvidencePackage,
    ExplanationSource,
)
from hexnil.explain.prompt import build_system_prompt, build_user_prompt
from hexnil.explain.store import ExplanationStore
from hexnil.explain.validator import validate_groq_response
from hexnil.predict.models import ValidationPlan
from hexnil.predict.store import PredictionStore
from hexnil.stats.models import StatisticalAnalysisRecord
from hexnil.stats.store import StatisticalAnalysisStore

logger = logging.getLogger("hexnil.explain.orchestrator")


class EvidenceExplanationOrchestrator:
    """Orchestrates structured evidence loading, eligibility gating, Groq inference, validation, and deterministic fallback."""

    def __init__(
        self,
        comparisons_dir: Path,
        predictions_dir: Optional[Path] = None,
        groq_client: Optional[GroqClient] = None,
    ):
        self.comparisons_dir = comparisons_dir
        self.predictions_dir = predictions_dir
        self.stats_store = StatisticalAnalysisStore(comparisons_dir)
        self.diff_store = ComparisonStore(comparisons_dir)
        self.pred_store = PredictionStore(predictions_dir) if predictions_dir else None
        self.exp_store = ExplanationStore(comparisons_dir)
        self.cache = ExplanationCache(self.exp_store)
        self.client = groq_client or GroqClient()

    def explain_comparison(
        self,
        comparison_id: str,
        offline: bool = False,
        use_cache: bool = True,
        model: Optional[str] = None,
    ) -> EvidenceExplanation:
        """Run the end-to-end evidence explanation pipeline for a given comparison ID."""
        # 1. Load Phase 6 Statistical Analysis
        if not self.stats_store.has_analysis(comparison_id):
            raise HexnilError(
                f"No statistical analysis found for comparison '{comparison_id}'.",
                suggestion=f"Run 'python -m hexnil stats analyze --comparison {comparison_id}' first."
            )

        analysis = self.stats_store.load_analysis(comparison_id)
        if not analysis:
            raise HexnilError(f"Failed to load statistical analysis record for '{comparison_id}'.")

        # 2. Load Phase 5 Comparison Record if available
        comparison_record: Optional[ComparisonRecord] = None
        try:
            comparison_record = self.diff_store.load_comparison(comparison_id)
        except Exception:
            logger.info("Comparison record for '%s' not loaded from store; proceeding with analysis record.", comparison_id)

        # 3. Load Phase 7 Validation Plan if available
        plan_record: Optional[ValidationPlan] = None
        if self.pred_store:
            try:
                # Attempt to find plan associated with comparison
                existing_plans = self.pred_store.list_plans()
                if existing_plans:
                    plan_record = self.pred_store.load_plan(existing_plans[0])
            except Exception:
                logger.info("Validation plan not found; proceeding with default registered claims.")

        # 4. Build Evidence Package
        package = build_evidence_package(analysis, comparison_record, plan_record)

        # 5. Validate Evidence Eligibility Gate
        is_eligible, state, reasons = validate_evidence_eligibility(package)
        if not is_eligible:
            logger.warning("Evidence package '%s' is %s: %s", comparison_id, state.value, "; ".join(reasons))
            # Fallback immediately explaining why evidence is insufficient or invalid
            return generate_deterministic_explanation(
                package,
                reason=f"Evidence eligibility check failed ({state.value}): {'; '.join(reasons)}",
                source=ExplanationSource.DETERMINISTIC_FALLBACK,
            )

        # 6. Check Cache
        if use_cache:
            cached = self.cache.get_cached(package)
            if cached:
                logger.info("Serving valid cached explanation for comparison '%s'", comparison_id)
                return cached

        # 7. Check Offline or Missing Key
        if offline or not self.client.has_valid_key():
            reason = "Offline mode explicitly requested" if offline else "Groq API key not present in environment"
            logger.info("Using deterministic analysis for '%s' (%s)", comparison_id, reason)
            explanation = generate_deterministic_explanation(
                package,
                reason=reason,
                source=ExplanationSource.DETERMINISTIC_ANALYSIS if offline else ExplanationSource.DETERMINISTIC_FALLBACK,
            )
            self.cache.put_cached(explanation)
            return explanation

        # 8. Online Groq Inference
        system_prompt = build_system_prompt()
        user_prompt = build_user_prompt(package)

        try:
            raw_response = self.client.complete(user_prompt, system_prompt, model=model)
            latency_ms = raw_response.get("_latency_ms", 0.0)
            actual_model = raw_response.get("_model", self.client.model)

            # 9. Response Validation against Ground Truth
            is_valid, errors, validated_data = validate_groq_response(raw_response, package)
            if not is_valid or not validated_data:
                logger.warning(
                    "Groq response failed validation against evidence package: %s. Falling back to deterministic analysis.",
                    "; ".join(errors),
                )
                explanation = generate_deterministic_explanation(
                    package,
                    reason=f"Groq response rejected by ground-truth validator: {'; '.join(errors)}",
                    source=ExplanationSource.DETERMINISTIC_FALLBACK,
                )
                self.cache.put_cached(explanation)
                return explanation

            # 10. Construct Verified Groq Explanation
            explanation = EvidenceExplanation(
                explanation_id=f"EXP-GROQ-{comparison_id}",
                comparison_id=comparison_id,
                source=ExplanationSource.GROQ_AI,
                model=actual_model,
                verdict=validated_data["verdict"],
                severity=validated_data["severity"],
                summary=validated_data["summary"],
                claim_assessment=validated_data["claim_assessment"],
                observed_changes=validated_data["observed_changes"],
                statistical_interpretation=validated_data["statistical_interpretation"],
                limitations=validated_data["limitations"],
                recommended_next_step=validated_data["recommended_next_step"],
                evidence_references=validated_data["evidence_references"],
                created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                latency_ms=latency_ms,
                is_cached=False,
                evidence_hash=package.evidence_hash,
            )
            self.cache.put_cached(explanation)
            return explanation

        except Exception as exc:
            # Safe catch: do not expose headers, tokens, or crash
            logger.warning("Groq inference encountered an error: %s. Falling back to deterministic explanation.", exc)
            explanation = generate_deterministic_explanation(
                package,
                reason=f"Groq inference error: {str(exc)}",
                source=ExplanationSource.DETERMINISTIC_FALLBACK,
            )
            self.cache.put_cached(explanation)
            return explanation
