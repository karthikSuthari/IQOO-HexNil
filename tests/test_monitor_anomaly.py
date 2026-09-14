"""Tests for Phase 9: Anomaly Detector."""

import pytest
from hexnil.monitor.anomaly_detector import AnomalyDetector, MIN_SAMPLES_FOR_DETECTION
from hexnil.monitor.models import AnomalyType, MonitoringSample


def _make_sample(idx, battery=80.0, jank=2.0, heap=100.0, cpu_temp=35.0):
    return MonitoringSample(
        session_id="MON-0001",
        sample_index=idx,
        timestamp=f"2026-01-01T00:{idx:02d}:00Z",
        battery_level_percent=battery,
        jank_percent=jank,
        app_heap_mb=heap,
        cpu_temperature_celsius=cpu_temp,
    )


class TestAnomalyDetector:
    def setup_method(self):
        self.detector = AnomalyDetector(z_threshold=2.5)

    def test_no_anomalies_stable_metrics(self):
        samples = [_make_sample(i) for i in range(10)]
        report = self.detector.analyze("MON-0001", "ABC", samples)
        assert not report.has_pre_existing_issues
        assert len(report.anomalies) == 0

    def test_insufficient_samples(self):
        samples = [_make_sample(i) for i in range(3)]
        report = self.detector.analyze("MON-0001", "ABC", samples)
        assert not report.has_pre_existing_issues

    def test_detect_jank_spike(self):
        # 9 normal samples + 1 extreme spike
        samples = [_make_sample(i, jank=2.0) for i in range(9)]
        samples.append(_make_sample(9, jank=50.0))  # Huge spike
        report = self.detector.analyze("MON-0001", "ABC", samples)
        jank_anomalies = [a for a in report.anomalies if a.anomaly_type == AnomalyType.JANK_SPIKE]
        assert len(jank_anomalies) > 0

    def test_detect_thermal_spike(self):
        samples = [_make_sample(i, cpu_temp=35.0) for i in range(9)]
        samples.append(_make_sample(9, cpu_temp=85.0))  # Extreme temperature
        report = self.detector.analyze("MON-0001", "ABC", samples)
        thermal_anomalies = [
            a for a in report.anomalies
            if a.anomaly_type == AnomalyType.THERMAL_THROTTLE
        ]
        assert len(thermal_anomalies) > 0

    def test_detect_memory_trend(self):
        # Monotonically increasing memory
        samples = [_make_sample(i, heap=100.0 + i * 10) for i in range(15)]
        report = self.detector.analyze("MON-0001", "ABC", samples)
        memory_anomalies = [
            a for a in report.anomalies
            if a.anomaly_type == AnomalyType.MEMORY_LEAK
        ]
        assert len(memory_anomalies) > 0

    def test_no_memory_trend_stable(self):
        samples = [_make_sample(i, heap=100.0) for i in range(10)]
        report = self.detector.analyze("MON-0001", "ABC", samples)
        memory_anomalies = [
            a for a in report.anomalies
            if a.anomaly_type == AnomalyType.MEMORY_LEAK
            and "Monotonic" in a.description
        ]
        assert len(memory_anomalies) == 0

    def test_detect_battery_drain(self):
        # Rapid battery drain
        samples = [_make_sample(i, battery=95 - i) for i in range(9)]
        samples.append(_make_sample(9, battery=50))  # Sudden huge drop
        report = self.detector.analyze("MON-0001", "ABC", samples)
        drain_anomalies = [
            a for a in report.anomalies
            if a.anomaly_type == AnomalyType.BATTERY_DRAIN
        ]
        assert len(drain_anomalies) > 0

    def test_report_summary(self):
        samples = [_make_sample(i, jank=2.0) for i in range(9)]
        samples.append(_make_sample(9, jank=50.0))
        report = self.detector.analyze("MON-0001", "ABC", samples)
        assert report.total_samples == 10
        assert "anomaly" in report.summary.lower() or "detected" in report.summary.lower()

    def test_empty_samples(self):
        report = self.detector.analyze("MON-0001", "ABC", [])
        assert not report.has_pre_existing_issues
        assert report.total_samples == 0
        assert report.monitoring_duration_seconds == 0.0

    def test_severity_classification(self):
        # Use many normal samples to keep stdev low, then add extreme spike
        # With 50 samples at 2.0 and 1 at 500.0, stdev stays manageable → z > 4.0
        samples = [_make_sample(i, jank=2.0) for i in range(50)]
        samples.append(_make_sample(50, jank=500.0))
        report = self.detector.analyze("MON-0001", "ABC", samples)
        jank_anomalies = [a for a in report.anomalies if "jank" in a.metric_name]
        assert len(jank_anomalies) > 0
        # At least one should be HIGH severity
        high_sev = [a for a in jank_anomalies if a.severity == "HIGH"]
        assert len(high_sev) > 0

    def test_custom_z_threshold(self):
        # Lower threshold = more sensitive
        detector = AnomalyDetector(z_threshold=1.5)
        samples = [_make_sample(i, jank=2.0) for i in range(9)]
        samples.append(_make_sample(9, jank=10.0))  # Moderate spike
        report_sensitive = detector.analyze("MON-0001", "ABC", samples)

        # Higher threshold = less sensitive
        detector_strict = AnomalyDetector(z_threshold=5.0)
        report_strict = detector_strict.analyze("MON-0001", "ABC", samples)

        assert len(report_sensitive.anomalies) >= len(report_strict.anomalies)
