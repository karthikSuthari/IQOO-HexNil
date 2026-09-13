"""Phase 7: Claim Intelligence & Pre-Update Prediction for Hexnil."""

from hexnil.predict.extractor import (
    PARSER_VERSION,
    ingest_raw_text,
    normalize_claim_text,
)
from hexnil.predict.mapping import (
    MAPPING_VERSION,
    detect_subsystem,
    extract_condition,
    map_metric_and_direction,
    structure_claim,
)
from hexnil.predict.models import (
    ClaimPrediction,
    ClaimSubsystem,
    ExtractionMethod,
    FeatureAvailability,
    MetricStatus,
    PredictionPath,
    PredictionQuality,
    PrioritizedWorkload,
    RawClaim,
    RiskBand,
    StructuredClaim,
    ValidationPlan,
    WorkloadRecommendation,
)
from hexnil.predict.planner import (
    build_evidence_linkage_schema,
    create_validation_plan,
    generate_plan_id,
)
from hexnil.predict.predictor import (
    PREDICTOR_VERSION,
    inspect_feature_availability,
    predict_claim_risk,
    score_to_risk_band,
    select_prediction_path,
)
from hexnil.predict.quality import audit_prediction_quality
from hexnil.predict.recommender import (
    RECOMMENDER_VERSION,
    prioritize_workloads,
    recommend_workloads_for_claim,
)
from hexnil.predict.store import PredictionStore

__all__ = [
    # Constants
    "PARSER_VERSION",
    "MAPPING_VERSION",
    "PREDICTOR_VERSION",
    "RECOMMENDER_VERSION",
    # Models
    "RawClaim",
    "StructuredClaim",
    "ExtractionMethod",
    "ClaimSubsystem",
    "MetricStatus",
    "PredictionPath",
    "RiskBand",
    "FeatureAvailability",
    "WorkloadRecommendation",
    "ClaimPrediction",
    "PrioritizedWorkload",
    "ValidationPlan",
    "PredictionQuality",
    # Functions
    "ingest_raw_text",
    "normalize_claim_text",
    "detect_subsystem",
    "extract_condition",
    "map_metric_and_direction",
    "structure_claim",
    "inspect_feature_availability",
    "select_prediction_path",
    "predict_claim_risk",
    "score_to_risk_band",
    "recommend_workloads_for_claim",
    "prioritize_workloads",
    "create_validation_plan",
    "generate_plan_id",
    "build_evidence_linkage_schema",
    "audit_prediction_quality",
    "PredictionStore",
]
