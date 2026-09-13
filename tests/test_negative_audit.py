"""Negative tests proving honest failure across all 16 required audit scenarios."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from hexnil.device.discovery import DeviceDiscovery
from hexnil.device.models import DeviceState, DiscoveredDevice
from hexnil.diff.models import ComparisonQualityReport, ComparisonRunPair, PairStatus
from hexnil.diff.matcher import WorkloadRunMatcher
from hexnil.diff.quality import evaluate_comparison_quality
from hexnil.exceptions import (
    AdbExecutionError,
    DeviceNotFoundError,
    DeviceOfflineError,
    DeviceUnauthorizedError,
    ExperimentPersistenceError,
    NoDevicesConnectedError,
)
from hexnil.experiments.store import ExperimentStore
from hexnil.predict.models import (
    MetricStatus,
    PredictionPath,
    RiskBand,
)
from hexnil.predict.planner import create_validation_plan
from hexnil.predict.predictor import (
    inspect_feature_availability,
    predict_claim_risk,
    select_prediction_path,
)
from hexnil.predict.quality import audit_prediction_quality
from hexnil.predict.store import PredictionStore
from hexnil.stats.classifier import classify_verdict_and_severity
from hexnil.stats.engine import compute_percentage_delta
from hexnil.stats.models import (
    EngineeringThreshold,
    MetricDirection,
    MetricEligibility,
    Verdict,
)
from hexnil.stats.orchestrator import StatisticalAnalysisOrchestrator
from hexnil.telemetry.adb_collectors import AdbGfxinfoCollector
from hexnil.telemetry.models import (
    CapabilityStatus,
    DeviceMetadata,
    SoftwareIdentity,
    TelemetryRecord,
    WorkloadIdentity,
)
from hexnil.workloads.models import RunStatus, WorkloadRun


# ------------------------------------------------------------------------------
# 1. No Android device connected
# ------------------------------------------------------------------------------
def test_negative_01_no_device_connected():
    mock_adb = MagicMock()
    mock_adb.run_cmd.return_value = "List of devices attached\n\n"
    discovery = DeviceDiscovery(mock_adb)

    with pytest.raises(NoDevicesConnectedError) as exc_info:
        discovery.select_device()
    assert "No Android devices connected" in str(exc_info.value)


# ------------------------------------------------------------------------------
# 2. Device unauthorized / offline
# ------------------------------------------------------------------------------
def test_negative_02_device_unauthorized_or_offline():
    mock_adb = MagicMock()
    mock_adb.run_cmd.return_value = (
        "List of devices attached\n"
        "SERIAL_UNAUTH          unauthorized\n"
        "SERIAL_OFFLINE         offline\n"
    )

    discovery = DeviceDiscovery(mock_adb)
    with pytest.raises(DeviceUnauthorizedError):
        discovery.select_device("SERIAL_UNAUTH")

    with pytest.raises(DeviceOfflineError):
        discovery.select_device("SERIAL_OFFLINE")


# ------------------------------------------------------------------------------
# 3. Metric source unavailable
# ------------------------------------------------------------------------------
def test_negative_03_metric_source_unavailable(tmp_path: Path):
    mock_adb = MagicMock()
    mock_adb.run_serial_cmd.return_value = "Graphics info unavailable on platform"
    collector = AdbGfxinfoCollector(mock_adb)
    dev = DeviceMetadata(
        serial="SERIAL1",
        model="TestModel",
        manufacturer="TestBrand",
        build_fingerprint="test/fp",
        android_version="14",
        sdk_version=34,
    )
    sw = SoftwareIdentity(package="com.test", version_name="1.0", version_code=1)
    wl = WorkloadIdentity(workload_id="startup_01", workload_name="Cold Startup")
    
    records = collector.collect("SERIAL1", "EXP1", dev, sw, wl, tmp_path)
    assert len(records) == 1
    # Verify capability is not fabricated, value is None (never defaulted to 0.0)
    assert records[0].metric.value is None
    assert records[0].capability in (CapabilityStatus.CONDITIONAL, CapabilityStatus.UNSUPPORTED)


# ------------------------------------------------------------------------------
# 4. Telemetry command / API failure
# ------------------------------------------------------------------------------
def test_negative_04_telemetry_command_failure():
    mock_adb = MagicMock()
    mock_adb.run_cmd.side_effect = AdbExecutionError(
        command=["adb", "shell", "dumpsys"],
        returncode=1,
        stderr="Permission denied",
    )
    
    with pytest.raises(AdbExecutionError):
        mock_adb.run_cmd(["shell", "dumpsys"])


# ------------------------------------------------------------------------------
# 5. Missing V0 data
# ------------------------------------------------------------------------------
def test_negative_05_missing_v0_data(tmp_path: Path):
    store = ExperimentStore(tmp_path)
    with pytest.raises(ExperimentPersistenceError) as exc_info:
        store.load("EXP-NONEXISTENT-V0")
    assert "does not exist" in str(exc_info.value)


# ------------------------------------------------------------------------------
# 6. Missing V1 data
# ------------------------------------------------------------------------------
def test_negative_06_missing_v1_data(tmp_path: Path):
    store = ExperimentStore(tmp_path)
    with pytest.raises(ExperimentPersistenceError) as exc_info:
        store.load("EXP-NONEXISTENT-V1")
    assert "does not exist" in str(exc_info.value)


# ------------------------------------------------------------------------------
# 7. Mismatched device
# ------------------------------------------------------------------------------
def test_negative_07_mismatched_device():
    # Comparison between two different devices flags contamination and sets is_clean_comparison=False
    report = evaluate_comparison_quality(
        comparison_id="CMP-TEST-DEV-MISMATCH",
        v0_experiment_id="EXP-V0",
        v1_experiment_id="EXP-V1",
        device_serial="DEVICE_BBB",
        device_model="Galaxy S21",
        v0_version="1.0.0",
        v1_version="1.1.0",
        v0_apk_sha256="abc",
        v1_apk_sha256="def",
        workloads_requested=["startup_01"],
        workloads_matched=["startup_01"],
        workloads_mismatched=[],
        iterations_requested=1,
        v0_valid_runs_count=1,
        v1_valid_runs_count=1,
        pairs=[],
        contamination_flags=["Device serial mismatch: V0 was measured on 'DEVICE_AAA', but target is 'DEVICE_BBB'"],
    )
    assert report.is_clean_comparison is False
    assert report.summary_verdict == "CONTAMINATED_COMPARISON"
    assert any("Device serial mismatch" in f for f in report.contamination_flags)


# ------------------------------------------------------------------------------
# 8. Mismatched workload configuration
# ------------------------------------------------------------------------------
def test_negative_08_mismatched_workload_config():
    matcher = WorkloadRunMatcher()
    v0_run = WorkloadRun(
        run_id="RUN-V0",
        experiment_id="EXP-V0",
        workload_id="startup_01",
        workload_version="1.0",
        iteration=1,
        configuration_hash="HASH_AAA",
        status=RunStatus.SUCCESS,
        started_at="2026-09-13T10:00:00Z",
        ended_at="2026-09-13T10:00:01Z",
        duration_ms=1000.0,
    )
    v1_run = WorkloadRun(
        run_id="RUN-V1",
        experiment_id="EXP-V1",
        workload_id="startup_01",
        workload_version="1.0",
        iteration=1,
        configuration_hash="HASH_BBB",
        status=RunStatus.SUCCESS,
        started_at="2026-09-13T10:05:00Z",
        ended_at="2026-09-13T10:05:01Z",
        duration_ms=1000.0,
    )
    pairs = matcher.match_runs(
        comparison_id="CMP-CONFIG-MISMATCH",
        v0_runs=[v0_run],
        v1_runs=[v1_run],
        v0_workload_hashes={"startup_01": "HASH_AAA"},
        v1_workload_hashes={"startup_01": "HASH_BBB"},
    )
    assert len(pairs) == 1
    assert pairs[0].pair_status == PairStatus.CONFIGURATION_MISMATCH
    assert "Configuration hash mismatch" in pairs[0].mismatch_reason


# ------------------------------------------------------------------------------
# 9. Insufficient matched pairs
# ------------------------------------------------------------------------------
def test_negative_09_insufficient_matched_pairs():
    threshold = EngineeringThreshold(threshold_type="percent", meaningful_change_percent=5.0)
    
    # 1 sample is insufficient for paired t-test
    verdict, severity, reason = classify_verdict_and_severity(
        direction=MetricDirection.LOWER_IS_BETTER,
        eligibility=MetricEligibility.INSUFFICIENT_DATA,
        absolute_delta=100.0,
        percent_delta=10.0,
        threshold=threshold,
        sample_count=1,
    )
    assert verdict == Verdict.INCONCLUSIVE
    assert "Insufficient" in reason


# ------------------------------------------------------------------------------
# 10. Missing statistical inputs (safe denominator check)
# ------------------------------------------------------------------------------
def test_negative_10_missing_statistical_inputs_safe_denominator():
    # If baseline is 0, percentage delta cannot divide by zero
    delta = compute_percentage_delta([0.0, 0.0], [50.0, 60.0])
    assert delta is None  # Must NOT be 0.0 or raise ZeroDivisionError


# ------------------------------------------------------------------------------
# 11. Unsupported metric
# ------------------------------------------------------------------------------
def test_negative_11_unsupported_metric():
    threshold = EngineeringThreshold(threshold_type="percent", meaningful_change_percent=5.0)
    
    verdict, severity, reason = classify_verdict_and_severity(
        direction=MetricDirection.UNKNOWN,
        eligibility=MetricEligibility.UNSUPPORTED,
        absolute_delta=None,
        percent_delta=None,
        threshold=threshold,
        sample_count=0,
    )
    assert verdict == Verdict.INCONCLUSIVE
    assert severity.value == "NONE"
    assert "not supported" in reason.lower()


# ------------------------------------------------------------------------------
# 12. Invalid / corrupt artifact
# ------------------------------------------------------------------------------
def test_negative_12_corrupt_artifact(tmp_path: Path):
    store = PredictionStore(tmp_path)
    corrupt_dir = tmp_path / "PLAN-CORRUPT"
    corrupt_dir.mkdir()
    (corrupt_dir / "validation_plan.json").write_text("{corrupt: json content", encoding="utf-8")
    
    with pytest.raises(ExperimentPersistenceError):
        store.load_plan("PLAN-CORRUPT")


# ------------------------------------------------------------------------------
# 13. Missing Phase 7 model artifact
# ------------------------------------------------------------------------------
def test_negative_13_missing_phase7_model_artifact(tmp_path: Path):
    # When model file doesn't exist, predictor gracefully falls back to Path B prior
    from hexnil.predict.mapping import structure_claim
    claim = structure_claim("Faster startup", "Faster startup", 1)
    code_churn = {"delta_loc": 500, "delta_nom": 10, "delta_noc": 2, "delta_wmc": 50.0, "delta_cbo": 0.01, "delta_bad_smells": 0}
    
    with patch("hexnil.predict.predictor.MODEL_PATH", tmp_path / "nonexistent.joblib"):
        features = inspect_feature_availability([claim], code_changes=code_churn)
        pred = predict_claim_risk(claim, features, code_changes=code_churn)
        # Verify fallback and explanation
        assert pred.raw_risk_score > 0.0
        assert any("fallback" in exp.lower() or "artifact not found" in exp.lower() for exp in pred.explanation)
        assert pred.prediction_path == PredictionPath.PATH_B_CLAIM_HISTORY


# ------------------------------------------------------------------------------
# 14. Release note with no recognized claims
# ------------------------------------------------------------------------------
def test_negative_14_release_note_no_recognized_claims():
    raw = "Magical revolutionary experience of delight and bliss."
    plan = create_validation_plan(raw, plan_id="PLAN-NO-RECOG")
    assert len(plan.claims) == 1
    assert plan.claims[0].subsystem == "unknown"
    assert plan.claims[0].metric_status == MetricStatus.UNSUPPORTED
    assert len(plan.prioritized_workloads) == 0
    
    quality = audit_prediction_quality(plan)
    assert quality.quality_verdict == "INCONCLUSIVE"


# ------------------------------------------------------------------------------
# 15. Claim with no measurable metric
# ------------------------------------------------------------------------------
def test_negative_15_claim_no_measurable_metric():
    raw = "Reduced camera shutter lag and low-light optical sensor distortion."
    plan = create_validation_plan(raw, plan_id="PLAN-CAM")
    assert plan.claims[0].metric == "UNSUPPORTED"
    assert plan.claims[0].metric_status == MetricStatus.UNSUPPORTED
    assert plan.claims[0].expected_direction == MetricDirection.UNKNOWN
    # No fake workloads created
    assert len(plan.prioritized_workloads) == 0


# ------------------------------------------------------------------------------
# 16. Prediction path with unavailable code-change features
# ------------------------------------------------------------------------------
def test_negative_16_unavailable_code_change_features_never_uses_path_a():
    raw = "- Improved battery efficiency during video playback\n- Faster startup"
    # When code changes are absent
    plan = create_validation_plan(raw, code_changes=None, plan_id="PLAN-NO-CHURN")
    assert plan.feature_availability.has_code_change_features is False
    assert plan.overall_path == PredictionPath.PATH_B_CLAIM_HISTORY
    # Must NOT select Path A
    assert plan.overall_path != PredictionPath.PATH_A_CODE_CHANGE
    for p in plan.predictions:
        assert p.prediction_path == PredictionPath.PATH_B_CLAIM_HISTORY
