"""Unit tests for Supabase Fleet Client and Sync Manager."""

from unittest.mock import MagicMock, patch
import pytest

from hexnil.cloud.client import SupabaseFleetClient
from hexnil.cloud.sync import FleetSyncManager
from hexnil.device.models import AdbStatus, DeviceMetadata, ExperimentRecord
from hexnil.experiments.store import ExperimentStore


@pytest.fixture
def mock_client():
    client = SupabaseFleetClient(
        supabase_url="https://fake-project.supabase.co",
        supabase_key="fake-key",
    )
    return client


def test_supabase_client_headers(mock_client):
    headers = mock_client.headers
    assert headers["apikey"] == "fake-key"
    assert "Bearer fake-key" in headers["Authorization"]
    assert headers["Content-Type"] == "application/json"


@patch("requests.post")
def test_register_device(mock_post, mock_client):
    mock_post.return_value.status_code = 201
    mock_post.return_value.json.return_value = [{"device_id": "test_device_001"}]

    device_payload = {
        "device_id": "test_device_001",
        "model": "I2302",
        "manufacturer": "vivo",
    }
    res = mock_client.register_device(device_payload)
    assert res["device_id"] == "test_device_001"
    mock_post.assert_called_once()


@patch("requests.get")
def test_list_devices(mock_get, mock_client):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = [
        {"device_id": "dev_1", "model": "Model A"},
        {"device_id": "dev_2", "model": "Model B"},
    ]
    devices = mock_client.list_devices()
    assert len(devices) == 2
    assert devices[0]["device_id"] == "dev_1"


@patch("requests.post")
def test_upload_telemetry_batch(mock_post, mock_client):
    mock_post.return_value.status_code = 201
    mock_post.return_value.json.return_value = [{"id": 1}, {"id": 2}]

    samples = [
        {"device_id": "dev_1", "metric_name": "battery_level_percent", "metric_value": 95.0},
        {"device_id": "dev_1", "metric_name": "cpu_celsius", "metric_value": 38.5},
    ]
    count = mock_client.upload_telemetry_batch(samples)
    assert count == 2


@patch("requests.post")
def test_publish_device_report_and_issues(mock_post, mock_client, tmp_path):
    store = ExperimentStore(tmp_path)
    sync = FleetSyncManager(store, client=mock_client)

    mock_post.return_value.status_code = 201
    mock_post.return_value.json.return_value = [{"report_id": "REPORT-001"}]

    res = sync.push_device_report_and_issues(
        device_id="dev_1",
        comparison_id="CMP-001",
        v0_build_id="BUILD_A",
        v1_build_id="BUILD_B",
        verdict="SAFE TO ROLLOUT",
        coverage="5 / 5",
        summary_text="All stable",
        evidence_dossier={},
        issues=[
            {
                "workload_id": "startup_01",
                "metric_name": "startup_duration_ms",
                "category": "STABLE",
                "severity": "NONE",
            }
        ],
    )
    assert res["verdict"] == "SAFE TO ROLLOUT"
    assert res["total_issues"] == 1


@patch("requests.get")
def test_pull_device_telemetry(mock_get, mock_client, tmp_path):
    store = ExperimentStore(tmp_path)
    sync = FleetSyncManager(store, client=mock_client)

    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = [
        {"experiment_id": "EXP-001", "metric_name": "battery_level_percent", "metric_value": 90.0},
        {"experiment_id": "EXP-001", "metric_name": "cpu_celsius", "metric_value": 35.0},
    ]

    res = sync.pull_device_telemetry("dev_1")
    assert res["device_id"] == "dev_1"
    assert res["samples_fetched"] == 2
    assert res["experiments_count"] == 1
    assert len(res["saved_paths"]) == 1


@patch("requests.post")
def test_push_final_evidence_report(mock_post, mock_client, tmp_path):
    store = ExperimentStore(tmp_path)
    sync = FleetSyncManager(store, client=mock_client)

    mock_post.return_value.status_code = 201
    mock_post.return_value.json.return_value = [{"report_id": "REPORT-001"}]

    report_data = {
        "device_serial": "dev_vivo_1",
        "comparison_id": "CMP-999",
        "overall_verdict": "UPDATE_HAS_REGRESSIONS",
        "executive_summary": "Detected regression in battery discharge rate",
        "new_regressions": [
            {
                "metric_name": "battery_drain_rate",
                "post_update_severity": "HIGH",
                "percent_delta": 24.5,
                "explanation": "Elevated background wakeups after update",
            }
        ],
    }

    res = sync.push_final_evidence_report(report_data)
    assert res["device_id"] == "dev_vivo_1"
    assert res["verdict"] == "UPDATE_HAS_REGRESSIONS"
    assert res["total_issues"] == 1

