"""Validation plan generator and pre-update orchestrator for Phase 7."""

import datetime
import hashlib
from typing import Any, Dict, List, Optional

from hexnil.predict.extractor import PARSER_VERSION, ingest_raw_text, normalize_claim_text
from hexnil.predict.mapping import MAPPING_VERSION, structure_claim
from hexnil.predict.models import (
    ClaimPrediction,
    FeatureAvailability,
    PredictionPath,
    PrioritizedWorkload,
    RiskBand,
    StructuredClaim,
    ValidationPlan,
)
from hexnil.predict.predictor import (
    PREDICTOR_VERSION,
    inspect_feature_availability,
    predict_claim_risk,
    score_to_risk_band,
    select_prediction_path,
)
from hexnil.predict.recommender import (
    RECOMMENDER_VERSION,
    prioritize_workloads,
    recommend_workloads_for_claim,
)


def generate_plan_id(plan_number: int = 1) -> str:
    """Generate deterministic plan ID adhering to PLAN-YYYYMMDD-XXX convention."""
    today_str = datetime.date.today().strftime("%Y%m%d")
    return f"PLAN-{today_str}-{plan_number:03d}"


def build_evidence_linkage_schema(
    claims: List[StructuredClaim],
    predictions: List[ClaimPrediction],
    prioritized_workloads: List[PrioritizedWorkload],
) -> Dict[str, Any]:
    """Construct structured linkage schema connecting claims to future validation evidence.

    Schema:
      claim -> predicted_risk -> recommended_workload -> v0_baseline_metric -> v1_measurement -> phase_6_verdict
    """
    pred_map = {p.claim_id: p for p in predictions}
    workload_map = {pw.workload_id: pw for pw in prioritized_workloads}

    linkages: List[Dict[str, Any]] = []

    for claim in claims:
        pred = pred_map.get(claim.claim_id)
        risk_score = pred.raw_risk_score if pred else 0.0
        risk_band = pred.risk_band.value if pred else "UNKNOWN"

        recs = pred.recommendations if pred else []
        for rec in recs:
            pw = workload_map.get(rec.workload_id)
            linkage = {
                "claim_id": claim.claim_id,
                "claim_text": claim.normalized_text,
                "subsystem": claim.subsystem,
                "predicted_risk_score": risk_score,
                "predicted_risk_band": risk_band,
                "recommended_workload_id": rec.workload_id,
                "priority_rank": pw.priority_rank if pw else 99,
                "target_metric": claim.metric,
                "metric_status": claim.metric_status.value,
                "expected_direction": claim.expected_direction.value,
                # Placeholders for future phases (Phase 4/5/6); NEVER fabricated in Phase 7
                "v0_baseline_experiment_id": None,
                "v0_baseline_metric_value": None,
                "v1_target_experiment_id": None,
                "v1_target_metric_value": None,
                "phase_6_verdict": None,
                "status": "AWAITING_MEASUREMENT",
            }
            linkages.append(linkage)

    return {
        "schema_version": "1.0.0",
        "description": "Pre-update claim-to-evidence linkage schema connecting predictions to empirical Phase 5/6 verdicts.",
        "linkages": linkages,
    }


def create_validation_plan(
    raw_release_notes: str,
    plan_id: Optional[str] = None,
    code_changes: Optional[Dict[str, Any]] = None,
    history_available: bool = False,
    source: str = "release_notes",
) -> ValidationPlan:
    """Ingest release notes and orchestrate complete pre-update validation planning."""
    created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    raw_text = raw_release_notes or ""
    text_hash = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()

    # 1. Ingestion & Extraction
    raw_claim_items = ingest_raw_text(raw_text, source=source)
    claims: List[StructuredClaim] = []
    for idx, raw_item in enumerate(raw_claim_items, start=1):
        norm_text = normalize_claim_text(raw_item.raw_text)
        if norm_text:
            claims.append(
                structure_claim(
                    raw_text=raw_item.raw_text,
                    normalized_text=norm_text,
                    claim_index=idx,
                    source=source,
                )
            )

    # 2. Feature Availability Inspection
    features = inspect_feature_availability(
        claims=claims,
        code_changes=code_changes,
        history_available=history_available,
    )
    overall_path = select_prediction_path(features)

    # 3. Risk Prediction & Workload Recommendation
    predictions: List[ClaimPrediction] = []
    for claim in claims:
        pred = predict_claim_risk(
            claim=claim,
            features=features,
            code_changes=code_changes,
        )
        # Map recommendations
        recs = recommend_workloads_for_claim(claim)
        pred.recommendations = recs
        predictions.append(pred)

    # 4. Deterministic Workload Prioritization
    prioritized = prioritize_workloads(claims, predictions)

    # 5. Overall Risk Calculation
    if predictions:
        overall_score = round(max(p.raw_risk_score for p in predictions), 4)
    else:
        overall_score = 0.0
    overall_band = score_to_risk_band(overall_score)

    # 6. Evidence Linkage Schema
    linkage_schema = build_evidence_linkage_schema(claims, predictions, prioritized)

    resolved_plan_id = plan_id or generate_plan_id()

    provenance = {
        "plan_id": resolved_plan_id,
        "created_at": created_at,
        "source_release_notes_hash": text_hash,
        "claims_count": len(claims),
        "predictions_count": len(predictions),
        "prioritized_workloads_count": len(prioritized),
        "code_changes_supplied": bool(code_changes),
        "history_available": history_available,
    }

    model_versions = {
        "parser_version": PARSER_VERSION,
        "mapping_version": MAPPING_VERSION,
        "predictor_version": PREDICTOR_VERSION,
        "recommender_version": RECOMMENDER_VERSION,
    }

    return ValidationPlan(
        plan_id=resolved_plan_id,
        phase="07_claim_intelligence_prediction",
        created_at=created_at,
        source_release_notes_raw=raw_text,
        source_release_notes_hash=text_hash,
        claims=claims,
        predictions=predictions,
        prioritized_workloads=prioritized,
        model_versions=model_versions,
        feature_availability=features,
        overall_risk_score=overall_score,
        overall_risk_band=overall_band,
        overall_path=overall_path,
        evidence_linkage_schema=linkage_schema,
        provenance=provenance,
    )
