"""Unit tests for experiment ID generation and local JSON persistence."""

import datetime
from pathlib import Path
import pytest

from hexnil.device.models import AdbStatus, DeviceMetadata, ExperimentRecord
from hexnil.exceptions import ExperimentPersistenceError
from hexnil.experiments.ids import generate_experiment_id
from hexnil.experiments.store import ExperimentStore


def test_experiment_id_generation_initial(tmp_path: Path):
    target_date = datetime.date(2026, 9, 13)
    exp_id = generate_experiment_id(tmp_path, target_date=target_date)
    assert exp_id == "EXP-20260913-001"


def test_experiment_id_generation_incrementing(tmp_path: Path):
    target_date = datetime.date(2026, 9, 13)

    # Simulate existing files
    (tmp_path / "EXP-20260913-001.json").write_text("{}", encoding="utf-8")
    (tmp_path / "EXP-20260913-002.json").write_text("{}", encoding="utf-8")

    next_id = generate_experiment_id(tmp_path, target_date=target_date)
    assert next_id == "EXP-20260913-003"


def test_experiment_id_different_dates(tmp_path: Path):
    (tmp_path / "EXP-20260912-005.json").write_text("{}", encoding="utf-8")

    target_date = datetime.date(2026, 9, 13)
    new_id = generate_experiment_id(tmp_path, target_date=target_date)
    assert new_id == "EXP-20260913-001"


def test_save_and_load_record_roundtrip(tmp_path: Path):
    store = ExperimentStore(tmp_path)

    metadata = DeviceMetadata(
        serial="SERIAL_TEST_123",
        manufacturer="Samsung",
        model="Galaxy S21",
        codename="o1s",
        android_version="14",
        sdk=34,
        build_id="UP1A.231005.007",
        build_fingerprint="samsung/o1s/o1s:14/UP1A.231005.007/G991BXXU9FWK4:user/release-keys",
        abi="arm64-v8a",
    )
    record = ExperimentRecord(
        experiment_id="EXP-20260913-001",
        created_at="2026-09-13T12:00:00Z",
        device=metadata,
        adb=AdbStatus(state="device", connected=True),
        phase="01_android_device_foundation",
        status="ready",
        warnings=["Test warning"],
    )

    saved_path = store.save(record)
    assert saved_path.exists()
    assert saved_path.name in ("metadata.json", "EXP-20260913-001.json")

    loaded = store.load("EXP-20260913-001")
    assert loaded.experiment_id == record.experiment_id
    assert loaded.created_at == record.created_at
    assert loaded.device.serial == "SERIAL_TEST_123"
    assert loaded.device.manufacturer == "Samsung"
    assert loaded.device.sdk == 34
    assert loaded.adb.state == "device"
    assert loaded.adb.connected is True
    assert loaded.warnings == ["Test warning"]


def test_load_nonexistent_record_raises(tmp_path: Path):
    store = ExperimentStore(tmp_path)
    with pytest.raises(ExperimentPersistenceError) as exc_info:
        store.load("EXP-99999999-999")
    assert "does not exist" in str(exc_info.value)


def test_load_corrupted_record_raises(tmp_path: Path):
    store = ExperimentStore(tmp_path)
    bad_file = tmp_path / "EXP-20260913-001.json"
    bad_file.write_text("invalid json content {{{", encoding="utf-8")

    with pytest.raises(ExperimentPersistenceError) as exc_info:
        store.load("EXP-20260913-001")
    assert "Corrupted or invalid experiment JSON" in str(exc_info.value)


def test_list_all_sorted(tmp_path: Path):
    store = ExperimentStore(tmp_path)

    for i in [1, 3, 2]:
        exp_id = f"EXP-20260913-00{i}"
        rec = ExperimentRecord(
            experiment_id=exp_id,
            created_at="2026-09-13T12:00:00Z",
            device=DeviceMetadata(serial=f"SERIAL_{i}"),
            adb=AdbStatus(),
        )
        store.save(rec)

    records = store.list_all()
    assert len(records) == 3
    assert [r.experiment_id for r in records] == [
        "EXP-20260913-003",
        "EXP-20260913-002",
        "EXP-20260913-001",
    ]


def test_telemetry_jsonl_append_and_load(tmp_path: Path):
    from hexnil.telemetry.models import TelemetryRecord, MetricValue, WorkloadIdentity
    store = ExperimentStore(tmp_path)
    exp_id = "EXP-20260913-005"
    device_meta = DeviceMetadata(serial="TEST_SERIAL", manufacturer="TestBrand", model="TestPhone")
    
    rec1 = TelemetryRecord(
        experiment_id=exp_id,
        timestamp="2026-09-13T12:00:00Z",
        device=device_meta,
        source="android_app",
        capability="UNIVERSAL",
        metric=MetricValue(name="battery_level", value=85, unit="percent"),
        workload=WorkloadIdentity(id="startup_basic", iteration=1)
    )
    rec2 = TelemetryRecord(
        experiment_id=exp_id,
        timestamp="2026-09-13T12:00:01Z",
        device=device_meta,
        source="adb",
        capability="UNIVERSAL",
        metric=MetricValue(name="mem_total_pss_kb", value=142300, unit="kb"),
        workload=WorkloadIdentity(id="startup_basic", iteration=1)
    )

    path1 = store.append_telemetry(exp_id, [rec1], filename="android.jsonl")
    path2 = store.append_telemetry(exp_id, [rec2], filename="adb.jsonl")

    assert path1.exists()
    assert path2.exists()
    assert path1.name == "android.jsonl"
    assert path2.name == "adb.jsonl"

    loaded_all = store.load_telemetry(exp_id)
    assert len(loaded_all) == 2
    assert {r.metric.name for r in loaded_all} == {"battery_level", "mem_total_pss_kb"}

    loaded_android = store.load_telemetry(exp_id, source="android")
    assert len(loaded_android) == 1
    assert loaded_android[0].metric.name == "battery_level"


def test_save_artifact(tmp_path: Path):
    store = ExperimentStore(tmp_path)
    exp_id = "EXP-20260913-006"
    art_path = store.save_artifact(exp_id, "dumpsys_meminfo.txt", "mock dump content")
    assert art_path.exists()
    assert art_path.read_text(encoding="utf-8") == "mock dump content"
    assert "artifacts" in str(art_path)

