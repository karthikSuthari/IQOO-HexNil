"""Pre-update anomaly detection from continuous monitoring samples."""

import datetime
import logging
import statistics
from typing import Dict, List, Optional, Tuple

from hexnil.monitor.models import (
    AnomalyType,
    MonitoringSample,
    PreUpdateAnomaly,
    PreUpdateAnomalyReport,
)

logger = logging.getLogger("hexnil.monitor.anomaly_detector")

# Metric-to-anomaly-type mapping
METRIC_ANOMALY_MAP: Dict[str, AnomalyType] = {
    "battery_level_percent": AnomalyType.BATTERY_DRAIN,
    "thermal_status": AnomalyType.THERMAL_THROTTLE,
    "cpu_temperature_celsius": AnomalyType.THERMAL_THROTTLE,
    "jank_percent": AnomalyType.JANK_SPIKE,
    "memory_available_mb": AnomalyType.MEMORY_LEAK,
    "app_heap_mb": AnomalyType.MEMORY_LEAK,
}

# Z-score threshold for anomaly detection
DEFAULT_Z_THRESHOLD = 2.5

# Minimum samples required for meaningful anomaly detection
MIN_SAMPLES_FOR_DETECTION = 5


class AnomalyDetector:
    """Detects pre-update anomalies from continuous monitoring samples using z-score analysis."""

    def __init__(self, z_threshold: float = DEFAULT_Z_THRESHOLD):
        self.z_threshold = z_threshold

    def _extract_metric_series(
        self, samples: List[MonitoringSample], metric_name: str
    ) -> List[Tuple[int, float]]:
        """Extract a (sample_index, value) time series for a specific metric."""
        series: List[Tuple[int, float]] = []
        for s in samples:
            val = getattr(s, metric_name, None)
            if val is None and metric_name in s.raw_metrics:
                val = s.raw_metrics[metric_name]
            if val is not None and isinstance(val, (int, float)):
                series.append((s.sample_index, float(val)))
        return series

    def _detect_z_score_anomalies(
        self,
        series: List[Tuple[int, float]],
        metric_name: str,
        anomaly_type: AnomalyType,
    ) -> List[PreUpdateAnomaly]:
        """Detect anomalies using z-score deviation from the running mean."""
        if len(series) < MIN_SAMPLES_FOR_DETECTION:
            return []

        values = [v for _, v in series]
        mean_val = statistics.mean(values)
        stdev_val = statistics.stdev(values) if len(values) > 1 else 0.0

        if stdev_val == 0.0:
            return []

        anomalies: List[PreUpdateAnomaly] = []
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        for idx, val in series:
            z = abs(val - mean_val) / stdev_val
            if z >= self.z_threshold:
                severity = "LOW"
                if z >= 4.0:
                    severity = "HIGH"
                elif z >= 3.0:
                    severity = "MEDIUM"

                anomaly = PreUpdateAnomaly(
                    anomaly_id=f"ANOM-{metric_name}-{idx}",
                    anomaly_type=anomaly_type,
                    metric_name=metric_name,
                    description=(
                        f"Anomalous {metric_name} value {val:.2f} at sample {idx} "
                        f"(z-score: {z:.2f}, baseline mean: {mean_val:.2f} ± {stdev_val:.2f})"
                    ),
                    severity=severity,
                    detected_at=now_iso,
                    sample_indices=[idx],
                    baseline_value=round(mean_val, 3),
                    observed_value=round(val, 3),
                    z_score=round(z, 3),
                )
                anomalies.append(anomaly)

        return anomalies

    def _detect_battery_drain(
        self, samples: List[MonitoringSample]
    ) -> List[PreUpdateAnomaly]:
        """Detect abnormal battery drain rate from monotonically decreasing battery levels."""
        series = self._extract_metric_series(samples, "battery_level_percent")
        if len(series) < MIN_SAMPLES_FOR_DETECTION:
            return []

        # Calculate discharge rate between consecutive samples
        drain_rates: List[Tuple[int, float]] = []
        for i in range(1, len(series)):
            prev_idx, prev_val = series[i - 1]
            curr_idx, curr_val = series[i]
            drain = prev_val - curr_val  # Positive means discharge
            if drain > 0:
                drain_rates.append((curr_idx, drain))

        if not drain_rates:
            return []

        return self._detect_z_score_anomalies(
            drain_rates, "battery_drain_rate", AnomalyType.BATTERY_DRAIN
        )

    def _detect_memory_trend(
        self, samples: List[MonitoringSample]
    ) -> List[PreUpdateAnomaly]:
        """Detect monotonic memory consumption increase (potential leak)."""
        series = self._extract_metric_series(samples, "app_heap_mb")
        if len(series) < MIN_SAMPLES_FOR_DETECTION:
            return []

        values = [v for _, v in series]
        # Check if memory is monotonically increasing over a window
        window_size = min(10, len(values))
        if window_size < 5:
            return []

        last_window = values[-window_size:]
        increasing_count = sum(
            1 for i in range(1, len(last_window)) if last_window[i] > last_window[i - 1]
        )

        anomalies: List[PreUpdateAnomaly] = []
        if increasing_count >= window_size * 0.8:
            now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
            start_val = last_window[0]
            end_val = last_window[-1]
            growth = end_val - start_val

            anomalies.append(
                PreUpdateAnomaly(
                    anomaly_id=f"ANOM-memory_trend-{series[-1][0]}",
                    anomaly_type=AnomalyType.MEMORY_LEAK,
                    metric_name="app_heap_mb",
                    description=(
                        f"Monotonic memory increase detected: {start_val:.1f} MB → {end_val:.1f} MB "
                        f"(+{growth:.1f} MB over {window_size} samples, "
                        f"{increasing_count}/{window_size - 1} consecutive increases)"
                    ),
                    severity="MEDIUM" if growth > 20 else "LOW",
                    detected_at=now_iso,
                    sample_indices=[s[0] for s in series[-window_size:]],
                    baseline_value=round(start_val, 3),
                    observed_value=round(end_val, 3),
                )
            )

        return anomalies

    def analyze(
        self,
        session_id: str,
        device_serial: str,
        samples: List[MonitoringSample],
    ) -> PreUpdateAnomalyReport:
        """Run full pre-update anomaly analysis on collected monitoring samples."""
        all_anomalies: List[PreUpdateAnomaly] = []

        # 1. Z-score analysis on each monitored metric
        for metric_name, anomaly_type in METRIC_ANOMALY_MAP.items():
            series = self._extract_metric_series(samples, metric_name)
            anomalies = self._detect_z_score_anomalies(series, metric_name, anomaly_type)
            all_anomalies.extend(anomalies)

        # 2. Battery drain rate analysis
        all_anomalies.extend(self._detect_battery_drain(samples))

        # 3. Memory trend analysis
        all_anomalies.extend(self._detect_memory_trend(samples))

        # Compute monitoring duration
        duration = 0.0
        if len(samples) >= 2:
            try:
                t0 = datetime.datetime.fromisoformat(samples[0].timestamp)
                t1 = datetime.datetime.fromisoformat(samples[-1].timestamp)
                duration = (t1 - t0).total_seconds()
            except (ValueError, TypeError):
                pass

        has_issues = len(all_anomalies) > 0
        summary_parts: List[str] = []
        if has_issues:
            by_type: Dict[str, int] = {}
            for a in all_anomalies:
                by_type[a.anomaly_type.value] = by_type.get(a.anomaly_type.value, 0) + 1
            summary_parts.append(
                f"{len(all_anomalies)} pre-update anomaly(ies) detected: "
                + ", ".join(f"{k}={v}" for k, v in sorted(by_type.items()))
            )
        else:
            summary_parts.append(
                f"No anomalies detected in {len(samples)} monitoring samples."
            )

        logger.info(
            "Anomaly analysis for session %s: %d anomalies from %d samples",
            session_id,
            len(all_anomalies),
            len(samples),
        )

        return PreUpdateAnomalyReport(
            session_id=session_id,
            device_serial=device_serial,
            monitoring_duration_seconds=duration,
            total_samples=len(samples),
            anomalies=all_anomalies,
            has_pre_existing_issues=has_issues,
            summary="; ".join(summary_parts),
        )
