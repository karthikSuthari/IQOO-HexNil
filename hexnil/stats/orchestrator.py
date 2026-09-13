"""Statistical Analysis Orchestrator coordinating sample extraction, inferential testing, and verdicts."""

import datetime
import logging
from pathlib import Path
import statistics
from typing import Any, Dict, List, Optional, Tuple

from hexnil.diff.models import PairStatus
from hexnil.diff.store import ComparisonStore
from hexnil.exceptions import HexnilError
from hexnil.experiments.store import ExperimentStore
from hexnil.stats.classifier import classify_verdict_and_severity
from hexnil.stats.engine import (
    adjust_p_values,
    compute_absolute_delta,
    compute_cohens_d_paired,
    compute_paired_confidence_interval,
    compute_paired_differences,
    compute_percentage_delta,
    perform_paired_t_test,
)
from hexnil.stats.models import (
    MetricComparison,
    MetricDirection,
    MetricEligibility,
    Severity,
    StatisticalAnalysisRecord,
    StatisticalQualityReport,
    Verdict,
)
from hexnil.stats.registry import (
    METRIC_REGISTRY,
    get_metric_direction,
    get_registered_metrics_for_workload,
)
from hexnil.stats.store import StatisticalAnalysisStore
from hexnil.stats.thresholds import CURRENT_THRESHOLD_VERSION, get_threshold_for_metric
from hexnil.telemetry.models import TelemetryRecord
from hexnil.workloads.models import WorkloadRun

logger = logging.getLogger("hexnil.stats.orchestrator")


class StatisticalAnalysisOrchestrator:
    """Coordinates statistical analysis, hypothesis testing, and deterministic regression detection."""

    def __init__(
        self,
        exp_store: ExperimentStore,
        comp_store: ComparisonStore,
        stats_store: StatisticalAnalysisStore,
    ):
        self.exp_store = exp_store
        self.comp_store = comp_store
        self.stats_store = stats_store

    def inspect_comparison(self, comparison_id: str) -> Dict[str, Any]:
        """Inspect a comparison package and verify readiness for statistical comparison."""
        comp_record = self.comp_store.load_comparison(comparison_id)
        quality = self.comp_store.load_comparison_quality(comparison_id)
        pairs = self.comp_store.load_comparison_pairs(comparison_id)

        matched_pairs = [p for p in pairs if p.pair_status == PairStatus.MATCHED]
        unmatched_pairs = [p for p in pairs if p.pair_status != PairStatus.MATCHED]

        is_ready = bool(quality and quality.is_clean_comparison and len(matched_pairs) > 0)

        return {
            "comparison_id": comparison_id,
            "v0_experiment_id": comp_record.v0_experiment_id,
            "v1_experiment_id": comp_record.v1_experiment_id,
            "device_serial": comp_record.device.serial,
            "device_model": f"{comp_record.device.manufacturer or ''} {comp_record.device.model or ''}".strip(),
            "v0_version": comp_record.v0_software.version_name,
            "v1_version": comp_record.v1_software.version_name,
            "total_pairs": len(pairs),
            "matched_pairs": len(matched_pairs),
            "unmatched_pairs": len(unmatched_pairs),
            "is_clean_comparison": quality.is_clean_comparison if quality else False,
            "comparison_verdict": quality.summary_verdict if quality else "UNKNOWN",
            "is_ready_for_stats": is_ready,
        }

    def _extract_metric_values_for_run(
        self,
        run: WorkloadRun,
        telemetry: List[TelemetryRecord],
        metric_name: str,
    ) -> Optional[float]:
        """Extract a single numeric observation for a metric from a specific workload run and its telemetry."""
        # 1. Universal duration
        if metric_name == "workload_duration_ms":
            return round(run.duration_ms, 3)

        # 2. startup_01
        elif metric_name == "startup_duration_ms":
            tel = [
                t for t in telemetry
                if t.workload.iteration == run.iteration and t.metric.name == "app_startup_duration_ms"
                and isinstance(t.metric.value, (int, float))
            ]
            if tel:
                return float(tel[0].metric.value)
            launch_step = next((s for s in run.steps if s.action.value == "launch_app"), None)
            if launch_step:
                return round(launch_step.duration_ms, 3)

        # 3. cpu_01
        elif metric_name == "compute_duration_ms":
            step = next((s for s in run.steps if s.action.value == "compute_work"), None)
            if step:
                return round(step.duration_ms, 3)

        # 4. memory_01
        elif metric_name == "app_heap_allocated_mb":
            tel = [
                float(t.metric.value) for t in telemetry
                if t.workload.iteration == run.iteration and t.metric.name == "app_heap_allocated_mb"
                and isinstance(t.metric.value, (int, float))
            ]
            if tel:
                return round(statistics.mean(tel), 3)

        elif metric_name == "device_memory_available_mb":
            tel = [
                float(t.metric.value) for t in telemetry
                if t.workload.iteration == run.iteration and t.metric.name == "device_memory_available_mb"
                and isinstance(t.metric.value, (int, float))
            ]
            if tel:
                return round(statistics.mean(tel), 3)

        # 5. scroll_01
        elif metric_name == "scroll_duration_ms":
            step = next((s for s in run.steps if s.action.value == "scroll"), None)
            if step:
                return round(step.duration_ms, 3)

        elif metric_name == "ui_frame_jank_percent":
            tel = [
                float(t.metric.value) for t in telemetry
                if t.workload.iteration == run.iteration and t.metric.name == "ui_frame_jank_percent"
                and isinstance(t.metric.value, (int, float))
            ]
            if tel:
                return round(statistics.mean(tel), 3)

        # 6. video_power_01
        elif metric_name == "playback_duration_ms":
            step = next((s for s in run.steps if s.action.value == "local_media_playback"), None)
            if step:
                return round(step.duration_ms, 3)

        elif metric_name == "battery_discharge_proxy":
            matching_bat = [
                float(t.metric.value) for t in telemetry
                if t.workload.iteration == run.iteration and t.metric.name == "battery_level_percent"
                and isinstance(t.metric.value, (int, float))
            ]
            if len(matching_bat) >= 2:
                return round(matching_bat[0] - matching_bat[-1], 3)
            elif len(matching_bat) == 1:
                return 0.0

        return None

    def analyze_comparison(
        self,
        comparison_id: str,
        alpha: float = 0.05,
        multiple_comparison_policy: str = "none",
        random_seed: int = 42,
    ) -> StatisticalAnalysisRecord:
        """Execute deterministic statistical analysis across all eligible metrics."""
        # 1. Inspect comparison readiness
        inspection = self.inspect_comparison(comparison_id)
        if not inspection["is_ready_for_stats"]:
            raise HexnilError(
                f"Comparison '{comparison_id}' is not ready for statistical analysis (clean: {inspection['is_clean_comparison']}, verdict: {inspection['comparison_verdict']}).",
                suggestion="Run a clean differential comparison via 'python -m hexnil diff run' before analyzing.",
            )

        comp_record = self.comp_store.load_comparison(comparison_id)
        all_pairs = self.comp_store.load_comparison_pairs(comparison_id)

        # 2. Exclude invalid or unmatched pairs
        valid_matched_pairs = [p for p in all_pairs if p.pair_status == PairStatus.MATCHED]
        exclusions: List[Dict[str, Any]] = [
            {
                "workload_id": p.workload_id,
                "iteration": p.iteration,
                "pair_status": p.pair_status.value,
                "reason": p.mismatch_reason or "Unmatched run pair excluded from statistical analysis",
            }
            for p in all_pairs if p.pair_status != PairStatus.MATCHED
        ]

        # 3. Load V0 and V1 workload runs and telemetry
        v0_runs = {r.run_id: r for r in self.exp_store.list_workload_runs(comp_record.v0_experiment_id)}
        v1_runs = {r.run_id: r for r in self.exp_store.list_workload_runs(comp_record.v1_experiment_id)}

        v0_telemetry = self.exp_store.load_telemetry(comp_record.v0_experiment_id)
        v1_telemetry = self.exp_store.load_telemetry(comp_record.v1_experiment_id)

        # 4. Group matched pairs by workload_id
        workload_pairs: Dict[str, List[Any]] = {}
        for p in valid_matched_pairs:
            workload_pairs.setdefault(p.workload_id, []).append(p)

        metric_results: List[MetricComparison] = []
        test_results_for_adjustment: List[Tuple[int, Any]] = []

        # 5. Evaluate all registered metrics per workload
        for w_id in comp_record.workload_suite:
            pairs_for_w = workload_pairs.get(w_id, [])
            registered_metrics = get_registered_metrics_for_workload(w_id)

            for meta in registered_metrics:
                m_name = meta.metric_name
                direction = meta.direction
                unit = meta.unit
                threshold = get_threshold_for_metric(m_name)

                # Extract paired observations
                v0_vals: List[float] = []
                v1_vals: List[float] = []
                v0_ids: List[str] = []
                v1_ids: List[str] = []

                for pair in pairs_for_w:
                    r0 = v0_runs.get(pair.v0_run_id)
                    r1 = v1_runs.get(pair.v1_run_id)
                    if not r0 or not r1:
                        continue

                    val0 = self._extract_metric_values_for_run(r0, v0_telemetry, m_name)
                    val1 = self._extract_metric_values_for_run(r1, v1_telemetry, m_name)

                    if val0 is not None and val1 is not None:
                        v0_vals.append(val0)
                        v1_vals.append(val1)
                        v0_ids.append(r0.run_id)
                        v1_ids.append(r1.run_id)

                sample_count = len(v0_vals)

                # Determine eligibility
                if sample_count == 0:
                    eligibility = MetricEligibility.UNSUPPORTED
                    verdict = Verdict.INCONCLUSIVE
                    sev = Severity.NONE
                    reason = f"No valid observations found for metric '{m_name}'."

                    comp_item = MetricComparison(
                        comparison_id=comparison_id,
                        workload_id=w_id,
                        metric_name=m_name,
                        metric_unit=unit,
                        direction=direction,
                        eligibility=eligibility,
                        sample_count=0,
                        threshold=threshold,
                        verdict=verdict,
                        severity=sev,
                        verdict_reason=reason,
                        status="UNSUPPORTED",
                    )
                    metric_results.append(comp_item)
                    continue

                if sample_count < 3:
                    eligibility = MetricEligibility.INSUFFICIENT_DATA
                    verdict = Verdict.INCONCLUSIVE
                    sev = Severity.NONE
                    reason = f"Sample count (n={sample_count}) is below minimum requirement (n=3)."

                    comp_item = MetricComparison(
                        comparison_id=comparison_id,
                        workload_id=w_id,
                        metric_name=m_name,
                        metric_unit=unit,
                        direction=direction,
                        eligibility=eligibility,
                        sample_count=sample_count,
                        v0_run_ids=v0_ids,
                        v1_run_ids=v1_ids,
                        v0_values=v0_vals,
                        v1_values=v1_vals,
                        threshold=threshold,
                        verdict=verdict,
                        severity=sev,
                        verdict_reason=reason,
                        status="INCONCLUSIVE",
                    )
                    metric_results.append(comp_item)
                    continue

                # Metric is eligible
                eligibility = MetricEligibility.SUPPORTED_AND_ELIGIBLE
                paired_diffs = compute_paired_differences(v0_vals, v1_vals)
                v0_mean = round(statistics.mean(v0_vals), 3)
                v1_mean = round(statistics.mean(v1_vals), 3)
                v0_med = round(statistics.median(v0_vals), 3)
                v1_med = round(statistics.median(v1_vals), 3)
                abs_delta = compute_absolute_delta(v0_vals, v1_vals)
                pct_delta = compute_percentage_delta(v0_vals, v1_vals)
                cohen_d = compute_cohens_d_paired(paired_diffs)

                ci = compute_paired_confidence_interval(paired_diffs, confidence_level=0.95)
                test_res = perform_paired_t_test(v0_vals, v1_vals, alpha=alpha)

                # Classify verdict and severity
                verdict, sev, reason = classify_verdict_and_severity(
                    direction=direction,
                    eligibility=eligibility,
                    absolute_delta=abs_delta,
                    percent_delta=pct_delta,
                    threshold=threshold,
                    confidence_interval=ci,
                    statistical_test=test_res,
                    sample_count=sample_count,
                )

                item_idx = len(metric_results)
                test_results_for_adjustment.append((item_idx, test_res))

                comp_item = MetricComparison(
                    comparison_id=comparison_id,
                    workload_id=w_id,
                    metric_name=m_name,
                    metric_unit=unit,
                    direction=direction,
                    eligibility=eligibility,
                    sample_count=sample_count,
                    v0_run_ids=v0_ids,
                    v1_run_ids=v1_ids,
                    v0_values=v0_vals,
                    v1_values=v1_vals,
                    paired_differences=paired_diffs,
                    v0_mean=v0_mean,
                    v1_mean=v1_mean,
                    v0_median=v0_med,
                    v1_median=v1_med,
                    absolute_delta=abs_delta,
                    percent_delta=pct_delta,
                    effect_size=cohen_d,
                    confidence_interval=ci,
                    statistical_test=test_res,
                    threshold=threshold,
                    verdict=verdict,
                    severity=sev,
                    verdict_reason=reason,
                    status="VALID",
                )
                metric_results.append(comp_item)

        # 6. Apply multiple comparison adjustments if requested
        if multiple_comparison_policy.lower() != "none" and test_results_for_adjustment:
            raw_tests = [t for _, t in test_results_for_adjustment]
            adjusted = adjust_p_values(raw_tests, method=multiple_comparison_policy)
            for (idx, _), adj_test in zip(test_results_for_adjustment, adjusted):
                metric_results[idx].statistical_test = adj_test

        # 7. Build Quality Report
        eligible_count = sum(1 for m in metric_results if m.eligibility == MetricEligibility.SUPPORTED_AND_ELIGIBLE)
        inconclusive_count = sum(1 for m in metric_results if m.verdict == Verdict.INCONCLUSIVE)
        invalid_count = sum(1 for m in metric_results if m.verdict == Verdict.INVALID)
        unsupported_count = sum(1 for m in metric_results if m.eligibility == MetricEligibility.UNSUPPORTED)

        coverage_str = f"{eligible_count}/{len(metric_results)} claims/metrics with sufficient measured evidence"

        verdicts_summary: Dict[str, int] = {}
        for m in metric_results:
            verdicts_summary[m.verdict.value] = verdicts_summary.get(m.verdict.value, 0) + 1

        severity_summary: Dict[str, int] = {}
        for m in metric_results:
            if m.severity != Severity.NONE:
                severity_summary[m.severity.value] = severity_summary.get(m.severity.value, 0) + 1

        # Preserve environmental confounders
        confounders: List[str] = []
        if comp_record.environment_comparison:
            env_comp = comp_record.environment_comparison
            if env_comp.battery_level_delta_percent is not None and abs(env_comp.battery_level_delta_percent) > 5.0:
                confounders.append(f"Battery level drifted by {env_comp.battery_level_delta_percent:.1f}%")
            if env_comp.thermal_status_transition not in ("UNKNOWN -> UNKNOWN", "NONE -> NONE"):
                confounders.append(f"Thermal status transition: {env_comp.thermal_status_transition}")
            for d in env_comp.drift_summary:
                if d not in confounders:
                    confounders.append(d)

        quality_report = StatisticalQualityReport(
            analysis_id=f"STATS-{comparison_id}",
            comparison_id=comparison_id,
            metrics_analyzed=len(metric_results),
            metrics_eligible=eligible_count,
            metrics_inconclusive=inconclusive_count,
            metrics_invalid=invalid_count,
            metrics_unsupported=unsupported_count,
            evidence_coverage=coverage_str,
            environment_confounders=confounders,
            verdicts_summary=verdicts_summary,
            severity_summary=severity_summary,
            summary_verdict="COMPLETED",
        )

        # 8. Assemble Master Record
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        analysis_record = StatisticalAnalysisRecord(
            analysis_id=f"STATS-{comparison_id}",
            phase="06_statistical_comparison",
            comparison_id=comparison_id,
            created_at=now_iso,
            analysis_version="1.0.0",
            threshold_version=CURRENT_THRESHOLD_VERSION,
            multiple_comparison_policy=multiple_comparison_policy.upper(),
            random_seed=random_seed,
            metric_results=metric_results,
            quality=quality_report,
            exclusions=exclusions,
            provenance={
                "v0_experiment_id": comp_record.v0_experiment_id,
                "v1_experiment_id": comp_record.v1_experiment_id,
                "device_serial": comp_record.device.serial,
                "build_fingerprint": comp_record.device.build_fingerprint,
                "v0_apk_sha256": comp_record.v0_software.apk_sha256,
                "v1_apk_sha256": comp_record.v1_software.apk_sha256,
            },
        )

        # 9. Persist Analysis Record
        self.stats_store.save_analysis(analysis_record)
        return analysis_record
