"""Comprehensive unit and integration test suite for Phase 7: Claim Intelligence & Pre-Update Prediction."""

import json
import pytest
from pathlib import Path

from hexnil.config import HexnilConfig
from hexnil.exceptions import ExperimentPersistenceError
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
from hexnil.stats.models import MetricDirection


# ==============================================================================
# 1. INGESTION & EXTRACTION TESTS
# ==============================================================================

def test_ingest_raw_text_bullets():
    raw = (
        "- Faster cold app startup and reduced splash duration\n"
        "* Improved battery efficiency during background video streaming\n"
        "+ Reduced heap memory usage to prevent jank\n"
        "1. Smooth 60fps scrolling in product catalogue\n"
    )
    claims = ingest_raw_text(raw)
    assert len(claims) == 4
    # Ensure original raw text is preserved
    assert claims[0].raw_text == "- Faster cold app startup and reduced splash duration"
    assert claims[1].raw_text == "* Improved battery efficiency during background video streaming"
    assert claims[2].raw_text == "+ Reduced heap memory usage to prevent jank"
    assert claims[3].raw_text == "1. Smooth 60fps scrolling in product catalogue"


def test_ingest_raw_text_paragraphs():
    raw = (
        "This update features enhanced battery optimization for continuous video playback.\n\n"
        "We also worked on app launch responsiveness for faster startup."
    )
    claims = ingest_raw_text(raw)
    assert len(claims) == 2
    assert "battery" in claims[0].raw_text
    assert "startup" in claims[1].raw_text


def test_ingest_raw_text_empty_and_whitespace():
    assert ingest_raw_text("") == []
    assert ingest_raw_text("   \n\n\t  ") == []


def test_normalize_claim_text():
    bullet = "   -   Faster cold startup latency and responsiveness.   "
    normalized = normalize_claim_text(bullet)
    assert normalized == "Faster cold startup latency and responsiveness."

    numbered = "12. Reduced heap memory allocations during image loading."
    assert normalize_claim_text(numbered) == "Reduced heap memory allocations during image loading."


# ==============================================================================
# 2. MAPPING TESTS (SUBSYSTEM, METRIC, DIRECTION, CONDITION)
# ==============================================================================

def test_subsystem_detection():
    sub, conf = detect_subsystem("Improved battery efficiency and reduced power drain")
    assert sub == ClaimSubsystem.BATTERY
    assert conf >= 0.85

    sub, conf = detect_subsystem("Faster cold startup time on initial app launch")
    assert sub == ClaimSubsystem.STARTUP
    assert conf >= 0.85

    sub, conf = detect_subsystem("Reduced heap memory allocation and fewer OOM occurrences")
    assert sub == ClaimSubsystem.MEMORY
    assert conf >= 0.85

    sub, conf = detect_subsystem("Eliminated jank and dropped frames during 120fps scrolling")
    assert sub == ClaimSubsystem.UI_PERFORMANCE
    assert conf >= 0.85

    sub, conf = detect_subsystem("Optimized CPU compute and reduced thread contention")
    assert sub == ClaimSubsystem.CPU_PERFORMANCE
    assert conf >= 0.85

    sub, conf = detect_subsystem("Fixed NullPointerException crash when rotating device")
    assert sub == ClaimSubsystem.STABILITY
    assert conf >= 0.85

    sub, conf = detect_subsystem("Lower skin temperature and improved thermal dissipation")
    assert sub == ClaimSubsystem.THERMAL
    assert conf >= 0.85

    sub, conf = detect_subsystem("Magical revolutionary experience with unbelievable delights")
    assert sub == ClaimSubsystem.UNKNOWN
    assert conf <= 0.30


def test_metric_and_direction_mapping():
    # Battery -> battery_discharge_proxy (LOWER_IS_BETTER)
    metric, status, direction, _ = map_metric_and_direction(
        ClaimSubsystem.BATTERY, "improved battery life and reduced power consumption"
    )
    assert metric == "battery_discharge_proxy"
    assert status == MetricStatus.SUPPORTED
    assert direction == MetricDirection.LOWER_IS_BETTER

    # Startup -> startup_duration_ms (LOWER_IS_BETTER)
    metric, status, direction, _ = map_metric_and_direction(
        ClaimSubsystem.STARTUP, "faster cold launch"
    )
    assert metric == "startup_duration_ms"
    assert status == MetricStatus.SUPPORTED
    assert direction == MetricDirection.LOWER_IS_BETTER

    # Memory allocated -> app_heap_allocated_mb (LOWER_IS_BETTER)
    metric, status, direction, _ = map_metric_and_direction(
        ClaimSubsystem.MEMORY, "reduced heap memory footprint"
    )
    assert metric == "app_heap_allocated_mb"
    assert status == MetricStatus.SUPPORTED
    assert direction == MetricDirection.LOWER_IS_BETTER

    # Memory available RAM -> device_memory_available_mb (HIGHER_IS_BETTER)
    metric, status, direction, _ = map_metric_and_direction(
        ClaimSubsystem.MEMORY, "more available RAM for multitasking"
    )
    assert metric == "device_memory_available_mb"
    assert status == MetricStatus.SUPPORTED
    assert direction == MetricDirection.HIGHER_IS_BETTER

    # UI Jank -> ui_frame_jank_percent (LOWER_IS_BETTER)
    metric, status, direction, _ = map_metric_and_direction(
        ClaimSubsystem.UI_PERFORMANCE, "reduced frame jank during fast scrolling"
    )
    assert metric == "ui_frame_jank_percent"
    assert status == MetricStatus.SUPPORTED
    assert direction == MetricDirection.LOWER_IS_BETTER

    # CPU compute -> compute_duration_ms (LOWER_IS_BETTER)
    metric, status, direction, _ = map_metric_and_direction(
        ClaimSubsystem.CPU_PERFORMANCE, "faster processing calculation"
    )
    assert metric == "compute_duration_ms"
    assert status == MetricStatus.SUPPORTED
    assert direction == MetricDirection.LOWER_IS_BETTER

    # Unsupported subsystem (e.g. thermal or camera) -> UNSUPPORTED metric
    metric, status, direction, _ = map_metric_and_direction(
        ClaimSubsystem.THERMAL, "lowered skin temperature"
    )
    assert metric == "UNSUPPORTED"
    assert status == MetricStatus.UNSUPPORTED
    assert direction == MetricDirection.UNKNOWN


def test_structure_claim_integrity():
    raw = "   * Faster cold startup latency and eliminated splash delay   "
    norm = normalize_claim_text(raw)
    claim = structure_claim(raw, norm, 1)

    assert claim.claim_id == "CLM-001"
    assert claim.raw_text == raw
    assert claim.normalized_text == norm
    assert claim.subsystem == "startup/performance"
    assert claim.metric == "startup_duration_ms"
    assert claim.metric_status == MetricStatus.SUPPORTED
    assert claim.expected_direction == MetricDirection.LOWER_IS_BETTER
    assert claim.confidence >= 0.85
    assert claim.extraction_method == ExtractionMethod.RULE_BASED


# ==============================================================================
# 3. FEATURE AVAILABILITY & PREDICTION PATH TESTS
# ==============================================================================

def test_feature_availability_release_notes_only():
    claim = structure_claim("Faster startup", "Faster startup", 1)
    features = inspect_feature_availability([claim], code_changes=None)

    assert features.has_claim_text is True
    assert features.has_subsystem is True
    assert features.has_metric is True
    assert features.has_expected_direction is True
    assert features.has_code_change_features is False
    assert "code_change_ast_metrics" in features.missing_features

    # Release notes alone MUST select Path B
    path = select_prediction_path(features)
    assert path == PredictionPath.PATH_B_CLAIM_HISTORY


def test_feature_availability_with_code_changes():
    claim = structure_claim("Faster startup", "Faster startup", 1)
    code_churn = {
        "delta_loc": 500,
        "delta_nom": 20,
        "delta_noc": 4,
        "delta_wmc": 85.0,
        "delta_cbo": 0.02,
        "delta_bad_smells": 1,
    }
    features = inspect_feature_availability([claim], code_changes=code_churn)
    assert features.has_code_change_features is True

    # When code changes are genuinely supplied, select Path A
    path = select_prediction_path(features)
    assert path == PredictionPath.PATH_A_CODE_CHANGE


def test_feature_availability_empty_claims():
    features = inspect_feature_availability([], code_changes=None)
    assert features.has_claim_text is False
    path = select_prediction_path(features)
    assert path == PredictionPath.PATH_C_INSUFFICIENT_EVIDENCE


# ==============================================================================
# 4. RISK SCORING & BAND BOUNDS TESTS
# ==============================================================================

def test_score_to_risk_band():
    assert score_to_risk_band(0.0) == RiskBand.LOW
    assert score_to_risk_band(0.199) == RiskBand.LOW
    assert score_to_risk_band(0.20) == RiskBand.MODERATE
    assert score_to_risk_band(0.499) == RiskBand.MODERATE
    assert score_to_risk_band(0.50) == RiskBand.HIGH
    assert score_to_risk_band(0.799) == RiskBand.HIGH
    assert score_to_risk_band(0.80) == RiskBand.CRITICAL
    assert score_to_risk_band(1.0) == RiskBand.CRITICAL
    # Clamping
    assert score_to_risk_band(-0.5) == RiskBand.LOW
    assert score_to_risk_band(1.5) == RiskBand.CRITICAL


def test_predict_claim_risk_path_b():
    claim = structure_claim(
        "Improved battery efficiency during continuous background video playback",
        "Improved battery efficiency during continuous background video playback",
        1,
    )
    features = inspect_feature_availability([claim], code_changes=None)
    pred = predict_claim_risk(claim, features)

    assert pred.prediction_path == PredictionPath.PATH_B_CLAIM_HISTORY
    assert 0.0 <= pred.raw_risk_score <= 1.0
    # Battery has high mobile variance prior (0.65 baseline)
    assert pred.risk_band in (RiskBand.HIGH, RiskBand.MODERATE)
    assert len(pred.explanation) >= 3


def test_predict_claim_risk_path_a_evaluation():
    claim = structure_claim("Refactored background service", "Refactored background service", 1)
    code_churn = {
        "delta_loc": 25000,
        "delta_nom": 2000,
        "delta_noc": 300,
        "delta_wmc": 10000.0,
        "delta_cbo": 0.05,
        "delta_bad_smells": 10,
    }
    features = inspect_feature_availability([claim], code_changes=code_churn)
    pred = predict_claim_risk(claim, features, code_changes=code_churn)

    assert pred.prediction_path == PredictionPath.PATH_A_CODE_CHANGE
    assert pred.model_name == "RandomForestCodeRiskClassifier"
    assert 0.0 <= pred.raw_risk_score <= 1.0
    assert pred.risk_band == RiskBand.CRITICAL or pred.risk_band == RiskBand.HIGH


# ==============================================================================
# 5. WORKLOAD RECOMMENDATION & DETERMINISTIC PRIORITIZATION
# ==============================================================================

def test_recommend_workloads():
    # Battery claim -> video_power_01
    claim_bat = structure_claim("Improved battery life", "Improved battery life", 1)
    recs_bat = recommend_workloads_for_claim(claim_bat)
    assert len(recs_bat) == 1
    assert recs_bat[0].workload_id == "video_power_01"
    assert "battery_discharge_proxy" in recs_bat[0].required_metrics

    # Startup claim -> startup_01
    claim_start = structure_claim("Faster startup", "Faster startup", 2)
    recs_start = recommend_workloads_for_claim(claim_start)
    assert len(recs_start) == 1
    assert recs_start[0].workload_id == "startup_01"
    assert "startup_duration_ms" in recs_start[0].required_metrics

    # Memory claim -> memory_01
    claim_mem = structure_claim("Reduced memory usage", "Reduced memory usage", 3)
    recs_mem = recommend_workloads_for_claim(claim_mem)
    assert len(recs_mem) == 1
    assert recs_mem[0].workload_id == "memory_01"

    # UI frame claim -> scroll_01
    claim_ui = structure_claim("Smoother scrolling without jank", "Smoother scrolling without jank", 4)
    recs_ui = recommend_workloads_for_claim(claim_ui)
    assert len(recs_ui) == 1
    assert recs_ui[0].workload_id == "scroll_01"


def test_deterministic_prioritization():
    raw = (
        "- Faster cold app startup\n"
        "- Improved battery life during video streaming\n"
        "- Reduced heap memory allocations\n"
    )
    plan1 = create_validation_plan(raw, plan_id="PLAN-DET-001")
    plan2 = create_validation_plan(raw, plan_id="PLAN-DET-002")

    # Verify identical ordering and priority scores
    w1 = [pw.workload_id for pw in plan1.prioritized_workloads]
    w2 = [pw.workload_id for pw in plan2.prioritized_workloads]
    assert w1 == w2

    s1 = [pw.priority_score for pw in plan1.prioritized_workloads]
    s2 = [pw.priority_score for pw in plan2.prioritized_workloads]
    assert s1 == s2

    # Verify ranks are sequential
    for idx, pw in enumerate(plan1.prioritized_workloads, start=1):
        assert pw.priority_rank == idx


# ==============================================================================
# 6. VALIDATION PLAN & EVIDENCE LINKAGE SCHEMA
# ==============================================================================

def test_validation_plan_linkage_schema():
    raw = "- Improved battery efficiency during background video playback"
    plan = create_validation_plan(raw, plan_id="PLAN-LINK-001")

    schema = plan.evidence_linkage_schema
    assert schema["schema_version"] == "1.0.0"
    linkages = schema["linkages"]
    assert len(linkages) == 1

    linkage = linkages[0]
    assert linkage["claim_id"] == "CLM-001"
    assert linkage["recommended_workload_id"] == "video_power_01"
    assert linkage["target_metric"] == "battery_discharge_proxy"
    # Ensure no fabricated V1 measurements exist in Phase 7
    assert linkage["v0_baseline_metric_value"] is None
    assert linkage["v1_target_metric_value"] is None
    assert linkage["phase_6_verdict"] is None
    assert linkage["status"] == "AWAITING_MEASUREMENT"


# ==============================================================================
# 7. PREDICTION STORE PERSISTENCE & ROUNDTRIP
# ==============================================================================

def test_prediction_store_roundtrip(tmp_path: Path):
    store = PredictionStore(tmp_path)
    raw = "- Faster cold app launch\n- Smooth scrolling at 120fps"
    plan = create_validation_plan(raw, plan_id="PLAN-STORE-001")
    quality = audit_prediction_quality(plan)

    master_file = store.save_plan(plan, quality=quality)
    assert master_file.exists()

    # Verify decomposed files exist
    plan_dir = store.get_plan_dir("PLAN-STORE-001")
    assert (plan_dir / "input.json").exists()
    assert (plan_dir / "claims.json").exists()
    assert (plan_dir / "predictions.json").exists()
    assert (plan_dir / "quality.json").exists()
    assert (plan_dir / "validation_plan.json").exists()
    assert (plan_dir / "provenance.json").exists()

    # Load and verify integrity
    loaded_plan = store.load_plan("PLAN-STORE-001")
    assert loaded_plan.plan_id == "PLAN-STORE-001"
    assert len(loaded_plan.claims) == 2
    assert loaded_plan.overall_path == PredictionPath.PATH_B_CLAIM_HISTORY

    # Check quality reload
    loaded_quality = store.load_quality("PLAN-STORE-001")
    assert loaded_quality is not None
    assert loaded_quality.claims_extracted == 2
    assert loaded_quality.quality_verdict == "HIGH_CONFIDENCE"

    # Verify listing
    assert store.list_plans() == ["PLAN-STORE-001"]
    assert store.has_plan("PLAN-STORE-001") is True
    assert store.has_plan("PLAN-NONEXISTENT") is False


def test_prediction_store_missing_plan_error(tmp_path: Path):
    store = PredictionStore(tmp_path)
    with pytest.raises(ExperimentPersistenceError):
        store.load_plan("PLAN-DOES-NOT-EXIST")


# ==============================================================================
# 8. ADVERSARIAL & EDGE-CASE INPUTS
# ==============================================================================

def test_adversarial_empty_release_notes():
    plan = create_validation_plan("", plan_id="PLAN-EMPTY-001")
    assert len(plan.claims) == 0
    assert len(plan.predictions) == 0
    assert len(plan.prioritized_workloads) == 0
    assert plan.overall_path == PredictionPath.PATH_C_INSUFFICIENT_EVIDENCE
    assert plan.overall_risk_score == 0.0

    quality = audit_prediction_quality(plan)
    assert quality.quality_verdict == "INCONCLUSIVE"


def test_adversarial_vague_marketing_fluff():
    raw = (
        "Experience the magic of an all-new dynamic fluid horizon with revolutionary "
        "AI capabilities that redefine mobile possibilities."
    )
    plan = create_validation_plan(raw, plan_id="PLAN-VAGUE-001")
    assert len(plan.claims) == 1
    c = plan.claims[0]
    assert c.subsystem == "unknown"
    assert c.metric_status == MetricStatus.UNSUPPORTED
    assert c.expected_direction == MetricDirection.UNKNOWN
    assert c.confidence <= 0.25

    # Should not recommend fake workloads for unsupported marketing fluff
    assert len(plan.prioritized_workloads) == 0


def test_adversarial_duplicate_claims():
    raw = (
        "- Faster cold app startup\n"
        "- Faster cold app startup\n"
    )
    plan = create_validation_plan(raw, plan_id="PLAN-DUP-001")
    assert len(plan.claims) == 2
    assert plan.claims[0].claim_id == "CLM-001"
    assert plan.claims[1].claim_id == "CLM-002"
    # Both associate with startup_01, but startup_01 should appear once in prioritized workloads
    assert len(plan.prioritized_workloads) == 1
    assert plan.prioritized_workloads[0].workload_id == "startup_01"
    assert plan.prioritized_workloads[0].associated_claim_ids == ["CLM-001", "CLM-002"]


# ==============================================================================
# 9. CLI COMMANDS INTEGRATION TESTS
# ==============================================================================

def test_cli_predict_inspect(capsys):
    from hexnil.cli import main
    rc = main(["predict", "inspect", "Improved battery efficiency during video playback"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "CLM-001" in out
    assert "battery" in out
    assert "battery_discharge_proxy" in out


def test_cli_predict_inspect_json(capsys):
    from hexnil.cli import main
    rc = main(["predict", "inspect", "Improved battery efficiency during video playback", "--json"])
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["subsystem"] == "battery"


def test_cli_predict_analyze_and_show(tmp_path: Path, capsys):
    from hexnil.cli import main
    plan_id = "PLAN-CLI-TEST-001"

    # Analyze
    rc = main([
        "--data-dir", str(tmp_path / "experiments"),
        "predict", "analyze",
        "- Faster cold app launch\n- Smooth 60fps scrolling",
        "--plan-id", plan_id,
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert plan_id in out
    assert "PATH_B_CLAIM_HISTORY" in out

    # Show
    rc_show = main([
        "--data-dir", str(tmp_path / "experiments"),
        "predict", "show", plan_id,
    ])
    assert rc_show == 0
    out_show = capsys.readouterr().out
    assert plan_id in out_show

    # Claims
    rc_claims = main([
        "--data-dir", str(tmp_path / "experiments"),
        "predict", "claims", plan_id, "--json",
    ])
    assert rc_claims == 0
    claims_data = json.loads(capsys.readouterr().out)
    assert len(claims_data) == 2

    # Workloads
    rc_wl = main([
        "--data-dir", str(tmp_path / "experiments"),
        "predict", "workloads", plan_id, "--json",
    ])
    assert rc_wl == 0
    wl_data = json.loads(capsys.readouterr().out)
    assert len(wl_data) == 2

    # Quality
    rc_qual = main([
        "--data-dir", str(tmp_path / "experiments"),
        "predict", "quality", plan_id, "--json",
    ])
    assert rc_qual == 0
    qual_data = json.loads(capsys.readouterr().out)
    assert qual_data["quality_verdict"] == "HIGH_CONFIDENCE"
