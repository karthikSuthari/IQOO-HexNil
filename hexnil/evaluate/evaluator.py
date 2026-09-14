"""Prediction accuracy evaluator: compares Phase 7 predictions to Phase 6 actual outcomes."""

import datetime
import logging
from typing import Dict, List, Optional, Set, Tuple

from hexnil.evaluate.models import (
    PredictionEvaluationReport,
    PredictionHit,
    PredictionOutcome,
)
from hexnil.predict.models import (
    ClaimPrediction,
    RiskBand,
    StructuredClaim,
    ValidationPlan,
)
from hexnil.stats.models import (
    MetricComparison,
    Severity,
    StatisticalAnalysisRecord,
    Verdict,
)

logger = logging.getLogger("hexnil.evaluate.evaluator")

# Risk bands considered "predicted risk" for binary classification
HIGH_RISK_BANDS: Set[str] = {RiskBand.HIGH.value, RiskBand.CRITICAL.value}
LOW_RISK_BANDS: Set[str] = {RiskBand.LOW.value, RiskBand.MODERATE.value}

# Verdicts considered "actual change" for binary classification
ACTUAL_CHANGE_VERDICTS: Set[str] = {Verdict.REGRESSION.value, Verdict.IMPROVEMENT.value}
ACTUAL_UNCHANGED_VERDICTS: Set[str] = {Verdict.UNCHANGED.value}


class PredictionEvaluator:
    """Evaluates ML prediction accuracy by comparing pre-update predictions to actual outcomes."""

    def evaluate(
        self,
        session_id: str,
        comparison_id: str,
        plan: ValidationPlan,
        analysis: StatisticalAnalysisRecord,
    ) -> PredictionEvaluationReport:
        """Evaluate all predictions from the validation plan against analysis results."""
        # Build metric lookup from analysis
        metric_by_key: Dict[str, MetricComparison] = {}
        for m in analysis.metric_results:
            key = f"{m.workload_id}:{m.metric_name}"
            metric_by_key[key] = m

        # Build claim lookup
        claim_by_id: Dict[str, StructuredClaim] = {c.claim_id: c for c in plan.claims}

        outcomes: List[PredictionOutcome] = []

        for prediction in plan.predictions:
            claim = claim_by_id.get(prediction.claim_id)
            if not claim:
                continue

            # Find the actual metric result corresponding to this claim
            actual_metric = self._find_matching_metric(claim, metric_by_key)
            actual_verdict: Optional[str] = None
            actual_severity: Optional[str] = None

            if actual_metric:
                actual_verdict = actual_metric.verdict.value
                actual_severity = actual_metric.severity.value

            # Classify hit/miss
            hit = self._classify_hit(
                predicted_risk_band=prediction.risk_band.value,
                actual_verdict=actual_verdict,
            )

            explanation = self._build_explanation(
                prediction=prediction,
                claim=claim,
                actual_verdict=actual_verdict,
                actual_severity=actual_severity,
                hit=hit,
            )

            outcome = PredictionOutcome(
                claim_id=prediction.claim_id,
                claim_text=claim.raw_text,
                subsystem=claim.subsystem,
                predicted_risk_band=prediction.risk_band.value,
                predicted_risk_score=prediction.raw_risk_score,
                prediction_path=prediction.prediction_path.value,
                actual_verdict=actual_verdict,
                actual_severity=actual_severity,
                hit_classification=hit,
                explanation=explanation,
            )
            outcomes.append(outcome)

        # Compute aggregate metrics
        total = len(outcomes)
        tp = sum(1 for o in outcomes if o.hit_classification == PredictionHit.TRUE_POSITIVE)
        tn = sum(1 for o in outcomes if o.hit_classification == PredictionHit.TRUE_NEGATIVE)
        fp = sum(1 for o in outcomes if o.hit_classification == PredictionHit.FALSE_POSITIVE)
        fn = sum(1 for o in outcomes if o.hit_classification == PredictionHit.FALSE_NEGATIVE)
        uneval = sum(1 for o in outcomes if o.hit_classification == PredictionHit.UNEVALUATED)
        evaluated = tp + tn + fp + fn

        accuracy = round((tp + tn) / evaluated, 3) if evaluated > 0 else None
        precision = round(tp / (tp + fp), 3) if (tp + fp) > 0 else None
        recall = round(tp / (tp + fn), 3) if (tp + fn) > 0 else None
        f1 = (
            round(2 * (precision * recall) / (precision + recall), 3)
            if precision and recall and (precision + recall) > 0
            else None
        )

        overall = self._build_overall_assessment(
            tp=tp, tn=tn, fp=fp, fn=fn, uneval=uneval, accuracy=accuracy
        )

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        return PredictionEvaluationReport(
            session_id=session_id,
            comparison_id=comparison_id,
            plan_id=plan.plan_id,
            outcomes=outcomes,
            total_predictions=total,
            evaluated_predictions=evaluated,
            true_positives=tp,
            true_negatives=tn,
            false_positives=fp,
            false_negatives=fn,
            unevaluated=uneval,
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1,
            overall_assessment=overall,
            created_at=now_iso,
        )

    def _find_matching_metric(
        self,
        claim: StructuredClaim,
        metric_by_key: Dict[str, MetricComparison],
    ) -> Optional[MetricComparison]:
        """Find the metric result that best matches a claim's target metric."""
        # Direct metric match across all workloads
        for key, metric in metric_by_key.items():
            if metric.metric_name == claim.metric:
                return metric

        # Fuzzy subsystem-level match
        subsystem_workload_map = {
            "battery": "video_power_01",
            "startup/performance": "startup_01",
            "memory": "memory_01",
            "ui/frame performance": "scroll_01",
            "cpu/performance": "cpu_01",
            "thermal": "cpu_01",
        }
        target_workload = subsystem_workload_map.get(claim.subsystem)
        if target_workload:
            for key, metric in metric_by_key.items():
                if metric.workload_id == target_workload:
                    return metric

        return None

    def _classify_hit(
        self,
        predicted_risk_band: str,
        actual_verdict: Optional[str],
    ) -> PredictionHit:
        """Classify whether the prediction was correct."""
        if actual_verdict is None:
            return PredictionHit.UNEVALUATED

        predicted_risk = predicted_risk_band in HIGH_RISK_BANDS
        actual_change = actual_verdict in ACTUAL_CHANGE_VERDICTS

        if predicted_risk and actual_change:
            return PredictionHit.TRUE_POSITIVE
        elif not predicted_risk and not actual_change:
            return PredictionHit.TRUE_NEGATIVE
        elif predicted_risk and not actual_change:
            return PredictionHit.FALSE_POSITIVE
        elif not predicted_risk and actual_change:
            return PredictionHit.FALSE_NEGATIVE

        return PredictionHit.UNEVALUATED

    def _build_explanation(
        self,
        prediction: ClaimPrediction,
        claim: StructuredClaim,
        actual_verdict: Optional[str],
        actual_severity: Optional[str],
        hit: PredictionHit,
    ) -> str:
        """Build a human-readable explanation for the prediction outcome."""
        if hit == PredictionHit.UNEVALUATED:
            return (
                f"Claim '{claim.claim_id}' prediction ({prediction.risk_band.value}) "
                f"could not be evaluated: no matching metric outcome found."
            )

        verb = {
            PredictionHit.TRUE_POSITIVE: "CORRECTLY predicted risk",
            PredictionHit.TRUE_NEGATIVE: "CORRECTLY predicted stability",
            PredictionHit.FALSE_POSITIVE: "INCORRECTLY predicted risk (false alarm)",
            PredictionHit.FALSE_NEGATIVE: "MISSED actual change (blind spot)",
        }.get(hit, "evaluated")

        return (
            f"Claim '{claim.claim_id}' ({claim.subsystem}): {verb}. "
            f"Predicted: {prediction.risk_band.value} (score={prediction.raw_risk_score:.2f}), "
            f"Actual: {actual_verdict} (severity={actual_severity or 'N/A'})."
        )

    def _build_overall_assessment(
        self,
        tp: int,
        tn: int,
        fp: int,
        fn: int,
        uneval: int,
        accuracy: Optional[float],
    ) -> str:
        """Build the overall prediction evaluation assessment."""
        parts: List[str] = []
        evaluated = tp + tn + fp + fn

        if evaluated == 0:
            return "No predictions could be evaluated against actual outcomes."

        if accuracy is not None:
            parts.append(f"Prediction accuracy: {accuracy:.1%} ({tp + tn}/{evaluated} correct).")

        if fp > 0:
            parts.append(f"{fp} false positive(s) — predicted risk that did not materialize.")
        if fn > 0:
            parts.append(f"{fn} false negative(s) — actual changes the model missed.")
        if uneval > 0:
            parts.append(f"{uneval} prediction(s) could not be evaluated.")

        return " ".join(parts)
