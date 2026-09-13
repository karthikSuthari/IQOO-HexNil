"""Unit tests for PreconditionEvaluator."""

from unittest.mock import MagicMock
import pytest

from hexnil.workloads.models import PreconditionStatus
from hexnil.workloads.preconditions import PreconditionEvaluator


def test_precondition_screen_on_satisfied():
    mock_adb = MagicMock()
    mock_adb.run_serial_cmd.return_value = "Display Power: state=ON\nmWakefulness=Awake"

    evaluator = PreconditionEvaluator(mock_adb)
    results = evaluator.evaluate_all("SERIAL_TEST", {"screen_on": True})

    assert "screen_on" in results
    assert results["screen_on"].status == PreconditionStatus.SATISFIED
    assert results["screen_on"].actual_value is True


def test_precondition_battery_min_percent():
    mock_adb = MagicMock()
    mock_adb.run_serial_cmd.return_value = "Current Battery Service state:\n  level: 85\n  scale: 100"

    evaluator = PreconditionEvaluator(mock_adb)
    results = evaluator.evaluate_all("SERIAL_TEST", {"battery_min_percent": 20})

    assert results["battery_min_percent"].status == PreconditionStatus.SATISFIED
    assert results["battery_min_percent"].actual_value == 85

    # Test failure when level is below minimum
    results_fail = evaluator.evaluate_all("SERIAL_TEST", {"battery_min_percent": 90})
    assert results_fail["battery_min_percent"].status == PreconditionStatus.NOT_SATISFIED


def test_precondition_charging_state():
    mock_adb = MagicMock()
    mock_adb.run_serial_cmd.return_value = "USB powered: false\nAC powered: false\nWireless powered: false"

    evaluator = PreconditionEvaluator(mock_adb)
    res_discharging = evaluator.evaluate_all("SERIAL_TEST", {"charging_state": "discharging"})
    assert res_discharging["charging_state"].status == PreconditionStatus.SATISFIED

    res_charging = evaluator.evaluate_all("SERIAL_TEST", {"charging_state": "charging"})
    assert res_charging["charging_state"].status == PreconditionStatus.NOT_SATISFIED

    res_any = evaluator.evaluate_all("SERIAL_TEST", {"charging_state": "any"})
    assert res_any["charging_state"].status == PreconditionStatus.SATISFIED


def test_precondition_thermal_state_max():
    mock_adb = MagicMock()
    mock_adb.run_serial_cmd.return_value = "Current Thermal Status: 0"

    evaluator = PreconditionEvaluator(mock_adb)
    res = evaluator.evaluate_all("SERIAL_TEST", {"thermal_state_max": "moderate"})
    assert res["thermal_state_max"].status == PreconditionStatus.SATISFIED

    # Mock overheated thermal status (3 = SEVERE)
    mock_adb.run_serial_cmd.return_value = "Current Thermal Status: 3"
    res_hot = evaluator.evaluate_all("SERIAL_TEST", {"thermal_state_max": "light"})
    assert res_hot["thermal_state_max"].status == PreconditionStatus.NOT_SATISFIED


def test_precondition_unsupported():
    mock_adb = MagicMock()
    evaluator = PreconditionEvaluator(mock_adb)
    res = evaluator.evaluate_all("SERIAL_TEST", {"unknown_precondition_xyz": 123})
    assert res["unknown_precondition_xyz"].status == PreconditionStatus.NOT_SUPPORTED
