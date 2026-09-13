"""V0 Software Identity capture layer."""

import datetime
import logging
from typing import Optional

from hexnil.baseline.models import V0SoftwareIdentity
from hexnil.device.adb import AdbClient

logger = logging.getLogger("hexnil.baseline.identity")


def capture_v0_software_identity(
    adb: AdbClient,
    serial: str,
    package_name: str = "com.example.iqoo_hexnil",
) -> V0SoftwareIdentity:
    """Capture comprehensive V0 software and build identity for the target application."""
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # 1. Capture system build metadata
    props = adb.get_all_props(serial)
    os_version = props.get("ro.build.version.release")
    build_id = props.get("ro.build.id")
    build_fingerprint = props.get("ro.build.fingerprint")

    # 2. Query installed APK path via `pm path`
    apk_path: Optional[str] = None
    pm_out = adb.run_serial_cmd(serial, ["shell", "pm", "path", package_name], check=False).strip()
    for line in pm_out.splitlines():
        line_clean = line.strip()
        if line_clean.startswith("package:"):
            apk_path = line_clean.split(":", 1)[1].strip()
            break

    # 3. Compute cryptographic SHA-256 hash of the installed APK
    apk_sha256: Optional[str] = None
    if apk_path:
        sha_out = adb.run_serial_cmd(serial, ["shell", "sha256sum", apk_path], check=False).strip()
        if sha_out and not sha_out.startswith("sha256sum:"):
            parts = sha_out.split()
            if parts and len(parts[0]) == 64:
                apk_sha256 = parts[0].lower()
                logger.info("Captured APK SHA-256 for %s: %s", package_name, apk_sha256)

    # 4. Extract version metadata from `dumpsys package`
    version_name: Optional[str] = None
    version_code: Optional[int] = None
    dumpsys_pkg = adb.run_serial_cmd(serial, ["shell", "dumpsys", "package", package_name], check=False)
    for line in dumpsys_pkg.splitlines():
        line_clean = line.strip()
        if "versionName=" in line_clean and version_name is None:
            parts = line_clean.split("versionName=", 1)
            if len(parts) > 1:
                version_name = parts[1].split()[0].strip()
        if "versionCode=" in line_clean and version_code is None:
            parts = line_clean.split("versionCode=", 1)
            if len(parts) > 1:
                code_str = parts[1].split()[0].strip()
                try:
                    version_code = int(code_str)
                except ValueError:
                    pass

    return V0SoftwareIdentity(
        package=package_name,
        version_name=version_name,
        version_code=version_code,
        apk_path=apk_path,
        apk_sha256=apk_sha256,
        android_os_version=os_version,
        build_id=build_id,
        build_fingerprint=build_fingerprint,
        captured_at=now_iso,
        software_type="V0_ORIGINAL",
    )
