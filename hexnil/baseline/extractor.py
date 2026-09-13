"""Baseline metric extraction and statistical analysis layer."""

import logging
import math
import statistics
from typing import Dict, List, Optional, Tuple

from hexnil.baseline.models import (
    BaselineMetricSummary,
    UncertaintyEstimate,
)
from hexnil.telemetry.models import TelemetryRecord
from hexnil.workloads.models import RunStatus, WorkloadRun

logger = logging.getLogger("hexnil.baseline.extractor")

# Student's t critical values for two-tailed 95% confidence interval (alpha=0.05)
STUDENT_T_95_TABLE = {
    1: 12.706,
    2: 4.303,
    3: 3.182,
    4: 2.776,
    5: 2.571,
    6: 2.447,
    7: 2.365,
    8: 2.306,
    9: 2.262,
    10: 2.228,
    11: 2.201,
    12: 2.179,
    13: 2.160,
    14: 2.145,
    15: 2.131,
    16: 2.120,
    17: 2.110,
    18: 2.101,
    19: 2.093,
    20: 2.086,
    25: 2.060,
    30: 2.042,
}


def get_t_critical_95(df: int) -> float:
    """Retrieve or approximate two-tailed Student's t critical value for alpha=0.05."""
    if df in STUDENT_T_95_TABLE:
        return STUDENT_T_95_TABLE[df]
    if df < 1:
        return 12.706
    if df > 30:
        return 1.960  # Asymptotic normal z-critical value

    # Interpolate for degrees of freedom between 20 and 30
    sorted_dfs = sorted(STUDENT_T_95_TABLE.keys())
    lower_df = max(d for d in sorted_dfs if d <= df)
    upper_df = min(d for d in sorted_dfs if d >= df)
    if lower_df == upper_df:
        return STUDENT_T_95_TABLE[lower_df]

    weight = (df - lower_df) / (upper_df - lower_df)
    return round(
        STUDENT_T_95_TABLE[lower_df] + weight * (STUDENT_T_95_TABLE[upper_df] - STUDENT_T_95_TABLE[lower_df]),
        3,
    )


def compute_percentiles(values: List[float]) -> Tuple[float, float, float]:
    """Compute 25th percentile, median, and 75th percentile."""
    if not values:
        return 0.0, 0.0, 0.0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    if n == 1:
        return sorted_vals[0], sorted_vals[0], sorted_vals[0]

    med = statistics.median(sorted_vals)

    # 25th and 75th percentile approximations
    def percentile(p: float) -> float:
        k = (n - 1) * p
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return sorted_vals[int(k)]
        d0 = sorted_vals[int(f)] * (c - k)
        d1 = sorted_vals[int(c)] * (k - f)
        return d0 + d1

    p25 = percentile(0.25)
    p75 = percentile(0.75)
    return round(p25, 3), round(med, 3), round(p75, 3)


def summarize_metric_values(
    workload_id: str,
    metric_name: str,
    values: List[float],
    unit: Optional[str] = None,
    n_excluded: int = 0,
) -> BaselineMetricSummary:
    """Compute complete descriptive statistics and detect outliers for a list of valid run values."""
    n = len(values)
    if n == 0:
        return BaselineMetricSummary(
            workload_id=workload_id,
            metric_name=metric_name,
            unit=unit,
            n_valid_runs=0,
            n_excluded_runs=n_excluded,
            run_values=[],
        )

    mean_val = round(statistics.mean(values), 3)
    p25, med_val, p75 = compute_percentiles(values)
    min_val = round(min(values), 3)
    max_val = round(max(values), 3)
    iqr_val = round(p75 - p25, 3)

    if n > 1:
        std_val = round(statistics.stdev(values), 3)
        var_val = round(statistics.variance(values), 3)
        cv_val = round(std_val / mean_val, 4) if mean_val != 0 else 0.0
    else:
        std_val = 0.0
        var_val = 0.0
        cv_val = 0.0

    # Non-destructive outlier detection using 1.5 * IQR rule
    outliers_count = 0
    if n >= 4 and iqr_val > 0:
        lower_bound = p25 - 1.5 * iqr_val
        upper_bound = p75 + 1.5 * iqr_val
        outliers_count = sum(1 for v in values if (v < lower_bound or v > upper_bound))

    return BaselineMetricSummary(
        workload_id=workload_id,
        metric_name=metric_name,
        unit=unit,
        n_valid_runs=n,
        n_excluded_runs=n_excluded,
        mean=mean_val,
        median=med_val,
        min=min_val,
        max=max_val,
        std_dev=std_val,
        variance=var_val,
        p25=p25,
        p75=p75,
        iqr=iqr_val,
        coefficient_of_variation=cv_val,
        run_values=[round(v, 3) for v in values],
        outliers_detected=outliers_count,
    )


def estimate_uncertainty(
    workload_id: str,
    metric_name: str,
    values: List[float],
    confidence_level: float = 0.95,
) -> UncertaintyEstimate:
    """Quantify baseline uncertainty using Student's t confidence interval or mark INCONCLUSIVE."""
    n = len(values)
    if n < 3:
        return UncertaintyEstimate(
            workload_id=workload_id,
            metric_name=metric_name,
            sample_size=n,
            confidence_level=confidence_level,
            method="inconclusive",
            uncertainty_status="INCONCLUSIVE",
            explanation=f"Sample size (n={n}) is insufficient (minimum 3 required) to estimate variability.",
        )

    std_val = statistics.stdev(values)
    if std_val == 0.0:
        return UncertaintyEstimate(
            workload_id=workload_id,
            metric_name=metric_name,
            sample_size=n,
            confidence_level=confidence_level,
            method="inconclusive",
            uncertainty_status="INCONCLUSIVE",
            explanation="Observed variance is zero across samples; confidence interval cannot be computed.",
        )

    se = std_val / math.sqrt(n)
    df = n - 1
    t_crit = get_t_critical_95(df)
    margin = t_crit * se
    mean_val = statistics.mean(values)

    return UncertaintyEstimate(
        workload_id=workload_id,
        metric_name=metric_name,
        sample_size=n,
        standard_error=round(se, 4),
        ci_lower=round(mean_val - margin, 3),
        ci_upper=round(mean_val + margin, 3),
        confidence_level=confidence_level,
        method="student_t",
        uncertainty_status="ESTIMATED",
    )


class BaselineMetricExtractor:
    """Extracts run-level measurements and computes statistical summaries from valid runs."""

    def extract_metrics(
        self,
        runs: List[WorkloadRun],
        telemetry_records: List[TelemetryRecord],
    ) -> Tuple[Dict[str, Dict[str, BaselineMetricSummary]], Dict[str, Dict[str, UncertaintyEstimate]]]:
        """Extract valid measurements and summarize across workloads."""
        summaries: Dict[str, Dict[str, BaselineMetricSummary]] = {}
        uncertainties: Dict[str, Dict[str, UncertaintyEstimate]] = {}

        # Group runs by workload_id
        workload_runs: Dict[str, List[WorkloadRun]] = {}
        for r in runs:
            workload_runs.setdefault(r.workload_id, []).append(r)

        for w_id, all_w_runs in workload_runs.items():
            valid_runs = [r for r in all_w_runs if r.status == RunStatus.SUCCESS]
            n_excluded = len(all_w_runs) - len(valid_runs)

            summaries[w_id] = {}
            uncertainties[w_id] = {}

            # Workload Duration (Universal for all workloads)
            durations = [r.duration_ms for r in valid_runs]
            if durations:
                s_dur = summarize_metric_values(w_id, "workload_duration_ms", durations, unit="ms", n_excluded=n_excluded)
                u_dur = estimate_uncertainty(w_id, "workload_duration_ms", durations)
                summaries[w_id]["workload_duration_ms"] = s_dur
                uncertainties[w_id]["workload_duration_ms"] = u_dur

            # Specific workload metric extractions
            if w_id == "startup_01":
                startup_times: List[float] = []
                for vr in valid_runs:
                    matching_tel = [
                        t for t in telemetry_records
                        if t.workload.iteration == vr.iteration and t.metric.name == "app_startup_duration_ms"
                    ]
                    if matching_tel and isinstance(matching_tel[0].metric.value, (int, float)):
                        startup_times.append(float(matching_tel[0].metric.value))
                    else:
                        # Step-level fallback if recorded
                        launch_step = next((s for s in vr.steps if s.action.value == "launch_app"), None)
                        if launch_step:
                            startup_times.append(launch_step.duration_ms)

                if startup_times:
                    summaries[w_id]["startup_duration_ms"] = summarize_metric_values(
                        w_id, "startup_duration_ms", startup_times, unit="ms", n_excluded=n_excluded
                    )
                    uncertainties[w_id]["startup_duration_ms"] = estimate_uncertainty(
                        w_id, "startup_duration_ms", startup_times
                    )

            elif w_id == "cpu_01":
                compute_durations: List[float] = []
                for vr in valid_runs:
                    compute_step = next((s for s in vr.steps if s.action.value == "compute_work"), None)
                    if compute_step:
                        compute_durations.append(compute_step.duration_ms)
                if compute_durations:
                    summaries[w_id]["compute_duration_ms"] = summarize_metric_values(
                        w_id, "compute_duration_ms", compute_durations, unit="ms", n_excluded=n_excluded
                    )
                    uncertainties[w_id]["compute_duration_ms"] = estimate_uncertainty(
                        w_id, "compute_duration_ms", compute_durations
                    )

            elif w_id == "memory_01":
                heap_vals: List[float] = []
                avail_mem_vals: List[float] = []
                for vr in valid_runs:
                    matching = [t for t in telemetry_records if t.workload.iteration == vr.iteration]
                    for t in matching:
                        if t.metric.name == "app_heap_allocated_mb" and isinstance(t.metric.value, (int, float)):
                            heap_vals.append(float(t.metric.value))
                        elif t.metric.name == "device_memory_available_mb" and isinstance(t.metric.value, (int, float)):
                            avail_mem_vals.append(float(t.metric.value))

                if heap_vals:
                    summaries[w_id]["app_heap_allocated_mb"] = summarize_metric_values(
                        w_id, "app_heap_allocated_mb", heap_vals, unit="MB", n_excluded=n_excluded
                    )
                    uncertainties[w_id]["app_heap_allocated_mb"] = estimate_uncertainty(
                        w_id, "app_heap_allocated_mb", heap_vals
                    )
                if avail_mem_vals:
                    summaries[w_id]["device_memory_available_mb"] = summarize_metric_values(
                        w_id, "device_memory_available_mb", avail_mem_vals, unit="MB", n_excluded=n_excluded
                    )
                    uncertainties[w_id]["device_memory_available_mb"] = estimate_uncertainty(
                        w_id, "device_memory_available_mb", avail_mem_vals
                    )

            elif w_id == "scroll_01":
                scroll_durations: List[float] = []
                for vr in valid_runs:
                    sc_step = next((s for s in vr.steps if s.action.value == "scroll"), None)
                    if sc_step:
                        scroll_durations.append(sc_step.duration_ms)
                if scroll_durations:
                    summaries[w_id]["scroll_duration_ms"] = summarize_metric_values(
                        w_id, "scroll_duration_ms", scroll_durations, unit="ms", n_excluded=n_excluded
                    )
                    uncertainties[w_id]["scroll_duration_ms"] = estimate_uncertainty(
                        w_id, "scroll_duration_ms", scroll_durations
                    )

                jank_rates: List[float] = []
                for vr in valid_runs:
                    matching = [
                        t for t in telemetry_records
                        if t.workload.iteration == vr.iteration and t.metric.name == "ui_frame_jank_percent"
                    ]
                    if matching and isinstance(matching[0].metric.value, (int, float)):
                        jank_rates.append(float(matching[0].metric.value))

                if jank_rates:
                    summaries[w_id]["ui_frame_jank_percent"] = summarize_metric_values(
                        w_id, "ui_frame_jank_percent", jank_rates, unit="%", n_excluded=n_excluded
                    )
                    uncertainties[w_id]["ui_frame_jank_percent"] = estimate_uncertainty(
                        w_id, "ui_frame_jank_percent", jank_rates
                    )

            elif w_id == "video_power_01":
                playback_durations: List[float] = []
                for vr in valid_runs:
                    pb_step = next((s for s in vr.steps if s.action.value == "local_media_playback"), None)
                    if pb_step:
                        playback_durations.append(pb_step.duration_ms)
                if playback_durations:
                    summaries[w_id]["playback_duration_ms"] = summarize_metric_values(
                        w_id, "playback_duration_ms", playback_durations, unit="ms", n_excluded=n_excluded
                    )
                    uncertainties[w_id]["playback_duration_ms"] = estimate_uncertainty(
                        w_id, "playback_duration_ms", playback_durations
                    )

                battery_deltas: List[float] = []
                for vr in valid_runs:
                    matching_bat = [
                        float(t.metric.value) for t in telemetry_records
                        if t.workload.iteration == vr.iteration and t.metric.name == "battery_level_percent"
                        and isinstance(t.metric.value, (int, float))
                    ]
                    if len(matching_bat) >= 2:
                        first_level = matching_bat[0]
                        last_level = matching_bat[-1]
                        battery_deltas.append(round(first_level - last_level, 2))
                    elif len(matching_bat) == 1:
                        battery_deltas.append(0.0)

                if battery_deltas:
                    summaries[w_id]["battery_level_delta_percent"] = summarize_metric_values(
                        w_id, "battery_level_delta_percent", battery_deltas, unit="%", n_excluded=n_excluded
                    )
                    uncertainties[w_id]["battery_level_delta_percent"] = estimate_uncertainty(
                        w_id, "battery_level_delta_percent", battery_deltas
                    )
                    # Discharge proxy explicitly documented as percent drop proxy, NOT energy
                    summaries[w_id]["battery_discharge_proxy"] = summarize_metric_values(
                        w_id, "battery_discharge_proxy", battery_deltas, unit="delta_percent_proxy", n_excluded=n_excluded
                    )
                    uncertainties[w_id]["battery_discharge_proxy"] = estimate_uncertainty(
                        w_id, "battery_discharge_proxy", battery_deltas
                    )

        return summaries, uncertainties

