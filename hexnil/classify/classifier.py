"""Issue classification logic: cross-references pre-update anomalies with post-update statistical verdicts."""

import datetime
import logging
from typing import Dict, List, Optional, Set

from hexnil.classify.models import (
    IssueCategory,
    IssueClassification,
    IssueReport,
)
from hexnil.monitor.models import PreUpdateAnomaly, PreUpdateAnomalyReport
from hexnil.stats.models import (
    MetricComparison,
    MetricEligibility,
    Severity,
    StatisticalAnalysisRecord,
    Verdict,
)

logger = logging.getLogger("hexnil.classify.classifier")


class IssueClassifier:
    """Cross-references pre-update anomalies with post-update verdicts to classify issues."""

    def classify(
        self,
        session_id: str,
        comparison_id: str,
        device_serial: str,
        v0_build_id: str,
        v1_build_id: str,
        analysis: StatisticalAnalysisRecord,
        anomaly_report: Optional[PreUpdateAnomalyReport] = None,
    ) -> IssueReport:
        """Classify all metrics from the statistical analysis against pre-update anomalies."""
        # Build anomaly lookup by metric name
        anomaly_by_metric: Dict[str, PreUpdateAnomaly] = {}
        if anomaly_report:
            for anomaly in anomaly_report.anomalies:
                # Map to the metric name used in statistical analysis
                mapped_name = self._map_anomaly_to_metric(anomaly.metric_name)
                if mapped_name and mapped_name not in anomaly_by_metric:
                    anomaly_by_metric[mapped_name] = anomaly

        classifications: List[IssueClassification] = []
        counts = {
            "fixed": 0,
            "persisted": 0,
            "new_regression": 0,
            "new_improvement": 0,
            "unchanged": 0,
            "insufficient_evidence": 0,
        }

        for metric in analysis.metric_results:
            anomaly = anomaly_by_metric.get(metric.metric_name)
            pre_anomaly_existed = anomaly is not None

            category = self._classify_single(
                metric=metric,
                pre_anomaly_existed=pre_anomaly_existed,
            )

            explanation = self._build_explanation(
                category=category,
                metric=metric,
                anomaly=anomaly,
            )

            confidence = self._compute_confidence(metric, category)

            classification = IssueClassification(
                classification_id=f"CLS-{metric.workload_id}-{metric.metric_name}",
                workload_id=metric.workload_id,
                metric_name=metric.metric_name,
                category=category,
                pre_update_anomaly_existed=pre_anomaly_existed,
                pre_update_anomaly_id=anomaly.anomaly_id if anomaly else None,
                pre_update_anomaly_description=anomaly.description if anomaly else None,
                post_update_verdict=metric.verdict.value,
                post_update_severity=metric.severity.value,
                absolute_delta=metric.absolute_delta,
                percent_delta=metric.percent_delta,
                effect_size=metric.effect_size,
                explanation=explanation,
                confidence=confidence,
            )
            classifications.append(classification)

            # Count by category
            if category == IssueCategory.FIXED:
                counts["fixed"] += 1
            elif category in (IssueCategory.PERSISTED, IssueCategory.PERSISTED_WORSENED):
                counts["persisted"] += 1
            elif category == IssueCategory.NEW_REGRESSION:
                counts["new_regression"] += 1
            elif category == IssueCategory.NEW_IMPROVEMENT:
                counts["new_improvement"] += 1
            elif category == IssueCategory.UNCHANGED:
                counts["unchanged"] += 1
            elif category == IssueCategory.INSUFFICIENT_EVIDENCE:
                counts["insufficient_evidence"] += 1

        # Build overall assessment
        overall = self._build_overall_assessment(counts)

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        return IssueReport(
            session_id=session_id,
            comparison_id=comparison_id,
            device_serial=device_serial,
            v0_build_id=v0_build_id,
            v1_build_id=v1_build_id,
            classifications=classifications,
            fixed_count=counts["fixed"],
            persisted_count=counts["persisted"],
            new_regression_count=counts["new_regression"],
            new_improvement_count=counts["new_improvement"],
            unchanged_count=counts["unchanged"],
            insufficient_evidence_count=counts["insufficient_evidence"],
            overall_assessment=overall,
            created_at=now_iso,
        )

    def _classify_single(
        self,
        metric: MetricComparison,
        pre_anomaly_existed: bool,
    ) -> IssueCategory:
        """Classify a single metric based on pre-update anomaly and post-update verdict."""
        verdict = metric.verdict
        eligibility = metric.eligibility

        # Insufficient evidence cases
        if verdict == Verdict.INCONCLUSIVE or verdict == Verdict.INVALID:
            return IssueCategory.INSUFFICIENT_EVIDENCE
        if eligibility == MetricEligibility.UNSUPPORTED:
            return IssueCategory.INSUFFICIENT_EVIDENCE
        if eligibility == MetricEligibility.INSUFFICIENT_DATA:
            return IssueCategory.INSUFFICIENT_EVIDENCE

        # Cross-reference anomaly with verdict
        if pre_anomaly_existed:
            if verdict == Verdict.IMPROVEMENT:
                return IssueCategory.FIXED
            elif verdict == Verdict.REGRESSION:
                return IssueCategory.PERSISTED_WORSENED
            elif verdict == Verdict.UNCHANGED:
                return IssueCategory.PERSISTED
        else:
            if verdict == Verdict.REGRESSION:
                return IssueCategory.NEW_REGRESSION
            elif verdict == Verdict.IMPROVEMENT:
                return IssueCategory.NEW_IMPROVEMENT
            elif verdict == Verdict.UNCHANGED:
                return IssueCategory.UNCHANGED

        return IssueCategory.INSUFFICIENT_EVIDENCE

    def _map_anomaly_to_metric(self, anomaly_metric_name: str) -> Optional[str]:
        """Map anomaly detector metric names to statistical analysis metric names."""
        mapping = {
            "battery_level_percent": "battery_discharge_proxy",
            "battery_drain_rate": "battery_discharge_proxy",
            "cpu_temperature_celsius": "compute_duration_ms",
            "thermal_status": "compute_duration_ms",
            "jank_percent": "ui_frame_jank_percent",
            "memory_available_mb": "device_memory_available_mb",
            "app_heap_mb": "app_heap_allocated_mb",
        }
        return mapping.get(anomaly_metric_name, anomaly_metric_name)

    def _build_explanation(
        self,
        category: IssueCategory,
        metric: MetricComparison,
        anomaly: Optional[PreUpdateAnomaly],
    ) -> str:
        """Build a human-readable explanation for the classification."""
        parts: List[str] = []

        if category == IssueCategory.FIXED:
            parts.append(
                f"Pre-update anomaly '{anomaly.description}' has been resolved. "
                f"Post-update verdict: {metric.verdict.value} "
                f"(Δ={metric.percent_delta:+.1f}% {'improvement' if metric.verdict == Verdict.IMPROVEMENT else ''})."
            )
        elif category == IssueCategory.PERSISTED:
            parts.append(
                f"Pre-update anomaly '{anomaly.description}' persists after update. "
                f"Post-update verdict: {metric.verdict.value} (no significant change)."
            )
        elif category == IssueCategory.PERSISTED_WORSENED:
            parts.append(
                f"Pre-update anomaly '{anomaly.description}' has WORSENED after update. "
                f"Post-update regression: Δ={metric.percent_delta:+.1f}%, severity={metric.severity.value}."
            )
        elif category == IssueCategory.NEW_REGRESSION:
            parts.append(
                f"NEW regression introduced by update on {metric.metric_name}: "
                f"Δ={metric.percent_delta:+.1f}%, effect size={metric.effect_size:.2f}, "
                f"severity={metric.severity.value}."
            )
        elif category == IssueCategory.NEW_IMPROVEMENT:
            parts.append(
                f"Unexpected improvement on {metric.metric_name}: "
                f"Δ={metric.percent_delta:+.1f}%."
            )
        elif category == IssueCategory.UNCHANGED:
            parts.append(
                f"No significant change in {metric.metric_name} after update."
            )
        elif category == IssueCategory.INSUFFICIENT_EVIDENCE:
            parts.append(
                f"Insufficient evidence to classify {metric.metric_name} "
                f"(verdict={metric.verdict.value}, eligibility={metric.eligibility.value})."
            )

        return " ".join(parts)

    def _compute_confidence(
        self, metric: MetricComparison, category: IssueCategory
    ) -> float:
        """Compute classification confidence based on statistical strength."""
        if category == IssueCategory.INSUFFICIENT_EVIDENCE:
            return 0.0

        if category == IssueCategory.UNCHANGED:
            return 0.7 if metric.sample_count >= 3 else 0.4

        # For directional verdicts, use p-value and effect size
        base = 0.5
        if metric.statistical_test and metric.statistical_test.p_value is not None:
            if metric.statistical_test.p_value < 0.01:
                base += 0.3
            elif metric.statistical_test.p_value < 0.05:
                base += 0.2
            elif metric.statistical_test.p_value < 0.10:
                base += 0.1

        if metric.effect_size is not None:
            if abs(metric.effect_size) >= 0.8:
                base += 0.15
            elif abs(metric.effect_size) >= 0.5:
                base += 0.1

        return min(1.0, round(base, 2))

    def _build_overall_assessment(self, counts: Dict[str, int]) -> str:
        """Build the overall assessment string."""
        total = sum(counts.values())
        parts: List[str] = []

        if counts["new_regression"] > 0:
            parts.append(
                f"⚠ {counts['new_regression']} NEW REGRESSION(S) introduced by this update."
            )
        if counts["fixed"] > 0:
            parts.append(
                f"✓ {counts['fixed']} pre-existing issue(s) FIXED by this update."
            )
        if counts["persisted"] > 0:
            parts.append(
                f"→ {counts['persisted']} pre-existing issue(s) PERSISTED after update."
            )
        if counts["new_improvement"] > 0:
            parts.append(
                f"↑ {counts['new_improvement']} unexpected improvement(s) detected."
            )
        if counts["unchanged"] > 0:
            parts.append(f"= {counts['unchanged']} metric(s) UNCHANGED.")
        if counts["insufficient_evidence"] > 0:
            parts.append(
                f"? {counts['insufficient_evidence']} metric(s) with INSUFFICIENT EVIDENCE."
            )

        if not parts:
            return f"No classifications produced from {total} metrics."

        return " ".join(parts)
