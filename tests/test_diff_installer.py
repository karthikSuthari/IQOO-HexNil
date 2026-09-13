"""Unit tests for safe APK update installer and identity capture."""

import hashlib
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch

from hexnil.diff.installer import ApkInstaller, capture_v1_software_identity
from hexnil.diff.models import InstallOutcome


@pytest.fixture
def mock_adb():
    client = MagicMock()
    return client


def test_calculate_apk_sha256(tmp_path: Path, mock_adb):
    installer = ApkInstaller(mock_adb)
    apk_file = tmp_path / "test_app.apk"
    content = b"Mock APK binary content for test"
    apk_file.write_bytes(content)

    expected_sha = hashlib.sha256(content).hexdigest()
    assert installer.calculate_apk_sha256(apk_file) == expected_sha


def test_install_nonexistent_apk(mock_adb):
    installer = ApkInstaller(mock_adb)
    non_existent = Path("/non/existent/path/fake.apk")
    res = installer.install_v1_update("test-serial", non_existent)
    assert res.success is False
    assert res.outcome == InstallOutcome.INSTALL_FAILED_INVALID_APK
    assert "does not exist" in res.error_message


def test_install_success(tmp_path: Path, mock_adb):
    installer = ApkInstaller(mock_adb)
    apk_file = tmp_path / "app.apk"
    apk_file.write_bytes(b"dummy")

    mock_adb.run_serial_cmd.return_value = "Performing Streamed Install\nSuccess\n"
    res = installer.install_v1_update("test-serial", apk_file)

    assert res.success is True
    assert res.outcome == InstallOutcome.SUCCESS
    assert res.error_message is None
    mock_adb.run_serial_cmd.assert_called_once()
    args, kwargs = mock_adb.run_serial_cmd.call_args
    assert args[0] == "test-serial"
    assert args[1][0] == "install"
    assert "-r" in args[1]
    assert "-d" in args[1]


def test_install_version_downgrade(tmp_path: Path, mock_adb):
    installer = ApkInstaller(mock_adb)
    apk_file = tmp_path / "app.apk"
    apk_file.write_bytes(b"dummy")

    mock_adb.run_serial_cmd.return_value = "Failure [INSTALL_FAILED_VERSION_DOWNGRADE]"
    res = installer.install_v1_update("test-serial", apk_file)

    assert res.success is False
    assert res.outcome == InstallOutcome.INSTALL_FAILED_VERSION_DOWNGRADE
    assert "lower version code" in res.error_message


def test_install_signature_incompatible(tmp_path: Path, mock_adb):
    installer = ApkInstaller(mock_adb)
    apk_file = tmp_path / "app.apk"
    apk_file.write_bytes(b"dummy")

    mock_adb.run_serial_cmd.return_value = "Failure [INSTALL_FAILED_UPDATE_INCOMPATIBLE: Package signatures do not match]"
    res = installer.install_v1_update("test-serial", apk_file)

    assert res.success is False
    assert res.outcome == InstallOutcome.INSTALL_FAILED_UPDATE_INCOMPATIBLE
    assert "signing certificate is incompatible" in res.error_message


def test_install_insufficient_storage(tmp_path: Path, mock_adb):
    installer = ApkInstaller(mock_adb)
    apk_file = tmp_path / "app.apk"
    apk_file.write_bytes(b"dummy")

    mock_adb.run_serial_cmd.return_value = "Failure [INSTALL_FAILED_INSUFFICIENT_STORAGE]"
    res = installer.install_v1_update("test-serial", apk_file)

    assert res.success is False
    assert res.outcome == InstallOutcome.INSTALL_FAILED_INSUFFICIENT_STORAGE
    assert "insufficient storage" in res.error_message


def test_install_timeout(tmp_path: Path, mock_adb):
    installer = ApkInstaller(mock_adb)
    apk_file = tmp_path / "app.apk"
    apk_file.write_bytes(b"dummy")

    mock_adb.run_serial_cmd.return_value = "Command 'adb install ...' timed out after 120 seconds"
    res = installer.install_v1_update("test-serial", apk_file)

    assert res.success is False
    assert res.outcome == InstallOutcome.TIMEOUT
    assert "timed out" in res.error_message


def test_capture_v1_software_identity(mock_adb):
    mock_adb.get_all_props.return_value = {
        "ro.build.version.release": "15",
        "ro.build.id": "AP3A.240905.015",
        "ro.build.fingerprint": "google/oriole/oriole:15/AP3A.240905.015/test:user/release-keys",
    }

    def side_effect(serial, cmd, check=False):
        cmd_str = " ".join(cmd)
        if "pm path" in cmd_str:
            return "package:/data/app/~~test/com.example.iqoo_hexnil-1/base.apk\n"
        elif "sha256sum" in cmd_str:
            return "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  /data/app/test.apk\n"
        elif "dumpsys package" in cmd_str:
            return """
            Package [com.example.iqoo_hexnil] (38fa63b):
              userId=10283
              versionCode=2 minSdk=28 targetSdk=34
              versionName=1.1
            """
        return ""

    mock_adb.run_serial_cmd.side_effect = side_effect

    ident = capture_v1_software_identity(mock_adb, "test-serial", package_name="com.example.iqoo_hexnil")

    assert ident.package == "com.example.iqoo_hexnil"
    assert ident.version_name == "1.1"
    assert ident.version_code == 2
    assert ident.android_os_version == "15"
    assert ident.build_id == "AP3A.240905.015"
    assert ident.apk_path == "/data/app/~~test/com.example.iqoo_hexnil-1/base.apk"
    assert ident.apk_sha256 == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    assert ident.software_type == "V1_UPDATED"
    assert ident.update_method == "adb_install_replace"
