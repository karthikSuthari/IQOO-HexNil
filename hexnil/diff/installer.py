"""Safe APK update installation and post-install identity verification layer."""

import datetime
import hashlib
import logging
from pathlib import Path
import time
from typing import Optional

from hexnil.device.adb import AdbClient
from hexnil.diff.models import InstallOutcome, InstallResult, V1SoftwareIdentity

logger = logging.getLogger("hexnil.diff.installer")


class ApkInstaller:
    """Safely orchestrates target V1 APK update installation via ADB."""

    def __init__(self, adb: AdbClient):
        self.adb = adb

    def calculate_apk_sha256(self, apk_path: Path) -> str:
        """Calculate cryptographic SHA-256 hash of a local APK file."""
        hasher = hashlib.sha256()
        with apk_path.open("rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def install_v1_update(
        self,
        serial: str,
        apk_path: Path,
        timeout: float = 120.0,
    ) -> InstallResult:
        """Install target V1 APK onto target device using safe replace parameters."""
        if not apk_path.exists() or not apk_path.is_file():
            return InstallResult(
                apk_path=str(apk_path),
                apk_sha256="",
                outcome=InstallOutcome.INSTALL_FAILED_INVALID_APK,
                raw_output=f"File not found: {apk_path}",
                duration_ms=0.0,
                success=False,
                error_message=f"APK path '{apk_path}' does not exist or is not a file.",
            )

        apk_sha256 = self.calculate_apk_sha256(apk_path)
        logger.info("Installing V1 update APK %s (SHA-256: %s)", apk_path.name, apk_sha256)

        start_ns = time.perf_counter_ns()
        try:
            # -r: replace existing application
            # -d: allow version code downgrade if required by experiment
            cmd = ["install", "-r", "-d", str(apk_path.resolve())]
            output = self.adb.run_serial_cmd(serial, cmd, timeout=timeout, check=False)
        except Exception as exc:
            output = f"ERROR: Subprocess exception: {exc}"

        end_ns = time.perf_counter_ns()
        duration_ms = (end_ns - start_ns) / 1_000_000.0

        output_clean = output.strip()
        outcome = InstallOutcome.ERROR
        success = False
        error_msg: Optional[str] = None

        if "Success" in output_clean:
            outcome = InstallOutcome.SUCCESS
            success = True
            logger.info("Successfully installed V1 APK in %.1f ms", duration_ms)
        elif "INSTALL_FAILED_ALREADY_EXISTS" in output_clean:
            outcome = InstallOutcome.INSTALL_FAILED_ALREADY_EXISTS
            error_msg = "Package already exists with conflicting configuration."
        elif "INSTALL_FAILED_VERSION_DOWNGRADE" in output_clean:
            outcome = InstallOutcome.INSTALL_FAILED_VERSION_DOWNGRADE
            error_msg = "Target APK has lower version code than currently installed."
        elif "INSTALL_FAILED_UPDATE_INCOMPATIBLE" in output_clean:
            outcome = InstallOutcome.INSTALL_FAILED_UPDATE_INCOMPATIBLE
            error_msg = "Target APK signing certificate is incompatible with installed package."
        elif "INSTALL_FAILED_INSUFFICIENT_STORAGE" in output_clean:
            outcome = InstallOutcome.INSTALL_FAILED_INSUFFICIENT_STORAGE
            error_msg = "Target device has insufficient storage for APK installation."
        elif "INSTALL_FAILED_INVALID_APK" in output_clean:
            outcome = InstallOutcome.INSTALL_FAILED_INVALID_APK
            error_msg = "Target file is not a valid Android APK archive."
        elif "timed out" in output_clean.lower():
            outcome = InstallOutcome.TIMEOUT
            error_msg = f"Installation command timed out after {timeout} seconds."
        else:
            outcome = InstallOutcome.ERROR
            error_msg = f"ADB install failed: {output_clean}"

        return InstallResult(
            apk_path=str(apk_path.resolve()),
            apk_sha256=apk_sha256,
            outcome=outcome,
            raw_output=output_clean,
            duration_ms=round(duration_ms, 2),
            success=success,
            error_message=error_msg,
        )


def capture_v1_software_identity(
    adb: AdbClient,
    serial: str,
    package_name: str = "com.example.iqoo_hexnil",
    update_method: str = "adb_install_replace",
) -> V1SoftwareIdentity:
    """Query and verify installed V1 software identity on the target device."""
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # 1. Capture system build metadata
    props = adb.get_all_props(serial)
    os_version = props.get("ro.build.version.release")
    build_id = props.get("ro.build.id")
    build_fingerprint = props.get("ro.build.fingerprint")

    # 2. Query installed APK path
    apk_path: Optional[str] = None
    pm_out = adb.run_serial_cmd(serial, ["shell", "pm", "path", package_name], check=False).strip()
    for line in pm_out.splitlines():
        line_clean = line.strip()
        if line_clean.startswith("package:"):
            apk_path = line_clean.split(":", 1)[1].strip()
            break

    # 3. Compute cryptographic SHA-256 hash of installed APK
    apk_sha256: Optional[str] = None
    if apk_path:
        sha_out = adb.run_serial_cmd(serial, ["shell", "sha256sum", apk_path], check=False).strip()
        if sha_out and not sha_out.startswith("sha256sum:"):
            parts = sha_out.split()
            if parts and len(parts[0]) == 64:
                apk_sha256 = parts[0].lower()

    # 4. Extract version name and code
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

    return V1SoftwareIdentity(
        package=package_name,
        version_name=version_name,
        version_code=version_code,
        apk_path=apk_path,
        apk_sha256=apk_sha256,
        android_os_version=os_version,
        build_id=build_id,
        build_fingerprint=build_fingerprint,
        installed_at=now_iso,
        update_method=update_method,
        software_type="V1_UPDATED",
    )
