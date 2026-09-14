"""Phase 9: Continuous Monitoring & Update Detection.

Provides autonomous OS update lifecycle management including:
- DeviceOsState tracking and update detection
- Continuous pre-update monitoring with anomaly detection
- Master lifecycle orchestrator for end-to-end validation
"""

from hexnil.monitor.models import (
    AnomalyType,
    DeviceOsState,
    MonitoringPhase,
    MonitoringSample,
    MonitoringSession,
    PreUpdateAnomaly,
    PreUpdateAnomalyReport,
    PreUpdateSnapshot,
    TransitionType,
    UpdateTransition,
)
from hexnil.monitor.state_tracker import DeviceStateTracker
from hexnil.monitor.anomaly_detector import AnomalyDetector
from hexnil.monitor.store import MonitoringStore

__all__ = [
    "AnomalyDetector",
    "AnomalyType",
    "DeviceOsState",
    "DeviceStateTracker",
    "MonitoringPhase",
    "MonitoringSample",
    "MonitoringSession",
    "MonitoringStore",
    "PreUpdateAnomaly",
    "PreUpdateAnomalyReport",
    "PreUpdateSnapshot",
    "TransitionType",
    "UpdateTransition",
]
