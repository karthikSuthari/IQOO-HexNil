# HEXNIL — Phase 1: Android Device Foundation

Hexnil is a mobile release-validation intelligence system. Its core question is:
> *“Did the update do what it promised, and what did it accidentally break?”*

The overall product loop is:
```
Predict → Prioritize → Validate → Explain → Learn
```

Phase 1 establishes the **host-side Android Device Foundation**, providing reliable device discovery, serial-targeted health checks, hardware/OS metadata extraction, deterministic experiment ID generation, and local JSON persistence.

---

## Architecture Boundary

```
+-------------------------------------------------------------+
| HOST CONTROLLER (Python 3.11+)                              |
|                                                             |
|  hexnil.cli                                                 |
|    ├── hexnil.device.discovery (adb devices -l parser)      |
|    ├── hexnil.device.adb       (Safe subprocess runner)     |
|    ├── hexnil.device.metadata  (Health check & getprop)     |
|    └── hexnil.experiments      (ID generator & JSON store)  |
+------------------------------+------------------------------+
                               |
                   ADB Subprocess (-s <SERIAL>)
                               |
                               v
+-------------------------------------------------------------+
| TARGET ANDROID HARDWARE (USB / TCP)                         |
|  • Android OS (API / Build properties)                      |
|  • Device companion app (Target for later phases)           |
+-------------------------------------------------------------+
```

> [!IMPORTANT]
> **Host vs App Separation**: ADB execution strictly belongs to the host machine controller, never embedded inside the mobile APK.

---

## Project Structure

```
IQOOHEXNIL/
├── hexnil/
│   ├── __init__.py           # Package version and export
│   ├── __main__.py           # Entry point for `python -m hexnil`
│   ├── cli.py                # Command-line interface
│   ├── config.py             # ADB binary resolver & configuration
│   ├── exceptions.py         # Domain errors with actionable guidance
│   ├── device/
│   │   ├── __init__.py
│   │   ├── adb.py            # Safe argument array subprocess wrapper
│   │   ├── discovery.py      # Device listing and selection policy
│   │   ├── metadata.py       # Health check and property extraction
│   │   └── models.py         # Pydantic data schemas
│   └── experiments/
│       ├── __init__.py
│       ├── ids.py            # EXP-YYYYMMDD-001 generator
│       └── store.py          # Atomic JSON persistence and loader
├── tests/
│   ├── __init__.py
│   ├── test_adb_client.py    # Subprocess execution and validation tests
│   ├── test_adb_parser.py    # adb devices -l parser tests
│   ├── test_cli.py           # CLI invocation and error formatting tests
│   ├── test_config.py        # ADB path discovery tests
│   ├── test_device_selection.py # Single/multiple device policy tests
│   ├── test_experiment_store.py # Store persistence and roundtrip tests
│   └── test_metadata.py      # getprop mapping and health check tests
├── data/
│   └── experiments/          # Local JSON experiment records
├── app/                      # Android companion app (reserved for later phases)
├── requirements.txt
├── README.md
└── .gitignore
```

---

## Prerequisites

1. **Python 3.11+** installed and accessible on host machine.
2. **Android SDK Platform-Tools (ADB)** installed.
   - If installed via Android Studio, Hexnil automatically detects ADB from `local.properties` (`sdk.dir`), `ANDROID_HOME`, `ANDROID_SDK_ROOT`, or default SDK paths.
   - Alternatively, ensure `adb` is on system `PATH` or set `HEXNIL_ADB_PATH`.
3. **Android Device Setup**:
   - Enable **Developer Options** on device (Settings > About Phone > Tap "Build number" 7 times).
   - In Developer Options, enable **USB Debugging**.
   - Connect device to host via USB data cable.
   - When the device prompts **"Allow USB debugging?"**, check **"Always allow from this computer"** and tap **Allow**.

---

## Installation & Setup

Install Python dependencies:
```bash
python -m pip install -r requirements.txt
```

---

## Device Connection & CLI Commands

### 1. List All Connected Devices
```bash
python -m hexnil device list
```
Machine-readable format:
```bash
python -m hexnil device list --json
```

### 2. Connect & Capture Device Foundation (Device Status)
If exactly one usable device is connected:
```bash
python -m hexnil device status
```

To explicitly target a specific device by serial:
```bash
python -m hexnil device status --serial <SERIAL>
```

Machine-readable JSON output:
```bash
python -m hexnil device status --json
```

### 3. List Persisted Experiments
```bash
python -m hexnil experiment list
```

### 4. Inspect a Persisted Experiment
```bash
python -m hexnil experiment show EXP-20260913-001
```

---

## Example Outputs

### Successful Output (Human-Readable)
```
Hexnil Device Foundation
------------------------
Status: CONNECTED
Device: Google Pixel 8 Pro
Android: 15
SDK: 35
Build ID: AP2A.240805.005
Build fingerprint: google/husky/husky:15/AP2A.240805.005/12034873:user/release-keys
ADB serial: 39121FDJG0002Y
Experiment ID: EXP-20260913-001

Persisted record: C:\Users\sutha\Desktop\IQOOHEXNIL\data\experiments\EXP-20260913-001.json
```

### Successful Output (JSON)
```json
{
  "experiment_id": "EXP-20260913-001",
  "created_at": "2026-09-13T12:00:00+00:00",
  "device": {
    "serial": "39121FDJG0002Y",
    "manufacturer": "Google",
    "model": "Pixel 8 Pro",
    "codename": "husky",
    "android_version": "15",
    "sdk": 35,
    "build_id": "AP2A.240805.005",
    "build_fingerprint": "google/husky/husky:15/AP2A.240805.005/12034873:user/release-keys",
    "abi": "arm64-v8a"
  },
  "adb": {
    "state": "device",
    "connected": true
  },
  "phase": "01_android_device_foundation",
  "status": "ready",
  "warnings": []
}
```

---

## Example Error Outputs & Recovery Actions

### 1. No Devices Connected
```
[ERROR] No Android devices connected or detected via ADB.

Action required:
Connect an Android device via USB, ensure USB cable supports data transfer, enable Developer Options on the device, and turn on 'USB Debugging'. Run 'adb devices' to confirm detection.
```

### 2. Device Unauthorized
```
[ERROR] Device '39121FDJG0002Y' is unauthorized.

Action required:
Check the screen of device '39121FDJG0002Y'. Unlock the device and tap 'Allow USB debugging' (select 'Always allow from this computer'). If the prompt does not appear, try: adb reconnect or revoking USB authorizations in Developer Options.
```

### 3. Device Offline
```
[ERROR] Device '39121FDJG0002Y' is offline.

Action required:
Device '39121FDJG0002Y' is not communicating. Try unplugging and replugging the USB cable, or run: adb reconnect offline, or toggle USB Debugging off and on in Developer Options.
```

### 4. Multiple Devices Connected (Ambiguity Guard)
```
[ERROR] Multiple devices connected (2 found: 39121FDJG0002Y, emulator-5554). Hexnil requires an explicit target serial to avoid accidental operations.

Action required:
Select a device explicitly by running:
  python -m hexnil device status --serial <SERIAL>
Available serials: 39121FDJG0002Y, emulator-5554
```

### 5. Target Serial Not Found
```
[ERROR] Target device with serial 'INVALID_SERIAL' was not found.

Action required:
Verify the serial number. Currently detected devices: [39121FDJG0002Y]. Run 'python -m hexnil device list' to see all active devices.
```

---

## Running Automated Tests

Run the complete test suite:
```bash
python -m pytest tests/ -v
```

Run tests with code coverage report:
```bash
python -m pytest --cov=hexnil tests/
```
