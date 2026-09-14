"""Final evidence report assembly and formatting."""

import datetime
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from hexnil.classify.models import IssueCategory, IssueClassification, IssueReport
from hexnil.evaluate.models import PredictionEvaluationReport
from hexnil.monitor.models import (
    DeviceOsState,
    MonitoringSession,
    PreUpdateAnomalyReport,
    UpdateTransition,
)
from hexnil.predict.models import ValidationPlan
from hexnil.report.models import FinalEvidenceReport
from hexnil.stats.models import StatisticalAnalysisRecord

logger = logging.getLogger("hexnil.report.generator")


class ReportGenerator:
    """Assembles the FinalEvidenceReport from all upstream phase artifacts."""

    def generate(
        self,
        session: MonitoringSession,
        issue_report: Optional[IssueReport] = None,
        analysis: Optional[StatisticalAnalysisRecord] = None,
        plan: Optional[ValidationPlan] = None,
        prediction_evaluation: Optional[PredictionEvaluationReport] = None,
    ) -> FinalEvidenceReport:
        """Assemble the complete final evidence report."""
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        report_id = f"RPT-{session.session_id}"

        # Q1: Pre-update device state
        pre_state = session.v0_os_state
        if not pre_state:
            pre_state = DeviceOsState(
                build_fingerprint="unknown",
                build_id="unknown",
                android_version="unknown",
                captured_at=now_iso,
            )

        pre_summary = self._build_pre_update_summary(pre_state, session)

        # Q2: Pre-update anomalies
        anomaly_report = session.anomaly_report
        pre_anomalies: List[str] = []
        if anomaly_report and anomaly_report.has_pre_existing_issues:
            pre_anomalies = [a.description for a in anomaly_report.anomalies]

        # Q3: ML predictions
        ml_summary = ""
        risk_bands: Dict[str, str] = {}
        if plan:
            risk_bands = {
                p.claim_id: p.risk_band.value for p in plan.predictions
            }
            ml_summary = (
                f"{len(plan.predictions)} claim(s) analyzed via {plan.overall_path.value}. "
                f"Overall risk: {plan.overall_risk_band.value} (score={plan.overall_risk_score:.2f})."
            )

        # Q4: Update transition
        transition = session.update_transition
        update_desc = ""
        if transition:
            update_desc = (
                f"{transition.transition_type.value}: "
                + "; ".join(transition.changes[:5])
            )

        # Q5: Post-update changes
        post_state = session.v1_os_state
        post_changes: List[str] = []
        if analysis:
            for m in analysis.metric_results:
                if m.verdict.value in ("REGRESSION", "IMPROVEMENT"):
                    post_changes.append(
                        f"{m.workload_id}/{m.metric_name}: {m.verdict.value} "
                        f"(Δ={m.percent_delta:+.1f}%, severity={m.severity.value})"
                    )

        # Q6-Q9: Issue classifications
        fixed: List[IssueClassification] = []
        persisted: List[IssueClassification] = []
        new_regressions: List[IssueClassification] = []
        insufficient: List[IssueClassification] = []

        if issue_report:
            for cls in issue_report.classifications:
                if cls.category == IssueCategory.FIXED:
                    fixed.append(cls)
                elif cls.category in (IssueCategory.PERSISTED, IssueCategory.PERSISTED_WORSENED):
                    persisted.append(cls)
                elif cls.category == IssueCategory.NEW_REGRESSION:
                    new_regressions.append(cls)
                elif cls.category == IssueCategory.INSUFFICIENT_EVIDENCE:
                    insufficient.append(cls)

        # Q10: Prediction evaluation
        pred_accuracy_summary = ""
        if prediction_evaluation and prediction_evaluation.accuracy is not None:
            pred_accuracy_summary = (
                f"Prediction accuracy: {prediction_evaluation.accuracy:.1%} "
                f"({prediction_evaluation.true_positives + prediction_evaluation.true_negatives}"
                f"/{prediction_evaluation.evaluated_predictions} correct). "
                f"Quality: {prediction_evaluation.prediction_quality}."
            )

        # Overall verdict
        overall = self._compute_overall_verdict(
            fixed=fixed,
            persisted=persisted,
            new_regressions=new_regressions,
            insufficient=insufficient,
            analysis=analysis,
        )

        # Executive summary
        executive = self._build_executive_summary(
            session=session,
            transition=transition,
            fixed_count=len(fixed),
            persisted_count=len(persisted),
            regression_count=len(new_regressions),
            overall=overall,
        )

        # Recommendations
        recommendations = self._build_recommendations(
            new_regressions=new_regressions,
            persisted=persisted,
            insufficient=insufficient,
        )

        return FinalEvidenceReport(
            report_id=report_id,
            session_id=session.session_id,
            created_at=now_iso,
            device_serial=session.device_serial,
            device_model=session.device_model,
            pre_update_os_state=pre_state,
            pre_update_summary=pre_summary,
            pre_update_anomalies=pre_anomalies,
            anomaly_report=anomaly_report,
            ml_prediction_summary=ml_summary,
            predicted_risk_bands=risk_bands,
            prediction_plan_id=plan.plan_id if plan else None,
            update_transition=transition,
            update_description=update_desc,
            post_update_os_state=post_state,
            post_update_changes=post_changes,
            comparison_id=session.comparison_id,
            analysis_id=session.analysis_id,
            fixed_issues=fixed,
            persisted_issues=persisted,
            new_regressions=new_regressions,
            insufficient_evidence_items=insufficient,
            prediction_evaluation=prediction_evaluation,
            prediction_accuracy_summary=pred_accuracy_summary,
            issue_report=issue_report,
            overall_verdict=overall,
            executive_summary=executive,
            recommendations=recommendations,
        )

    def format_text(self, report: FinalEvidenceReport) -> str:
        """Format the final evidence report as human-readable text."""
        lines: List[str] = []
        lines.append("=" * 72)
        lines.append("HEXNIL — OS UPDATE IMPACT EVIDENCE REPORT")
        lines.append("=" * 72)
        lines.append(f"Report ID:    {report.report_id}")
        lines.append(f"Session ID:   {report.session_id}")
        lines.append(f"Device:       {report.device_model} ({report.device_serial})")
        lines.append(f"Generated:    {report.created_at}")
        lines.append("")

        lines.append("─" * 72)
        lines.append("Q1. WHAT WAS THE DEVICE LIKE BEFORE THE UPDATE?")
        lines.append("─" * 72)
        lines.append(report.pre_update_summary)
        lines.append("")

        lines.append("─" * 72)
        lines.append("Q2. WHAT PROBLEMS/ANOMALIES EXISTED BEFORE THE UPDATE?")
        lines.append("─" * 72)
        if report.pre_update_anomalies:
            for a in report.pre_update_anomalies:
                lines.append(f"  • {a}")
        else:
            lines.append("  No pre-update anomalies detected.")
        lines.append("")

        lines.append("─" * 72)
        lines.append("Q3. WHAT RISKS DID THE ML MODEL PREDICT?")
        lines.append("─" * 72)
        lines.append(f"  {report.ml_prediction_summary or 'No predictions available.'}")
        if report.predicted_risk_bands:
            for cid, band in report.predicted_risk_bands.items():
                lines.append(f"    {cid}: {band}")
        lines.append("")

        lines.append("─" * 72)
        lines.append("Q4. WHAT EXACT OS/SOFTWARE/SECURITY UPDATE OCCURRED?")
        lines.append("─" * 72)
        lines.append(f"  {report.update_description or 'No update transition recorded.'}")
        lines.append("")

        lines.append("─" * 72)
        lines.append("Q5. WHAT CHANGED AFTER THE UPDATE?")
        lines.append("─" * 72)
        if report.post_update_changes:
            for ch in report.post_update_changes:
                lines.append(f"  • {ch}")
        else:
            lines.append("  No significant metric changes detected.")
        lines.append("")

        lines.append("─" * 72)
        lines.append("Q6. DID THE UPDATE FIX AN EXISTING PROBLEM?")
        lines.append("─" * 72)
        if report.fixed_issues:
            for f in report.fixed_issues:
                lines.append(f"  ✓ {f.metric_name}: {f.explanation}")
        else:
            lines.append("  No pre-existing issues were fixed.")
        lines.append("")

        lines.append("─" * 72)
        lines.append("Q7. DID AN EXISTING PROBLEM REMAIN?")
        lines.append("─" * 72)
        if report.persisted_issues:
            for p in report.persisted_issues:
                lines.append(f"  → {p.metric_name}: {p.explanation}")
        else:
            lines.append("  No persisted issues.")
        lines.append("")

        lines.append("─" * 72)
        lines.append("Q8. DID THE UPDATE INTRODUCE A NEW REGRESSION?")
        lines.append("─" * 72)
        if report.new_regressions:
            for r in report.new_regressions:
                lines.append(f"  ⚠ {r.metric_name}: {r.explanation}")
        else:
            lines.append("  No new regressions introduced.")
        lines.append("")

        lines.append("─" * 72)
        lines.append("Q9. IS THERE INSUFFICIENT EVIDENCE?")
        lines.append("─" * 72)
        if report.insufficient_evidence_items:
            for ie in report.insufficient_evidence_items:
                lines.append(f"  ? {ie.metric_name}: {ie.explanation}")
        else:
            lines.append("  All metrics have sufficient evidence.")
        lines.append("")

        lines.append("─" * 72)
        lines.append("Q10. DID THE ML PREDICTION MATCH THE ACTUAL OUTCOME?")
        lines.append("─" * 72)
        lines.append(
            f"  {report.prediction_accuracy_summary or 'No prediction evaluation available.'}"
        )
        lines.append("")

        lines.append("=" * 72)
        lines.append(f"OVERALL VERDICT: {report.overall_verdict}")
        lines.append("=" * 72)
        lines.append(report.executive_summary)
        lines.append("")

        if report.recommendations:
            lines.append("RECOMMENDATIONS:")
            for rec in report.recommendations:
                lines.append(f"  • {rec}")

        lines.append("=" * 72)
        return "\n".join(lines)

    def _build_pre_update_summary(
        self, state: DeviceOsState, session: MonitoringSession
    ) -> str:
        parts = [
            f"Android {state.android_version}",
            f"Build: {state.build_id}",
            f"Fingerprint: {state.build_fingerprint}",
        ]
        if state.security_patch_level:
            parts.append(f"Security Patch: {state.security_patch_level}")
        return " | ".join(parts)

    def _compute_overall_verdict(
        self,
        fixed: List[IssueClassification],
        persisted: List[IssueClassification],
        new_regressions: List[IssueClassification],
        insufficient: List[IssueClassification],
        analysis: Optional[StatisticalAnalysisRecord],
    ) -> str:
        if new_regressions:
            has_critical = any(
                r.post_update_severity in ("CRITICAL", "HIGH") for r in new_regressions
            )
            if has_critical:
                return "CRITICAL_REGRESSIONS"
            return "UPDATE_HAS_REGRESSIONS"

        if fixed and not persisted:
            return "UPDATE_SAFE_WITH_FIXES"

        if persisted and not fixed:
            return "ISSUES_PERSIST"

        if fixed and persisted:
            return "MIXED_RESULTS"

        if not analysis or not analysis.metric_results:
            return "INSUFFICIENT_DATA"

        return "UPDATE_SAFE"

    def _build_executive_summary(
        self,
        session: MonitoringSession,
        transition: Optional[UpdateTransition],
        fixed_count: int,
        persisted_count: int,
        regression_count: int,
        overall: str,
    ) -> str:
        parts: List[str] = []
        parts.append(
            f"Device {session.device_model} ({session.device_serial}) was monitored "
            f"through an OS update lifecycle."
        )

        if transition:
            parts.append(
                f"Update type: {transition.transition_type.value} "
                f"({transition.v0_fingerprint[:40]}... → {transition.v1_fingerprint[:40]}...)."
            )

        if regression_count > 0:
            parts.append(f"{regression_count} new regression(s) were introduced.")
        if fixed_count > 0:
            parts.append(f"{fixed_count} pre-existing issue(s) were fixed.")
        if persisted_count > 0:
            parts.append(f"{persisted_count} pre-existing issue(s) persisted.")

        if overall == "UPDATE_SAFE":
            parts.append("The update appears SAFE with no detected regressions.")
        elif overall == "CRITICAL_REGRESSIONS":
            parts.append("CRITICAL regressions detected — update requires immediate attention.")

        return " ".join(parts)

    def _build_recommendations(
        self,
        new_regressions: List[IssueClassification],
        persisted: List[IssueClassification],
        insufficient: List[IssueClassification],
    ) -> List[str]:
        recs: List[str] = []

        if new_regressions:
            recs.append(
                f"Investigate {len(new_regressions)} new regression(s): "
                + ", ".join(r.metric_name for r in new_regressions[:5])
            )
            critical = [r for r in new_regressions if r.post_update_severity in ("CRITICAL", "HIGH")]
            if critical:
                recs.append(
                    f"URGENT: {len(critical)} high/critical severity regression(s) require immediate triage."
                )

        if persisted:
            recs.append(
                f"Monitor {len(persisted)} persisted issue(s) that the update did not resolve."
            )

        if insufficient:
            recs.append(
                f"Collect additional data for {len(insufficient)} metric(s) with insufficient evidence. "
                f"Consider increasing iteration count."
            )

        if not recs:
            recs.append("No action required. Continue standard monitoring cadence.")

        return recs
