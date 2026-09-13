# HEXNIL — Mobile Release-Validation Intelligence System

Hexnil is a mobile release-validation intelligence system. Its core question is:
> *“Did the update do what it promised, and what did it accidentally break?”*

The overall product loop is:
```
Predict → Prioritize → Validate → Explain → Learn
```

- **Phase 1**: Android Device Foundation (ADB discovery, serial selection, health checks, metadata capture, experiment IDs, JSON persistence).
- **Phase 2**: Universal Telemetry Collection (On-device Kotlin/Compose engine, host-side ADB bridge, deterministic workload foundation, capability taxonomy, JSONL persistence, artifact capture).
- **Phase 3**: Deterministic Workload Engine (Declarative workload definitions, canonical configuration hashing, controlled preconditions, monotonic execution engine, repeated iterations, run models, workload suite & registry).

---

## Phase 3 Architecture: Deterministic Workload Engine

```
+-------------------------------------------------------------------------+
| WORKLOAD REGISTRY & DEFINITIONS (Host: hexnil/workloads/definitions/)   |
|   ├── startup_01.json        (Cold launch timing & readiness)           |
|   ├── cpu_01.json            (Deterministic SHA-256 CPU hashing)        |
|   ├── memory_01.json         (Heap allocation, touch & GC release)      |
|   ├── scroll_01.json         (Fixed-distance vertical UI scrolling)     |
|   └── video_power_01.json    (Local media playback / battery discharge) |
+------------------------------------+------------------------------------+
                                     |
                       Load, Validate, Canonical Hash
                                     |
                                     v
+-------------------------------------------------------------------------+
| HOST EXECUTION ENGINE (Python 3.11+: hexnil.workloads.engine)           |
|   ├── PreconditionEvaluator  (Screen state, battery %, thermals, clean) |
|   ├── Monotonic Timer        (time.perf_counter_ns duration measurement)|
|   ├── Iteration Controller   (Unique run IDs, identical config hash)    |
|   └── TelemetryBridge Link   (Phase 2 snapshots around execution steps) |
+------------------------------------+------------------------------------+
                                     |
                          am start / input / run-as
                                     |
                                     v
+-------------------------------------------------------------------------+
| TARGET ANDROID DEVICE (Hardware: vivo I2302 / Android 16 / SDK 36)      |
|   └── Companion App (com.example.iqoo_hexnil)                           |
|         ├── WorkloadRunner   (On-device compute, memory, and timing)    |
|         └── TelemetryEngine  (Pre- & post-run telemetry snapshots)      |
+------------------------------------+------------------------------------+
                                     |
                             Store Persistence
                                     |
                                     v
+-------------------------------------------------------------------------+
| LOCAL EXPERIMENT & RUN STORE (data/experiments/EXP-YYYYMMDD-XXX/)       |
|   ├── metadata.json                                                     |
|   ├── workload_runs/<workload_id>/RUN-*.json                            |
|   ├── telemetry/android.jsonl & adb.jsonl                               |
|   └── artifacts/ (dumpsys, logcat, traces)                              |
+-------------------------------------------------------------------------+
```

---

## Workload Suite

| Workload ID | Version | Configuration Hash | Description | Preconditions |
|---|---|---|---|---|
| `startup_01` | `1.0.0` | `085d1a2b54a0c08d` | Cold application launch and initial rendering readiness | Screen ON, Battery >= 15%, Thermal <= Moderate, Clean state (force-stop) |
| `cpu_01` | `1.0.0` | `6e7f4490bb4eef72` | Deterministic SHA-256 CPU hashing with fixed seed (10,000 ops) | Screen ON, Battery >= 15%, Thermal <= Moderate |
| `memory_01` | `1.0.0` | `d57a0caea43ad47f` | Memory allocation (50 MB), touch pattern, and GC release cycle | Screen ON, Battery >= 15% |
| `scroll_01` | `1.0.0` | `be7217ff86a2ef88` | Fixed-distance vertical scrolling over local view items | Screen ON, Battery >= 15% |
| `video_power_01`| `1.0.0`| `b794a8f175d4aa46` | Deterministic local media playback & battery discharge proxy | Screen ON, Battery >= 15% |

---

## Canonical Configuration Hashing

Workload configurations are serialized to canonical JSON (sorted keys recursively, strict compact separators) and hashed via SHA-256:
- **Hash Stability**: The hash remains identical across runs and machines as long as the workload configuration has not changed.
- **Hash Sensitivity**: Changing any parameter (e.g. `operations_count` from 10,000 to 10,001) produces a completely different hash.
- **Run Identity**: Persisted run records include `workload_id`, `workload_version`, and `configuration_hash`.

---

## Controlled Preconditions Model

Preconditions are verified before executing workload steps. Each produces a `PreconditionResult`:
- `SATISFIED`: Precondition was met or automatically enforced.
- `NOT_SATISFIED`: Precondition failed (run is flagged as `PRECONDITION_FAILED` and steps do not execute).
- `NOT_SUPPORTED`: Precondition is not supported by the current device/evaluator.
- `ERROR`: Unexpected error during evaluation.

Supported Preconditions:
- `screen_on` (boolean): Display awake and powered on.
- `battery_min_percent` (integer): Charge level threshold.
- `charging_state` (`"discharging"`, `"charging"`, `"any"`).
- `thermal_state_max` (`"none"`, `"light"`, `"moderate"`, `"severe"`).
- `app_clean_state` (boolean): Force-stop prior to launch.

---

## Monotonic Duration Timing

- **Durations**: Computed using high-precision monotonic timers (`time.perf_counter_ns()` on host, `SystemClock.elapsedRealtime()` on Android). Monotonic clocks never jump or drift when system wall-clocks synchronize.
- **Timestamps**: All persisted timestamps (`started_at`, `ended_at`) strictly use UTC ISO-8601 formatting.

---

## Storage Structure

```
data/
  experiments/
    EXP-20260913-007/
      metadata.json
      workload_runs/
        cpu_01/
          RUN-20260913-080912-001-A231.json
          RUN-20260913-080923-002-AF2F.json
          RUN-20260913-080934-003-BC55.json
      telemetry/
        android.jsonl
        adb.jsonl
      artifacts/
        dumpsys_batterystats.txt
        dumpsys_gfxinfo.txt
        dumpsys_meminfo.txt
        dumpsys_thermalservice.txt
        logcat.txt
```

---

## CLI Usage

### Workload Management
```bash
# List all registered declarative workloads
python -m hexnil workload list

# Inspect workload definition and configuration hash
python -m hexnil workload show cpu_01

# Validate workload schema and preconditions
python -m hexnil workload validate cpu_01
```

### Workload Execution
```bash
# Run a single iteration against a connected device
python -m hexnil workload run startup_01 --serial <SERIAL>

# Run repeated iterations with telemetry collection
python -m hexnil workload run cpu_01 --serial <SERIAL> --iterations 3

# Output execution runs as JSON
python -m hexnil workload run cpu_01 --serial <SERIAL> --iterations 3 --json
```

---

## Phase 4: V0 Baseline Experiment

Phase 4 builds the trusted, reproducible V0 baseline experiment before the target software update:

```bash
# Execute full V0 baseline suite across all 5 workloads (3 iterations each)
python -m hexnil baseline run --serial <SERIAL> --iterations 3

# Show complete baseline experiment record and audit
python -m hexnil baseline show <EXPERIMENT_ID>

# Show derived baseline metrics and 95% confidence intervals
python -m hexnil baseline summary <EXPERIMENT_ID>

# Show quality audit report and contamination flags
python -m hexnil baseline quality <EXPERIMENT_ID>
```

### Persisted Baseline Directory Layout
```
data/experiments/EXP-YYYYMMDD-XXX/
  metadata.json        # ExperimentRecord (phase: "04_v0_baseline")
  software.json        # V0SoftwareIdentity (APK SHA-256, package, build ID)
  environment.json     # EnvironmentSnapshot (battery, thermal, idle state)
  workloads.json       # Workload configuration hashes and descriptions
  workload_runs/       # Individual WorkloadRun JSON files per workload iteration
  telemetry/           # android.jsonl and adb.jsonl raw unified telemetry
  artifacts/           # Raw dumpsys (meminfo, gfxinfo, batterystats) and logcat
  baseline/
    metrics.json       # Extracted metrics, descriptive stats, and 95% CI
    quality.json       # QualityReport with evidence coverage & contamination audit
    provenance.json    # ProvenanceRecord with SHA-256 integrity hashes
```

---

## Verification & Testing

### Unit Test Suite (100 passed in 1.46s)
```bash
python -m pytest tests/ -v
```
- Workload domain models, canonical serialization, and SHA-256 hash stability
- Registry discovery and schema validation
- Precondition evaluation logic (screen, battery, charging, thermals)
- Monotonic execution engine, step ordering, timeouts, and multi-iteration runs
- WorkloadRun persistence, loading, and filtering
- Baseline models, V0 software identity, and environment condition snapshots
- Baseline statistics: percentiles, descriptive stats, 1.5*IQR outlier tagging, 95% Student's t CI
- Baseline metric extractor, small-sample handling, and invalid-run exclusion
- Baseline orchestrator, device stabilizer, and quality auditing
- CLI argument parsing, subcommands dispatch, and JSON output formatting

### Real Hardware Verification (vivo I2302)
- **Experiment ID**: `EXP-20260913-010`
- **Device**: vivo I2302 (`adb-10BE38254U0003T-PJiTJm._adb-tls-connect._tcp`, Android 16 / SDK 36)
- **Build Fingerprint**: `iQOO/I2302T/I2302:16/BP2A.250605.031.A3/compiler260714114720:user/release-keys`
- **V0 Software Package**: `com.example.iqoo_hexnil` (Version 1.0, Code 1)
- **APK SHA-256**: `c02a0430aa40552bf313cb04ffa1d33bacd063a96b98aee7ff5f773922f27fc8`
- **Workload Suite**: `startup_01`, `cpu_01`, `memory_01`, `scroll_01`, `video_power_01` (3 iterations each)
- **Results**: 15 runs requested, 15 completed, 15 VALID (`SUCCESS`), 0 invalid, 0 failed, 0 precondition failures
- **Evidence Coverage**: `5/5 workloads validated with evidence`
- **Summary Verdict**: `[TRUSTED_V0_BASELINE]` (Clean Baseline: `YES`)
- **Telemetry & Artifacts**: 840 telemetry records, 75 raw diagnostic artifact files
- **Baseline Outputs**: `data/experiments/EXP-20260913-010/baseline/`

