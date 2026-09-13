"""Workload recommendation mapping and deterministic prioritization ranking for Phase 7."""

from typing import Any, Dict, List, Optional, Set, Tuple
from hexnil.predict.models import (
    ClaimPrediction,
    ClaimSubsystem,
    MetricStatus,
    PrioritizedWorkload,
    StructuredClaim,
    WorkloadRecommendation,
)

RECOMMENDER_VERSION = "1.0.0"

# Mapping from subsystem to existing Phase 3 workloads, required metrics, and base rationale
SUBSYSTEM_TO_WORKLOAD: Dict[str, List[Dict[str, Any]]] = {
    ClaimSubsystem.BATTERY.value: [
        {
            "workload_id": "video_power_01",
            "required_metrics": ["battery_discharge_proxy", "playback_duration_ms", "workload_duration_ms"],
            "base_relevance": 0.95,
            "reason_template": "Executes continuous video playback loop while sampling battery discharge proxy and duration.",
            "estimated_duration_ms": 10000,
        }
    ],
    ClaimSubsystem.STARTUP.value: [
        {
            "workload_id": "startup_01",
            "required_metrics": ["startup_duration_ms", "workload_duration_ms"],
            "base_relevance": 0.95,
            "reason_template": "Measures cold application process launch and initial frame rendering latency.",
            "estimated_duration_ms": 5000,
        }
    ],
    ClaimSubsystem.MEMORY.value: [
        {
            "workload_id": "memory_01",
            "required_metrics": ["app_heap_allocated_mb", "device_memory_available_mb", "workload_duration_ms"],
            "base_relevance": 0.92,
            "reason_template": "Samples ART/Dalvik allocated heap memory and system free RAM under deterministic load.",
            "estimated_duration_ms": 6000,
        }
    ],
    ClaimSubsystem.UI_PERFORMANCE.value: [
        {
            "workload_id": "scroll_01",
            "required_metrics": ["ui_frame_jank_percent", "scroll_duration_ms", "workload_duration_ms"],
            "base_relevance": 0.92,
            "reason_template": "Performs programmatic list scrolling gestures to measure vsync deadline misses and jank percent.",
            "estimated_duration_ms": 7000,
        }
    ],
    ClaimSubsystem.CPU_PERFORMANCE.value: [
        {
            "workload_id": "cpu_01",
            "required_metrics": ["compute_duration_ms", "workload_duration_ms"],
            "base_relevance": 0.90,
            "reason_template": "Executes CPU-bound SHA-256 computation step to measure sustained processor compute time.",
            "estimated_duration_ms": 8000,
        }
    ],
    ClaimSubsystem.STABILITY.value: [
        # Stability claims recommend running the core workload suite to detect process crashes
        {
            "workload_id": "startup_01",
            "required_metrics": ["workload_duration_ms"],
            "base_relevance": 0.60,
            "reason_template": "Verifies launch stability and absence of cold startup fatal exceptions.",
            "estimated_duration_ms": 5000,
        },
        {
            "workload_id": "scroll_01",
            "required_metrics": ["workload_duration_ms"],
            "base_relevance": 0.55,
            "reason_template": "Verifies runtime UI stability and gesture event loop handling without crashes.",
            "estimated_duration_ms": 7000,
        },
    ],
}


def recommend_workloads_for_claim(
    claim: StructuredClaim,
) -> List[WorkloadRecommendation]:
    """Map a structured claim to one or more existing Phase 3 workloads."""
    workload_configs = SUBSYSTEM_TO_WORKLOAD.get(claim.subsystem, [])
    if not workload_configs:
        return []

    recommendations: List[WorkloadRecommendation] = []
    for cfg in workload_configs:
        # Scale relevance by claim extraction confidence
        relevance = round(cfg["base_relevance"] * claim.confidence, 3)
        reason = f"{cfg['reason_template']} (Validates: '{claim.normalized_text}')"

        recommendations.append(
            WorkloadRecommendation(
                workload_id=cfg["workload_id"],
                reason=reason,
                relevance_score=relevance,
                required_metrics=list(cfg["required_metrics"]),
                claim_id=claim.claim_id,
                execution_type="Android-side test",
            )
        )

    return recommendations


def prioritize_workloads(
    claims: List[StructuredClaim],
    predictions: List[ClaimPrediction],
) -> List[PrioritizedWorkload]:
    """Deterministically prioritize workloads across all claims.

    Formula:
      composite_score = 0.50 * max_claim_risk
                      + 0.30 * max_relevance
                      + 0.15 * measurability_score
                      + 0.05 * cost_efficiency

    Tie-breaking:
      Sort by (-composite_score, workload_id) for strictly deterministic ordering.
    """
    # Group recommendations and predictions by workload_id
    workload_claims: Dict[str, List[str]] = {}
    workload_metrics: Dict[str, Set[str]] = {}
    workload_risks: Dict[str, List[float]] = {}
    workload_relevances: Dict[str, List[float]] = {}
    workload_reasons: Dict[str, List[str]] = {}
    workload_durations: Dict[str, int] = {}

    claim_risk_map = {p.claim_id: p.raw_risk_score for p in predictions}

    for pred in predictions:
        for rec in pred.recommendations:
            wid = rec.workload_id
            if wid not in workload_claims:
                workload_claims[wid] = []
                workload_metrics[wid] = set()
                workload_risks[wid] = []
                workload_relevances[wid] = []
                workload_reasons[wid] = []

            workload_claims[wid].append(rec.claim_id)
            workload_metrics[wid].update(rec.required_metrics)
            workload_risks[wid].append(claim_risk_map.get(rec.claim_id, 0.2))
            workload_relevances[wid].append(rec.relevance_score)
            workload_reasons[wid].append(rec.reason)

    if not workload_claims:
        return []

    scored_workloads: List[Tuple[float, str, PrioritizedWorkload]] = []

    for wid, c_ids in workload_claims.items():
        max_risk = max(workload_risks[wid]) if workload_risks[wid] else 0.2
        max_relevance = max(workload_relevances[wid]) if workload_relevances[wid] else 0.5
        measurability = 1.0  # Phase 3 workloads have supported metrics

        # Approximate duration cost: shorter tests get slightly higher throughput score
        estimated_duration = 6000
        for sub_list in SUBSYSTEM_TO_WORKLOAD.values():
            for item in sub_list:
                if item["workload_id"] == wid:
                    estimated_duration = item.get("estimated_duration_ms", 6000)
                    break

        cost_factor = max(0.0, 1.0 - (estimated_duration / 20000.0))

        priority_score = (
            0.50 * max_risk
            + 0.30 * max_relevance
            + 0.15 * measurability
            + 0.05 * cost_factor
        )
        priority_score = round(priority_score, 4)

        unique_claims = sorted(list(set(c_ids)))
        unique_metrics = sorted(list(workload_metrics[wid]))
        rationale = (
            f"Ranked for {len(unique_claims)} claim(s) [{', '.join(unique_claims)}]. "
            f"Max predicted risk: {max_risk:.2f}, relevance: {max_relevance:.2f}."
        )

        item = PrioritizedWorkload(
            priority_rank=0,  # assigned after sorting
            workload_id=wid,
            priority_score=priority_score,
            associated_claim_ids=unique_claims,
            target_metrics=unique_metrics,
            rationale=rationale,
            execution_type="Android-side test",
            estimated_duration_ms=estimated_duration,
        )
        scored_workloads.append((priority_score, wid, item))

    # Deterministic sort: highest priority_score first, then alphabetically by workload_id
    scored_workloads.sort(key=lambda x: (-x[0], x[1]))

    result: List[PrioritizedWorkload] = []
    for rank, (_, _, pw) in enumerate(scored_workloads, start=1):
        pw.priority_rank = rank
        result.append(pw)

    return result
