"""Hexnil configuration and path resolution utilities."""

import os
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


def find_adb_executable(custom_path: Optional[str] = None) -> Optional[str]:
    """Locate the adb executable across multiple standard locations.

    Priority:
    1. Explicit custom path provided via argument or HEXNIL_ADB_PATH env var
    2. PATH environment variable via shutil.which
    3. local.properties in current or ancestor directories (sdk.dir)
    4. ANDROID_HOME or ANDROID_SDK_ROOT environment variables
    5. Standard OS-specific SDK directories
    """
    candidate_paths: List[Path] = []

    # 1. Custom path or environment variable
    env_override = custom_path or os.environ.get("HEXNIL_ADB_PATH")
    if env_override:
        p = Path(env_override)
        if p.is_file() and os.access(p, os.X_OK):
            return str(p.resolve())
        elif p.is_dir():
            exe_name = "adb.exe" if sys.platform == "win32" else "adb"
            candidate_paths.append(p / exe_name)
            candidate_paths.append(p / "platform-tools" / exe_name)

    # 2. System PATH
    which_adb = shutil.which("adb")
    if which_adb:
        return str(Path(which_adb).resolve())

    exe_name = "adb.exe" if sys.platform == "win32" else "adb"

    # 3. Check local.properties in cwd and parents
    cwd = Path.cwd().resolve()
    for directory in [cwd, *cwd.parents]:
        local_props = directory / "local.properties"
        if local_props.is_file():
            try:
                for line in local_props.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line.startswith("sdk.dir="):
                        sdk_val = line.split("=", 1)[1].strip()
                        # Unescape backslashes in properties file (e.g. C\:\\Users\\...)
                        sdk_val = sdk_val.replace("\\:", ":").replace("\\\\", "\\")
                        candidate_paths.append(Path(sdk_val) / "platform-tools" / exe_name)
            except Exception:
                pass

    # 4. Check ANDROID_HOME and ANDROID_SDK_ROOT
    for env_var in ["ANDROID_HOME", "ANDROID_SDK_ROOT"]:
        env_val = os.environ.get(env_var)
        if env_val:
            candidate_paths.append(Path(env_val) / "platform-tools" / exe_name)

    # 5. Check standard platform locations
    if sys.platform == "win32":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            candidate_paths.append(
                Path(local_app_data) / "Android" / "Sdk" / "platform-tools" / exe_name
            )
        home = Path.home()
        candidate_paths.append(
            home / "AppData" / "Local" / "Android" / "Sdk" / "platform-tools" / exe_name
        )
    elif sys.platform == "darwin":
        candidate_paths.append(
            Path.home() / "Library" / "Android" / "sdk" / "platform-tools" / exe_name
        )
    else:  # Linux / other Unix
        candidate_paths.append(
            Path.home() / "Android" / "Sdk" / "platform-tools" / exe_name
        )
        candidate_paths.append(Path("/usr/bin/adb"))
        candidate_paths.append(Path("/usr/local/bin/adb"))

    # Test all candidate paths
    for candidate in candidate_paths:
        try:
            if candidate.is_file() and os.access(candidate, os.X_OK):
                return str(candidate.resolve())
        except OSError:
            continue

    return None


@dataclass
class HexnilConfig:
    """Runtime configuration for Hexnil controller."""

    adb_path: Optional[str] = None
    data_dir: Path = field(default_factory=lambda: Path("data/experiments"))
    adb_timeout_seconds: float = 10.0

    @classmethod
    def load(
        cls,
        adb_path: Optional[str] = None,
        data_dir: Optional[Path] = None,
        timeout: float = 10.0,
    ) -> "HexnilConfig":
        resolved_adb = find_adb_executable(adb_path)
        resolved_data = data_dir or Path(
            os.environ.get("HEXNIL_DATA_DIR", "data/experiments")
        )
        return cls(
            adb_path=resolved_adb,
            data_dir=resolved_data.resolve(),
            adb_timeout_seconds=timeout,
        )
