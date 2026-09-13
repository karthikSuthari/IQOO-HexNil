"""Unit tests for ComparisonStore and persistence."""

import datetime
from pathlib import Path
import pytest

from hexnil.baseline.models import EnvironmentSnapshot, V0SoftwareIdentity
from hexnil.device.models import DeviceMetadata
from hexnil.diff.models import (
    ComparisonQualityReport,
    ComparisonRecord,
    ComparisonRunPair,
    EnvironmentComparison,
    EnvironmentMatchStatus,
    InstallOutcome,
    InstallResult,
    PairStatus,
    V1SoftwareIdentity,
)
from hexnil.diff.store import ComparisonStore, generate_comparison_id


def test_generate_comparison_id(tmp_path: Path):
    target_date = datetime.date(2026, 9, 13)
    id1 = generate_comparison_id(tmp_path, target_date=target_date)
    assert id1 == "CMP-20260913-001"

    # Create dummy dir for id1
    (tmp_path / id1).mkdir()
    id2 = generate_comparison_id(tmp_path, target_date=target_date)
    assert id2 == "CMP-20260913-002"


def test_comparison_store_roundtrip(tmp_path: Path):
    store = ComparisonStore(tmp_path)
    cmp_id = "CMP-20260913-001"

    dev = DeviceMetadata(
        serial="serial-1",
        manufacturer="vivo",
        model="vivo I2302",
        brand="vivo",
        board="taro",
        android_version="16",
        sdk=36,
    )
    v0_soft = V0SoftwareIdentity(
        package="com.example.iqoo_hexnil",
        version_name="1.0",
        version_code=1,
        captured_at="2026-09-13T10:00:00Z",
    )
    v1_soft = V1SoftwareIdentity(
        package="com.example.iqoo_hexnil",
        version_name="1.1",
        version_code=2,
        installed_at="2026-09-13T11:00:00Z",
    )
    snap0 = EnvironmentSnapshot(timestamp="2026-09-13T10:00:00Z", battery_level_percent=80.0)
    snap1 = EnvironmentSnapshot(timestamp="2026-09-13T11:00:00Z", battery_level_percent=78.0)
    env = EnvironmentComparison(
        v0_snapshot=snap0,
        v1_snapshot=snap1,
        battery_level_delta_percent=2.0,
        condition_match_statuses={"battery": EnvironmentMatchStatus.MATCHED},
    )
    pair = ComparisonRunPair(
        comparison_id=cmp_id,
        workload_id="startup_01",
        iteration=1,
        v0_run_id="V0-1",
        v1_run_id="V1-1",
        v0_duration_ms=400.0,
        v1_duration_ms=390.0,
        v0_configuration_hash="hash1",
        v1_configuration_hash="hash1",
        pair_status=PairStatus.MATCHED,
    )
    inst = InstallResult(
        apk_path="/tmp/v1.apk",
        apk_sha256="sha123",
        outcome=InstallOutcome.SUCCESS,
        raw_output="Success",
        duration_ms=1200.0,
        success=True,
    )

    record = ComparisonRecord(
        comparison_id=cmp_id,
        created_at="2026-09-13T11:30:00Z",
        v0_experiment_id="EXP-V0",
        v1_experiment_id="EXP-V1",
        device=dev,
        v0_software=v0_soft,
        v1_software=v1_soft,
        workload_suite=["startup_01"],
        environment_comparison=env,
        run_pairs=[pair],
        install_result=inst,
    )

    saved_path = store.save_comparison(record)
    assert saved_path.exists()

    cmp_dir = store.get_comparison_dir(cmp_id)
    assert (cmp_dir / "comparison.json").exists()
    assert (cmp_dir / "v0_reference.json").exists()
    assert (cmp_dir / "v1_software.json").exists()
    assert (cmp_dir / "environment_comparison.json").exists()
    assert (cmp_dir / "matched_pairs.json").exists()

    loaded = store.load_comparison(cmp_id)
    assert loaded.comparison_id == cmp_id
    assert loaded.v0_software.version_name == "1.0"
    assert loaded.v1_software.version_name == "1.1"
    assert len(loaded.run_pairs) == 1
    assert loaded.run_pairs[0].pair_status == PairStatus.MATCHED

    pairs = store.load_comparison_pairs(cmp_id)
    assert len(pairs) == 1
    assert pairs[0].workload_id == "startup_01"

    all_recs = store.list_all()
    assert len(all_recs) == 1
    assert all_recs[0].comparison_id == cmp_id
