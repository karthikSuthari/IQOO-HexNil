"""Unit tests for Phase 2 Telemetry Schema and Capability Model."""

import json
import pytest
from hexnil.device.models import DeviceMetadata
from hexnil.telemetry.models import (
    CapabilityStatus,
    MetricValue,
    SoftwareIdentity,
    TelemetryRecord,
    WorkloadIdentity,
)


def test_telemetry_record_serialization():
    dev = DeviceMetadata(
        serial="DEV_001",
        manufacturer="vivo",
        model="I2302",
        android_version="16",
        sdk=36,
        build_id="BP2A.250605.031.A3",
        build_fingerprint="iQOO/I2302T/I2302:16",
        abi="arm64-v8a",
    )
    metric = MetricValue(name="battery_level_percent", value=82.5, unit="percent")
    rec = TelemetryRecord(
        experiment_id="EXP-20260913-001",
        timestamp="2026-09-13T12:00:00Z",
        device=dev,
        software=SoftwareIdentity(package="com.example.iqoo_hexnil"),
        workload=WorkloadIdentity(id="startup_basic", iteration=1),
        metric=metric,
        source="android_app",
        capability=CapabilityStatus.UNIVERSAL,
    )

    line = rec.to_jsonl_line()
    parsed = json.loads(line)

    assert parsed["experiment_id"] == "EXP-20260913-001"
    assert parsed["device"]["model"] == "I2302"
    assert parsed["software"]["package"] == "com.example.iqoo_hexnil"
    assert parsed["metric"]["name"] == "battery_level_percent"
    assert parsed["metric"]["value"] == 82.5
    assert parsed["capability"] == "UNIVERSAL"
    assert parsed["source"] == "android_app"


def test_unsupported_metric_null_handling():
    dev = DeviceMetadata(serial="DEV_001")
    rec = TelemetryRecord(
        experiment_id="EXP-20260913-001",
        timestamp="2026-09-13T12:00:00Z",
        device=dev,
        metric=MetricValue(name="soc_silicon_temperature_celsius", value=None, unit="celsius"),
        source="android_app",
        capability=CapabilityStatus.UNSUPPORTED,
        reason="Not exposed by public Android SDK without root",
    )

    parsed = json.loads(rec.to_jsonl_line())
    assert parsed["metric"]["value"] is None
    assert parsed["capability"] == "UNSUPPORTED"
    assert "without root" in parsed["reason"]


def test_capability_status_enum():
    assert CapabilityStatus.UNIVERSAL.value == "UNIVERSAL"
    assert CapabilityStatus.CONDITIONAL.value == "CONDITIONAL"
    assert CapabilityStatus.UNSUPPORTED.value == "UNSUPPORTED"
