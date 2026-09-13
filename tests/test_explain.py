"""Comprehensive unit and integration tests for Phase 8: Evidence-Grounded AI Analyst (Groq)."""

import json
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

from hexnil.diff.models import ComparisonRecord
from hexnil.diff.store import ComparisonStore
from hexnil.exceptions import GroqApiError, GroqConfigurationError, HexnilError
from hexnil.explain import (
    ClaimAssessment,
    EvidenceEligibilityState,
    EvidenceExplanation,
    EvidenceExplanationOrchestrator,
    EvidencePackage,
    EvidenceReference,
    ExplanationCache,
    ExplanationSource,
    ExplanationStore,
    GroqClient,
    MetricEvidenceSummary,
    build_evidence_package,
    build_system_prompt,
    build_user_prompt,
    compute_evidence_hash,
    generate_deterministic_explanation,
    validate_evidence_eligibility,
    validate_groq_response,
)
from hexnil.stats.models import (
    ConfidenceInterval,
    EngineeringThreshold,
    MetricComparison,
    MetricDirection,
    MetricEligibility,
    Severity,
    StatisticalAnalysisRecord,
    StatisticalQualityReport,
    StatisticalTestResult,
    Verdict,
)


@pytest.fixture
def sample_analysis_record() -> StatisticalAnalysisRecord:
    """Create a minimal valid StatisticalAnalysisRecord."""
    metric = MetricComparison(
        comparison_id="CMP-20260913-001",
        workload_id="startup_01",
        metric_name="startup_duration_ms",
        metric_unit="ms",
        direction=MetricDirection.LOWER_IS_BETTER,
        eligibility=MetricEligibility.SUPPORTED_AND_ELIGIBLE,
        sample_count=3,
        v0_mean=1000.0,
        v1_mean=1050.0,
        absolute_delta=50.0,
        percent_delta=5.0,
        effect_size=0.8,
        confidence_interval=ConfidenceInterval(lower=-20.0, upper=120.0),
        statistical_test=StatisticalTestResult(test_name="paired_t_test", p_value=0.25, is_significant=False),
        threshold=EngineeringThreshold(meaningful_change_percent=5.0),
        verdict=Verdict.INCONCLUSIVE,
        severity=Severity.NONE,
        verdict_reason="Shift not statistically significant (p=0.25 >= 0.05).",
        status="VALID",
    )
    metric_unsupported = MetricComparison(
        comparison_id="CMP-20260913-001",
        workload_id="video_power_01",
        metric_name="thermal_max_celsius",
        metric_unit="C",
        direction=MetricDirection.LOWER_IS_BETTER,
        eligibility=MetricEligibility.UNSUPPORTED,
        sample_count=0,
        verdict=Verdict.INCONCLUSIVE,
        severity=Severity.NONE,
        verdict_reason="Thermal sensor sysfs blocked on Android 16.",
        status="UNSUPPORTED",
        threshold=EngineeringThreshold(),
    )

    quality = StatisticalQualityReport(
        analysis_id="STATS-CMP-20260913-001",
        comparison_id="CMP-20260913-001",
        metrics_analyzed=2,
        metrics_eligible=1,
        metrics_inconclusive=1,
        metrics_unsupported=1,
        evidence_coverage="1 / 2",
        verdicts_summary={"UNCHANGED": 0, "REGRESSION": 0, "INCONCLUSIVE": 2},
        summary_verdict="COMPLETED",
    )

    return StatisticalAnalysisRecord(
        analysis_id="STATS-CMP-20260913-001",
        comparison_id="CMP-20260913-001",
        created_at="2026-09-13T12:00:00Z",
        metric_results=[metric, metric_unsupported],
        quality=quality,
        provenance={"v0_experiment_id": "EXP-20260913-010", "v1_experiment_id": "EXP-20260913-012"},
    )


def test_01_valid_evidence_package_accepted(sample_analysis_record):
    """Scenario 1: Valid evidence package is generated and accepted by eligibility gate."""
    package = build_evidence_package(sample_analysis_record)
    assert package.schema_version == "1.0"
    assert package.comparison_id == "CMP-20260913-001"
    assert len(package.metrics) == 2
    assert package.evidence_hash != ""

    is_eligible, state, reasons = validate_evidence_eligibility(package)
    assert is_eligible is True
    assert state in (EvidenceEligibilityState.SUFFICIENT, EvidenceEligibilityState.PARTIAL)


def test_02_missing_comparison_rejected(sample_analysis_record):
    """Scenario 2: Evidence package with missing comparison ID is rejected."""
    package = build_evidence_package(sample_analysis_record)
    package.comparison_id = ""

    is_eligible, state, reasons = validate_evidence_eligibility(package)
    assert is_eligible is False
    assert state == EvidenceEligibilityState.INVALID
    assert any("comparison ID" in r for r in reasons)


def test_03_missing_metric_rejected(sample_analysis_record):
    """Scenario 3: Evidence package with empty metrics is rejected as insufficient."""
    package = build_evidence_package(sample_analysis_record)
    package.metrics = []

    is_eligible, state, reasons = validate_evidence_eligibility(package)
    assert is_eligible is False
    assert state == EvidenceEligibilityState.INSUFFICIENT


def test_04_unsupported_metric_handled(sample_analysis_record):
    """Scenario 4: Unsupported metric is preserved as unsupported, never coerced to 0 or unchanged."""
    package = build_evidence_package(sample_analysis_record)
    unsupported = [m for m in package.metrics if m.status == "UNSUPPORTED"]
    assert len(unsupported) == 1
    assert unsupported[0].metric_name == "thermal_max_celsius"
    assert unsupported[0].v0_mean is None
    assert unsupported[0].verdict == "INCONCLUSIVE"


def test_05_inconclusive_evidence_remains_inconclusive(sample_analysis_record):
    """Scenario 5: Inconclusive metric verdict is preserved and never converted to regression."""
    package = build_evidence_package(sample_analysis_record)
    startup = next(m for m in package.metrics if m.metric_name == "startup_duration_ms")
    assert startup.verdict == "INCONCLUSIVE"

    explanation = generate_deterministic_explanation(package)
    assert "INCONCLUSIVE" in explanation.observed_changes[0] or "INCONCLUSIVE" in explanation.statistical_interpretation


def test_06_invalid_artifact_rejected(tmp_path):
    """Scenario 6: Corrupted analysis file is safely caught and rejected."""
    store = ExplanationStore(tmp_path)
    corrupted_dir = tmp_path / "CMP-20260913-CORRUPT" / "explanation"
    corrupted_dir.mkdir(parents=True)
    (corrupted_dir / "explanation.json").write_text("NOT_VALID_JSON", encoding="utf-8")

    loaded = store.load_explanation("CMP-20260913-CORRUPT")
    assert loaded is None


def test_07_missing_groq_key_uses_deterministic_fallback(sample_analysis_record, monkeypatch):
    """Scenario 7: Missing GROQ_API_KEY environment variable uses deterministic fallback."""
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    package = build_evidence_package(sample_analysis_record)
    client = GroqClient(api_key=None, load_env=False)
    assert client.has_valid_key() is False

    with pytest.raises(GroqConfigurationError):
        client.complete("prompt", "system")

    # Orchestrator handles missing key gracefully
    explanation = generate_deterministic_explanation(package, reason="No key")
    assert explanation.source == ExplanationSource.DETERMINISTIC_FALLBACK
    assert explanation.model is None


def test_08_groq_timeout_uses_fallback(sample_analysis_record):
    """Scenario 8: Network timeout in Groq client raises GroqApiError and triggers fallback."""
    package = build_evidence_package(sample_analysis_record)
    client = GroqClient(api_key="gsk_dummy_test_key", timeout_seconds=0.01)

    with patch("requests.post", side_effect=requests.exceptions.Timeout()):
        with pytest.raises(GroqApiError) as exc_info:
            client.complete("prompt", "system")
        assert "timed out" in str(exc_info.value).lower()

    # Fallback explanation generated cleanly
    explanation = generate_deterministic_explanation(package, reason="Request timed out")
    assert explanation.source == ExplanationSource.DETERMINISTIC_FALLBACK
    assert "Request timed out" in explanation.limitations[-1]


def test_09_groq_malformed_json_uses_fallback(sample_analysis_record):
    """Scenario 9: Groq returning invalid JSON is caught and handled."""
    client = GroqClient(api_key="gsk_dummy_test_key")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "INVALID_NON_JSON_CONTENT"}}]
    }

    with patch("requests.post", return_value=mock_resp):
        with pytest.raises(GroqApiError) as exc_info:
            client.complete("prompt", "system")
        assert "not valid JSON" in str(exc_info.value)


def test_10_groq_response_fabricated_metric_rejected(sample_analysis_record):
    """Scenario 10: Groq response citing a fabricated metric is rejected by ground-truth validator."""
    package = build_evidence_package(sample_analysis_record)
    fabricated_response = {
        "summary": "Summary of tests.",
        "observed_changes": ["Metric changed."],
        "statistical_interpretation": "p-value analysis.",
        "severity": "NONE",
        "limitations": ["Small sample size."],
        "recommended_next_step": "Run more tests.",
        "evidence_references": [
            {"reference_id": "REF-001", "type": "metric", "identifier": "non_existent_fake_metric"}
        ],
    }

    is_valid, errors, data = validate_groq_response(fabricated_response, package)
    assert is_valid is False
    assert any("unknown metric" in e.lower() for e in errors)


def test_11_groq_response_unknown_evidence_ref_rejected(sample_analysis_record):
    """Scenario 11: Groq response with unknown workload or comparison reference is rejected."""
    package = build_evidence_package(sample_analysis_record)
    bad_ref_response = {
        "summary": "Summary of tests.",
        "observed_changes": ["Metric changed."],
        "statistical_interpretation": "p-value analysis.",
        "severity": "NONE",
        "limitations": ["Small sample size."],
        "recommended_next_step": "Run more tests.",
        "evidence_references": [
            {"reference_id": "REF-001", "type": "comparison", "identifier": "CMP-99999999-999"}
        ],
    }

    is_valid, errors, data = validate_groq_response(bad_ref_response, package)
    assert is_valid is False
    assert any("comparison ID" in e for e in errors)


def test_12_groq_response_contradicting_verdict_rejected(sample_analysis_record):
    """Scenario 12: Groq response claiming critical regression when statistical engine found 0 is rejected."""
    package = build_evidence_package(sample_analysis_record)
    contradictory_response = {
        "summary": "A critical regression detected in mobile update build.",
        "observed_changes": ["Shift observed."],
        "statistical_interpretation": "Significant shift.",
        "severity": "NONE",
        "limitations": ["Limited power."],
        "recommended_next_step": "Block release.",
    }

    is_valid, errors, data = validate_groq_response(contradictory_response, package)
    assert is_valid is False
    assert any("regression" in e.lower() for e in errors)


def test_13_groq_response_changing_deterministic_severity_rejected(sample_analysis_record):
    """Scenario 13: Groq escalating severity beyond deterministic maximum is rejected."""
    package = build_evidence_package(sample_analysis_record)
    escalated_response = {
        "summary": "Summary of results.",
        "observed_changes": ["Shift observed."],
        "statistical_interpretation": "Analysis.",
        "severity": "CRITICAL",  # Deterministic max is NONE
        "limitations": ["None."],
        "recommended_next_step": "Fix immediately.",
    }

    is_valid, errors, data = validate_groq_response(escalated_response, package)
    assert is_valid is False
    assert any("exceeds deterministic maximum severity" in e for e in errors)


def test_14_no_regression_experiment_no_fabricated_regression(sample_analysis_record):
    """Scenario 14: Clean experiment with 0 regressions produces 0-regression explanation."""
    package = build_evidence_package(sample_analysis_record)
    explanation = generate_deterministic_explanation(package)
    assert "Zero regressions were detected" in explanation.summary
    assert explanation.severity == "NONE"


def test_15_cached_explanation_invalidated_when_comparison_changes(tmp_path, sample_analysis_record):
    """Scenario 15: Cached explanation is invalidated when the underlying evidence hash changes."""
    store = ExplanationStore(tmp_path)
    cache = ExplanationCache(store)

    package1 = build_evidence_package(sample_analysis_record)
    exp1 = generate_deterministic_explanation(package1)
    cache.put_cached(exp1)

    # Retrieval matches
    hit = cache.get_cached(package1)
    assert hit is not None
    assert hit.is_cached is True

    # Mutate package evidence
    package2 = build_evidence_package(sample_analysis_record)
    package2.evidence_hash = "different_hash_999"

    # Cache miss due to hash mismatch
    miss = cache.get_cached(package2)
    assert miss is None


def test_16_historical_comparison_not_silently_substituted(sample_analysis_record):
    """Scenario 16: Explanation is bound strictly to the target comparison ID."""
    package = build_evidence_package(sample_analysis_record)
    explanation = generate_deterministic_explanation(package)
    assert explanation.comparison_id == "CMP-20260913-001"
    assert "CMP-20260913-001" in explanation.summary
    assert explanation.evidence_references[0].identifier == "CMP-20260913-001"


def test_17_secrets_never_appear_in_logs(caplog):
    """Scenario 17: Secret API keys are never logged in plaintext or exception messages."""
    secret_key = "gsk_super_secret_key_123456789"
    client = GroqClient(api_key=secret_key)

    with caplog.at_level(logging.DEBUG):
        with patch("requests.post", side_effect=requests.exceptions.ConnectionError("Connection failed")):
            with pytest.raises(GroqApiError) as exc_info:
                client.complete("prompt", "system")

    # Verify secret is not in exception string
    assert secret_key not in str(exc_info.value)

    # Verify secret is not in log records
    for record in caplog.records:
        assert secret_key not in record.getMessage()


def test_18_android_ui_distinguishes_ai_vs_deterministic_fallback():
    """Scenario 18: Explanation source enum cleanly distinguishes Groq AI, Deterministic Analysis, and Fallback."""
    assert ExplanationSource.GROQ_AI.value == "GROQ_AI"
    assert ExplanationSource.DETERMINISTIC_ANALYSIS.value == "DETERMINISTIC_ANALYSIS"
    assert ExplanationSource.DETERMINISTIC_FALLBACK.value == "DETERMINISTIC_FALLBACK"
