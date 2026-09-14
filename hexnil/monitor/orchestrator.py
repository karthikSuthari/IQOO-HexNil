"""Master lifecycle orchestrator for end-to-end OS update impact validation."""

import datetime
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional

from hexnil.baseline.models import StabilizationPolicy
from hexnil.baseline.orchestrator import BaselineExperimentOrchestrator
from hexnil.classify.classifier import IssueClassifier
from hexnil.classify.models import IssueReport
from hexnil.device.adb import AdbClient
from hexnil.device.discovery import DeviceDiscovery
from hexnil.device.metadata import MetadataCollector
from hexnil.diff.orchestrator import DifferentialExperimentOrchestrator
from hexnil.diff.store import ComparisonStore
from hexnil.evaluate.evaluator import PredictionEvaluator
from hexnil.evaluate.models import PredictionEvaluationReport
from hexnil.exceptions import HexnilError
from hexnil.experiments.store import ExperimentStore
from hexnil.monitor.anomaly_detector import AnomalyDetector
from hexnil.monitor.models import (
    DeviceOsState,
    MonitoringPhase,
    MonitoringSample,
    MonitoringSession,
    PreUpdateSnapshot,
)
from hexnil.monitor.state_tracker import DeviceStateTracker
from hexnil.monitor.store import MonitoringStore
from hexnil.predict.models import ValidationPlan
from hexnil.predict.store import PredictionStore
from hexnil.report.generator import ReportGenerator
from hexnil.report.models import FinalEvidenceReport
from hexnil.stats.models import StatisticalAnalysisRecord
from hexnil.stats.orchestrator import StatisticalAnalysisOrchestrator
from hexnil.stats.store import StatisticalAnalysisStore
from hexnil.telemetry.bridge import TelemetryBridge

logger = logging.getLogger("hexnil.monitor.orchestrator")


class MonitoringOrchestrator:
    """Autonomous end-to-end OS update impact validation lifecycle.

    Implements the complete flow:
    DEVICE DISCOVERY → CURRENT OS IDENTITY → CONTINUOUS PRE-UPDATE MONITORING →
    TELEMETRY STORAGE → BASELINE AGGREGATION → PRE-UPDATE ANOMALY/RISK MODEL →
    V0 PRE-UPDATE SNAPSHOT → READY FOR SYSTEM UPDATE → WAIT FOR REAL OS UPDATE →
    UPDATE DETECTION GATE → CREATE V1 → DEVICE STABILIZATION → SAME TEST SUITE →
    POST-UPDATE TELEMETRY → V0 vs V1 COMPARISON → ISSUE CLASSIFICATION →
    ML PREDICTION EVALUATION → FINAL EVIDENCE REPORT
    """

    def __init__(
        self,
        adb: AdbClient,
        exp_store: ExperimentStore,
        comp_store: ComparisonStore,
        monitor_store: MonitoringStore,
        stats_store: Optional[StatisticalAnalysisStore] = None,
        pred_store: Optional[PredictionStore] = None,
    ):
        self.adb = adb
        self.exp_store = exp_store
        self.comp_store = comp_store
        self.monitor_store = monitor_store
        self.stats_store = stats_store or StatisticalAnalysisStore(comp_store.base_dir)
        self.pred_store = pred_store

        self.state_tracker = DeviceStateTracker(adb)
        self.anomaly_detector = AnomalyDetector()
        self.classifier = IssueClassifier()
        self.evaluator = PredictionEvaluator()
        self.report_generator = ReportGenerator()

    def run_session(
        self,
        serial: str,
        iterations: int = 3,
        poll_interval: int = 60,
        release_notes_path: Optional[str] = None,
        pre_monitoring_samples: int = 10,
        package_name: str = "com.example.iqoo_hexnil",
        workload_ids: Optional[List[str]] = None,
        stabilization_policy: Optional[StabilizationPolicy] = None,
    ) -> FinalEvidenceReport:
        """Execute the complete end-to-end monitoring session lifecycle."""

        # ──────────────────────────────────────────────────────────────────
        # 1. DEVICE DISCOVERY
        # ──────────────────────────────────────────────────────────────────
        logger.info("Phase 1: Device Discovery")
        discovery = DeviceDiscovery(self.adb)
        target = discovery.select_device(target_serial=serial)
        collector = MetadataCollector(self.adb)
        metadata, adb_status, warnings = collector.collect(target.serial)

        device_display = f"{metadata.manufacturer or ''} {metadata.model or ''}".strip()
        if not device_display:
            device_display = metadata.codename or "Unknown Android Device"

        # ──────────────────────────────────────────────────────────────────
        # 2. CURRENT OS IDENTITY
        # ──────────────────────────────────────────────────────────────────
        logger.info("Phase 2: Capturing current OS identity")
        v0_state = self.state_tracker.capture_os_state(serial)

        # ──────────────────────────────────────────────────────────────────
        # 3. CREATE MONITORING SESSION
        # ──────────────────────────────────────────────────────────────────
        session_id = self.monitor_store.generate_session_id()
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        session = MonitoringSession(
            session_id=session_id,
            device_serial=serial,
            device_model=device_display,
            created_at=now_iso,
            phase=MonitoringPhase.PRE_UPDATE_MONITORING,
            v0_os_state=v0_state,
            poll_interval_seconds=poll_interval,
            iterations=iterations,
            workload_suite=workload_ids or [],
            release_notes_path=release_notes_path,
            monitoring_started_at=now_iso,
        )
        self.monitor_store.save_session(session)

        logger.info(
            "Session %s created for device %s (Android %s, Build %s)",
            session_id, serial, v0_state.android_version, v0_state.build_id,
        )

        try:
            # ──────────────────────────────────────────────────────────────
            # 4. CONTINUOUS PRE-UPDATE MONITORING
            # ──────────────────────────────────────────────────────────────
            logger.info("Phase 3: Continuous pre-update monitoring (%d samples)", pre_monitoring_samples)
            samples = self._collect_monitoring_samples(
                session_id=session_id,
                serial=serial,
                num_samples=pre_monitoring_samples,
                poll_interval=poll_interval,
                v0_state=v0_state,
            )

            # ──────────────────────────────────────────────────────────────
            # 5. BASELINE AGGREGATION
            # ──────────────────────────────────────────────────────────────
            logger.info("Phase 4: Running baseline experiment (V0)")
            session.phase = MonitoringPhase.BASELINE_COLLECTION
            self.monitor_store.save_session(session)

            baseline_orch = BaselineExperimentOrchestrator(
                adb=self.adb,
                store=self.exp_store,
            )
            quality_report = baseline_orch.run_baseline_experiment(
                serial=serial,
                iterations=iterations,
                workload_ids=workload_ids,
                stabilization_policy=stabilization_policy,
                package_name=package_name,
            )
            session.baseline_experiment_id = quality_report.experiment_id
            self.monitor_store.save_session(session)

            # ──────────────────────────────────────────────────────────────
            # 6. PRE-UPDATE ANOMALY / RISK MODEL
            # ──────────────────────────────────────────────────────────────
            logger.info("Phase 5: Pre-update anomaly detection")
            anomaly_report = self.anomaly_detector.analyze(
                session_id=session_id,
                device_serial=serial,
                samples=samples,
            )
            session.anomaly_report = anomaly_report

            # ──────────────────────────────────────────────────────────────
            # 7. V0 PRE-UPDATE SNAPSHOT
            # ──────────────────────────────────────────────────────────────
            logger.info("Phase 6: Freezing V0 pre-update snapshot")
            snapshot = PreUpdateSnapshot(
                session_id=session_id,
                device_serial=serial,
                os_state=v0_state,
                baseline_experiment_id=session.baseline_experiment_id,
                anomaly_report=anomaly_report,
                prediction_plan_id=session.prediction_plan_id,
                frozen_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            )
            session.pre_update_snapshot = snapshot
            session.phase = MonitoringPhase.AWAITING_UPDATE
            self.monitor_store.save_session(session)

            logger.info(
                "V0 snapshot frozen. Pre-existing anomalies: %d. READY FOR SYSTEM UPDATE.",
                len(anomaly_report.anomalies),
            )

            # ──────────────────────────────────────────────────────────────
            # 8. WAIT FOR REAL OS / SECURITY UPDATE
            # ──────────────────────────────────────────────────────────────
            logger.info("Phase 7: Waiting for OS update (polling every %ds)...", poll_interval)
            v1_state = self._wait_for_update(
                serial=serial,
                v0_state=v0_state,
                poll_interval=poll_interval,
            )

            # ──────────────────────────────────────────────────────────────
            # 9. UPDATE DETECTION GATE
            # ──────────────────────────────────────────────────────────────
            logger.info("Phase 8: Update detected! Creating transition record")
            session.phase = MonitoringPhase.UPDATE_DETECTED
            session.update_detected_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

            transition = self.state_tracker.create_transition_record(v0_state, v1_state)
            session.v1_os_state = v1_state
            session.update_transition = transition
            self.monitor_store.save_session(session)

            logger.info(
                "Update confirmed: %s. Changes: %s",
                transition.transition_type.value,
                "; ".join(transition.changes[:3]),
            )

            # ──────────────────────────────────────────────────────────────
            # 10. DEVICE STABILIZATION + SAME TEST SUITE + POST-UPDATE TELEMETRY
            # ──────────────────────────────────────────────────────────────
            logger.info("Phase 9: Running post-update differential experiment (V1)")
            session.phase = MonitoringPhase.POST_UPDATE_VALIDATION
            self.monitor_store.save_session(session)

            diff_orch = DifferentialExperimentOrchestrator(
                adb=self.adb,
                exp_store=self.exp_store,
                comp_store=self.comp_store,
            )
            comp_quality = diff_orch.run_differential_experiment(
                v0_experiment_id=session.baseline_experiment_id,
                serial=serial,
                iterations=iterations,
                stabilization_policy=stabilization_policy,
                package_name=package_name,
                is_os_update=True,
            )
            session.comparison_id = comp_quality.comparison_id
            self.monitor_store.save_session(session)

            # ──────────────────────────────────────────────────────────────
            # 11. V0 vs V1 COMPARISON (Statistical Analysis)
            # ──────────────────────────────────────────────────────────────
            logger.info("Phase 10: Statistical analysis")
            session.phase = MonitoringPhase.ANALYSIS_IN_PROGRESS
            self.monitor_store.save_session(session)

            stats_orch = StatisticalAnalysisOrchestrator(
                exp_store=self.exp_store,
                comp_store=self.comp_store,
                stats_store=self.stats_store,
            )
            analysis = stats_orch.analyze_comparison(
                comparison_id=session.comparison_id,
            )
            session.analysis_id = analysis.analysis_id

            # ──────────────────────────────────────────────────────────────
            # 12. ISSUE CLASSIFICATION
            # ──────────────────────────────────────────────────────────────
            logger.info("Phase 11: Issue classification")
            issue_report = self.classifier.classify(
                session_id=session_id,
                comparison_id=session.comparison_id,
                device_serial=serial,
                v0_build_id=v0_state.build_id,
                v1_build_id=v1_state.build_id,
                analysis=analysis,
                anomaly_report=anomaly_report,
            )

            # ──────────────────────────────────────────────────────────────
            # 13. ML PREDICTION EVALUATION
            # ──────────────────────────────────────────────────────────────
            logger.info("Phase 12: Prediction evaluation")
            prediction_evaluation: Optional[PredictionEvaluationReport] = None
            plan: Optional[ValidationPlan] = None

            if self.pred_store:
                try:
                    plan_ids = self.pred_store.list_plans()
                    if plan_ids:
                        plan = self.pred_store.load_plan(plan_ids[0])
                        prediction_evaluation = self.evaluator.evaluate(
                            session_id=session_id,
                            comparison_id=session.comparison_id,
                            plan=plan,
                            analysis=analysis,
                        )
                except Exception as exc:
                    logger.warning("Prediction evaluation skipped: %s", exc)

            # ──────────────────────────────────────────────────────────────
            # 14. FINAL EVIDENCE REPORT
            # ──────────────────────────────────────────────────────────────
            logger.info("Phase 13: Generating final evidence report")
            report = self.report_generator.generate(
                session=session,
                issue_report=issue_report,
                analysis=analysis,
                plan=plan,
                prediction_evaluation=prediction_evaluation,
            )

            # Persist report
            report_json = report.model_dump_json(indent=2)
            self.monitor_store.save_artifact(session_id, "report.json", report_json)
            report_text = self.report_generator.format_text(report)
            self.monitor_store.save_artifact(session_id, "report.txt", report_text)

            session.report_id = report.report_id
            session.phase = MonitoringPhase.COMPLETED
            session.status = "completed"
            session.completed_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
            self.monitor_store.save_session(session)

            logger.info(
                "Session %s COMPLETED. Verdict: %s",
                session_id, report.overall_verdict,
            )

            return report

        except Exception as exc:
            session.phase = MonitoringPhase.FAILED
            session.status = "failed"
            session.error_message = str(exc)
            self.monitor_store.save_session(session)
            logger.error("Session %s FAILED: %s", session_id, exc)
            raise

    def _collect_monitoring_samples(
        self,
        session_id: str,
        serial: str,
        num_samples: int,
        poll_interval: int,
        v0_state: DeviceOsState,
    ) -> List[MonitoringSample]:
        """Collect continuous monitoring samples from the device."""
        samples: List[MonitoringSample] = []
        bridge = TelemetryBridge(self.adb, self.exp_store)

        for i in range(num_samples):
            now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

            # Capture current OS state to check for early update
            current_state = self.state_tracker.capture_os_state(serial)
            if self.state_tracker.has_update_occurred(v0_state, current_state):
                logger.info("Update detected during pre-monitoring at sample %d", i)
                break

            # Capture telemetry snapshot
            props = self.adb.get_all_props(serial)
            raw_metrics: Dict = {}

            # Battery
            bat_out = self.adb.run_serial_cmd(
                serial, ["shell", "dumpsys", "battery"], check=False
            )
            battery_level = self._parse_battery_level(bat_out)
            charging_state = self._parse_charging_state(bat_out)

            # Thermal
            thermal_out = self.adb.run_serial_cmd(
                serial, ["shell", "dumpsys", "thermalservice"], check=False
            )
            cpu_temp = self._parse_cpu_temperature(thermal_out)

            sample = MonitoringSample(
                session_id=session_id,
                sample_index=i,
                timestamp=now_iso,
                battery_level_percent=battery_level,
                battery_charging_state=charging_state,
                cpu_temperature_celsius=cpu_temp,
                os_state=current_state,
                raw_metrics=raw_metrics,
            )
            samples.append(sample)
            self.monitor_store.append_sample(session_id, sample)

            if i < num_samples - 1:
                time.sleep(poll_interval)

        return samples

    def _wait_for_update(
        self,
        serial: str,
        v0_state: DeviceOsState,
        poll_interval: int,
    ) -> DeviceOsState:
        """Poll until the OS update is detected or the device reboots into a new build."""
        while True:
            time.sleep(poll_interval)
            try:
                current_state = self.state_tracker.capture_os_state(serial)
                if self.state_tracker.has_update_occurred(v0_state, current_state):
                    return current_state
                logger.debug(
                    "No update yet. Current: %s", current_state.build_fingerprint[:50]
                )
            except Exception as exc:
                # Device may be rebooting during OTA
                logger.info(
                    "Device unreachable (likely rebooting for update): %s. Retrying in %ds...",
                    exc, poll_interval,
                )

    def _parse_battery_level(self, dumpsys_output: str) -> Optional[float]:
        """Parse battery level from dumpsys battery output."""
        for line in dumpsys_output.splitlines():
            line = line.strip()
            if line.startswith("level:"):
                try:
                    return float(line.split(":")[1].strip())
                except (ValueError, IndexError):
                    pass
        return None

    def _parse_charging_state(self, dumpsys_output: str) -> Optional[str]:
        """Parse charging state from dumpsys battery output."""
        for line in dumpsys_output.splitlines():
            line = line.strip()
            if line.startswith("status:"):
                status_val = line.split(":")[1].strip()
                status_map = {
                    "1": "UNKNOWN", "2": "CHARGING", "3": "DISCHARGING",
                    "4": "NOT_CHARGING", "5": "FULL",
                }
                return status_map.get(status_val, status_val)
        return None

    def _parse_cpu_temperature(self, thermal_output: str) -> Optional[float]:
        """Parse CPU temperature from dumpsys thermalservice output."""
        for line in thermal_output.splitlines():
            line = line.strip().lower()
            if "cpu" in line and ("temperature" in line or "temp" in line):
                for token in line.split():
                    try:
                        val = float(token)
                        if 20 <= val <= 120:
                            return val
                    except ValueError:
                        continue
        return None
