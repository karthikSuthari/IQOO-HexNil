# HEXNIL — Mobile Release-Validation Intelligence System

Hexnil is a mobile release-validation intelligence system. Its core question is:
> *“Did the update do what it promised, and what did it accidentally break?”*

The overall product loop is:
```
Predict → Prioritize → Validate → Explain → Learn
```

- **Phase 1**: Android Device Foundation (ADB discovery, serial selection, health checks, metadata capture, experiment IDs, JSON persistence).
- **Phase 2**: Universal Telemetry Collection (On-device Kotlin/Compose engine, host-side ADB bridge, deterministic workload runner, capability taxonomy, JSONL persistence, artifact capture).

---

## Phase 2 Architecture

```
+-------------------------------------------------------------------------+
| ANDROID TARGET DEVICE (Hardware: vivo I2302 / Android 16 / SDK 36)      |
|                                                                         |
|  Hexnil Companion App (com.example.iqoo_hexnil)                         |
|    ├── TelemetryEngine       (Snapshot coordinator & on-device JSONL)   |
|    ├── BatteryTelemetry      (Level, charging state, temp, voltage)    |
|    ├── MemoryTelemetry       (App PSS heap vs Device RAM/pressure)     |
|    ├── ThermalTelemetry      (ThermalStatus & headroom via public API)  |
|    ├── WorkloadRunner        (Deterministic workload execution & timing)|
|    └── Compose Dashboard     (Minimal dark UI with live capability map) |
+------------------------------------+------------------------------------+
                                     |
                          am start / run-as / JSONL pull
                                     |
                                     v
+-------------------------------------------------------------------------+
| HOST CONTROLLER (Python 3.11+)                                          |
|                                                                         |
|  hexnil.cli                                                             |
|    ├── hexnil.telemetry.bridge       (Host-device coordinator)          |
|    ├── hexnil.telemetry.adb_collectors:                                 |
|    │     ├── AdbLogcatCollector      (Bounded logcat capture)           |
|    │     ├── AdbMeminfoCollector     (dumpsys meminfo parser)           |
|    │     ├── AdbGfxinfoCollector     (dumpsys gfxinfo framestats parser)|
|    │     ├── AdbThermalCollector     (dumpsys thermalservice HAL parser)|
|    │     ├── AdbBatterystatsCollector(dumpsys batterystats collector)   |
|    │     └── AdbPerfettoCollector    (Bounded Perfetto trace capture)   |
|    └── hexnil.experiments.store      (JSONL telemetry & artifacts)      |
+-------------------------------------------------------------------------+
```

> [!IMPORTANT]
> **Host vs App Separation**: The Android application is the primary device-side collector using Android public APIs. Host ADB signals (logcat, dumpsys, Perfetto) strictly execute from Python on the host machine. ADB is never embedded inside the APK.

---

## Telemetry Principles

1. **Real Data > Complete Data**: Never fabricate a metric. If Android or the device does not legitimately expose a metric, mark it `UNSUPPORTED` with a descriptive `reason`. Missing metrics have `value: null, unit: null` (never 0, -1, or 999 fake placeholders).
2. **Capability Taxonomy**:
   - `UNIVERSAL`: Reliably available across standard Android devices via public APIs or standard ADB.
   - `CONDITIONAL`: Dependent on specific API levels, vendor HAL implementations, or hardware sensors.
   - `UNSUPPORTED`: Not exposed by public APIs without root or restricted by sandbox security.
3. **App vs Device Separation**: Never conflate application memory (heap PSS) with total device RAM.
4. **Honest Terminology**: Battery percentage is a proxy/estimate, never labeled as direct "power consumption".

---

## Telemetry Data Schema

Every telemetry metric record adheres to the following unified schema:

```json
{
  "experiment_id": "EXP-20260913-004",
  "timestamp": "2026-09-13T07:13:02.549449Z",
  "device": {
    "serial": "adb-10BE38254U0003T-PJiTJm._adb-tls-connect._tcp",
    "manufacturer": "vivo",
    "model": "I2302",
    "codename": "I2302T",
    "android_version": "16",
    "sdk": 36,
    "build_id": "BP2A.250605.031.A3",
    "build_fingerprint": "iQOO/I2302T/I2302:16/BP2A.250605.031.A3/...:user/release-keys",
    "abi": "arm64-v8a"
  },
  "software": {
    "package": "com.example.iqoo_hexnil",
    "version_name": "1.0",
    "version_code": 1
  },
  "workload": {
    "id": "startup_basic",
    "iteration": 1
  },
  "metric": {
    "name": "device_memory_available_mb",
    "value": 1709.27,
    "unit": "megabytes"
  },
  "source": "android_app",
  "capability": "UNIVERSAL",
  "reason": null
}
```

If a metric is unsupported:
```json
{
  "metric": {
    "name": "soc_silicon_temperature_celsius",
    "value": null,
    "unit": "celsius"
  },
  "source": "android_app",
  "capability": "UNSUPPORTED",
  "reason": "Exact SoC / CPU silicon temperature is not exposed by public Android SDK without root (use host ADB thermalservice)"
}
```

---

## Telemetry Storage Structure

Experiments are stored under `data/experiments/EXP-YYYYMMDD-XXX/`:

```
data/
  experiments/
    EXP-20260913-004/
      metadata.json          # Phase 1 & 2 experiment metadata
      telemetry/
        android.jsonl        # On-device timestamped telemetry records
        adb.jsonl            # Host-side ADB timestamped telemetry records
      artifacts/
        dumpsys_meminfo.txt
        dumpsys_gfxinfo.txt
        dumpsys_thermalservice.txt
        dumpsys_batterystats.txt
        logcat.txt
        trace.perfetto-trace (if supported)
```

---

## Telemetry Categories Collected

| Category | Source | Metric Name | Capability | Description |
|---|---|---|---|---|
| **Battery** | `android_app` | `battery_level_percent` | `UNIVERSAL` | Battery charge percentage |
| | `android_app` | `battery_charging_state` | `UNIVERSAL` | Charging / Discharging / Full |
| | `android_app` | `battery_temperature_celsius` | `CONDITIONAL` | Battery thermal reading |
| | `android_app` | `battery_voltage_volts` | `CONDITIONAL` | Battery voltage |
| | `android_app` | `battery_current_microamps` | `CONDITIONAL` | Real-time current flow |
| **Memory** | `android_app` | `app_heap_allocated_mb` | `UNIVERSAL` | Allocated JVM heap |
| | `android_app` | `app_heap_max_mb` | `UNIVERSAL` | Max available JVM heap |
| | `android_app` | `device_memory_available_mb`| `UNIVERSAL` | System-wide available RAM |
| | `android_app` | `device_memory_total_mb` | `UNIVERSAL` | Total device physical RAM |
| | `android_app` | `device_memory_low_pressure`| `UNIVERSAL` | Low memory pressure flag |
| | `adb` | `adb_mem_total_pss_kb` | `UNIVERSAL` | dumpsys meminfo Total PSS |
| | `adb` | `adb_mem_native_heap_pss_kb`| `UNIVERSAL` | Native heap PSS |
| | `adb` | `adb_mem_dalvik_heap_pss_kb`| `UNIVERSAL` | Dalvik heap PSS |
| **Thermal** | `android_app` | `thermal_status_name` | `UNIVERSAL` | PowerManager thermal status |
| | `android_app` | `thermal_headroom_ratio` | `CONDITIONAL` | API 30+ thermal headroom |
| | `android_app` | `soc_silicon_temperature_celsius`| `UNSUPPORTED`| Unexposed to non-root apps |
| | `adb` | `adb_thermal_cpu_celsius` | `UNIVERSAL` | dumpsys thermalservice CPU HAL |
| | `adb` | `adb_thermal_gpu_celsius` | `UNIVERSAL` | dumpsys thermalservice GPU HAL |
| | `adb` | `adb_thermal_battery_celsius` | `UNIVERSAL` | dumpsys thermalservice Battery HAL |
| | `adb` | `adb_thermal_skin_celsius` | `UNIVERSAL` | dumpsys thermalservice Skin HAL |
| **Workload**| `android_app` | `workload_duration_ms` | `UNIVERSAL` | Deterministic execution time |
| | `android_app` | `workload_success` | `UNIVERSAL` | Boolean workload status |
| | `android_app` | `workload_operations_count`| `UNIVERSAL` | Completed workload cycles |
| **Startup** | `android_app` | `app_startup_duration_ms` | `CONDITIONAL` | Measured application launch |
| **UI Jank** | `android_app` | `ui_frame_jank_percent` | `CONDITIONAL` | In-app FrameMetrics |
| | `adb` | `adb_gfx_total_frames` | `UNIVERSAL` | dumpsys gfxinfo total frames |
| | `adb` | `adb_gfx_janky_frames` | `UNIVERSAL` | dumpsys gfxinfo janky frames |
| | `adb` | `adb_gfx_p50_ms` - `p99_ms`| `UNIVERSAL` | Frame duration percentiles |
| **Logcat** | `adb` | `adb_logcat_lines` | `UNIVERSAL` | Bounded experiment log snippet |
| **Perfetto**| `adb` | `adb_perfetto_trace_bytes` | `CONDITIONAL` | System trace file capture |

---

## CLI Usage

### 1. Collect Telemetry
Execute deterministic workload and collect on-device + host ADB telemetry:
```bash
python -m hexnil telemetry collect --serial <SERIAL>
```
Output as JSON:
```bash
python -m hexnil telemetry collect --serial <SERIAL> --json
```

### 2. Inspect Experiment Telemetry
Display all telemetry records for an experiment:
```bash
python -m hexnil telemetry show EXP-20260913-004
```
Output as JSON:
```bash
python -m hexnil telemetry show EXP-20260913-004 --json
```

### 3. Device Discovery & Health (Phase 1)
```bash
python -m hexnil device list
python -m hexnil device status --serial <SERIAL>
python -m hexnil experiment list
```

---

## Verification & Testing

### Unit Test Suite (60 passed in 1.12s)
```bash
python -m pytest tests/ -v
```
- Schema validation, required fields, and null handling
- Capability enum enforcement (`UNIVERSAL`, `CONDITIONAL`, `UNSUPPORTED`)
- Dumpsys parsers (`meminfo`, `gfxinfo`, `thermalservice`, `batterystats`)
- Bounded logcat collector
- Telemetry JSONL append/load roundtrip
- Artifact persistence
- CLI argument parsing and error formatting

### Real Hardware Verification (vivo I2302)
- **Device**: vivo I2302 (`adb-10BE38254U0003T-PJiTJm._adb-tls-connect._tcp`)
- **OS**: Android 16 (SDK 36, arm64-v8a)
- **Experiment ID**: `EXP-20260913-004`
- **Workload**: `startup_basic` (5000 iterations, 9 ms duration)
- **Telemetry Records**: 56 records (42 Universal, 9 Conditional, 5 Unsupported)
- **Artifacts Saved**: 5 files (`dumpsys_meminfo.txt`, `dumpsys_gfxinfo.txt`, `dumpsys_thermalservice.txt`, `dumpsys_batterystats.txt`, `logcat.txt`)
