"""Unit tests for configuration loading and ADB path resolution."""

import os
from pathlib import Path
from unittest.mock import patch

from hexnil.config import HexnilConfig, find_adb_executable


def test_find_adb_executable_explicit_file(tmp_path: Path):
    fake_adb = tmp_path / "adb.exe"
    fake_adb.write_text("mock binary", encoding="utf-8")

    resolved = find_adb_executable(str(fake_adb))
    assert resolved == str(fake_adb.resolve())


def test_find_adb_executable_from_env_var(tmp_path: Path, monkeypatch):
    fake_adb = tmp_path / "adb.exe"
    fake_adb.write_text("mock binary", encoding="utf-8")

    monkeypatch.setenv("HEXNIL_ADB_PATH", str(fake_adb))
    resolved = find_adb_executable()
    assert resolved == str(fake_adb.resolve())


def test_find_adb_executable_from_local_properties(tmp_path: Path, monkeypatch):
    # Set up directory with local.properties
    sdk_dir = tmp_path / "AndroidSdk"
    pt_dir = sdk_dir / "platform-tools"
    pt_dir.mkdir(parents=True)
    fake_adb = pt_dir / ("adb.exe" if os.name == "nt" else "adb")
    fake_adb.write_text("mock binary", encoding="utf-8")

    props_file = tmp_path / "local.properties"
    # Write escaped path typical of Android Studio
    escaped_sdk = str(sdk_dir).replace("\\", "\\\\").replace(":", "\\:")
    props_file.write_text(f"sdk.dir={escaped_sdk}\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("HEXNIL_ADB_PATH", raising=False)

    with patch("shutil.which", return_value=None):
        resolved = find_adb_executable()
        assert resolved == str(fake_adb.resolve())


def test_config_load_defaults(tmp_path: Path):
    cfg = HexnilConfig.load(data_dir=tmp_path / "exp")
    assert cfg.data_dir == (tmp_path / "exp").resolve()
    assert cfg.adb_timeout_seconds == 10.0
