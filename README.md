# HEXNIL — Mobile OS Update Impact Intelligence System

HexNil is an **AI-powered Mobile OS Update Impact Analyzer**. Its core aim is:

> **To intelligently detect, analyze, and predict how mobile OS updates affect an Android app’s performance and behavior—before and after the update.**

---

### 🎯 The Core Question
> *“After this Android update, did our app or mobile break or degrade, what changed, why did it happen, and how serious is it?”*

---

### 🔄 The Product Loop
```
Predict → Prioritize → Validate → Explain → Learn
```

```
+-----------------------------------------------------------------------------+
|                                  HEXNIL LOOP                                |
|                                                                             |
|  [ PREDICT ]    Parse OS changelogs / release notes to forecast risk        |
|       │                                                                     |
|       ▼                                                                     |
|  [ PRIORITIZE ] Rank and select targeted workload probes                    |
|       │                                                                     |
|       ▼                                                                     |
|  [ VALIDATE ]   Execute matched V0 (Pre-OS) vs V1 (Post-OS) experiments     |
|       │                                                                     |
|       ▼                                                                     |
|  [ EXPLAIN ]    AI / LLM root-cause synthesis & severity assessment         |
|       │                                                                     |
|       ▼                                                                     |
|  [ LEARN ]      Feed observed regressions back to refine claim predictions  |
+-----------------------------------------------------------------------------+
```

---

## Architecture Overview

HexNil uses a standardized on-device Android application (`com.example.iqoo_hexnil`) as an **instrumented workload probe**. Rather than testing software in a vacuum, the probe executes realistic workloads (UI 120Hz scrolling, CPU stress, memory churn, startup latency, and video playback) across OS builds to capture system-level shifts in scheduling, thermals, power, memory pressure, and frame rendering.

### End-to-End Pipeline Phases:
- **Phase 1: Android Device Foundation**: ADB device discovery, serial selection, health checks, thermal/battery monitoring, and JSON metadata capture.
- **Phase 2: Universal Telemetry Collection**: On-device Compose engine, host-side ADB telemetry bridge (`dumpsys gfxinfo`, `meminfo`, `batterystats`, logcat), capability taxonomy, and streaming JSONL persistence.
- **Phase 3: Deterministic Workload Engine**: Declarative workload definitions, canonical configuration hashing, controlled preconditions, monotonic execution engine, and repeated iteration control.
- **Phase 4: V0 Baseline Experiment**: Software & OS identity capture (`ro.build.id`, `ro.build.version.release`, `ro.build.fingerprint`), device stabilization enforcement, 95% Student's t baseline extraction, and quality auditing.
- **Phase 5: V0 → V1 Differential Experiment**: Matched execution across updates—supporting both **Mobile OS Updates** (`--os-update`) and **App Updates** (`--apk`)—with workload configuration lock, iteration-level run pairing, environment drift auditing, and raw evidence preservation.
- **Phase 6: Statistical Comparison & Regression Detection**: Run-level sample independence, matched difference analysis ($D_i = V1_i - V0_i$), Cohen’s $d_z$ effect sizes, paired Student’s $t$-tests, deterministic bootstrap CIs, versioned engineering thresholds, and deterministic verdicts (`REGRESSION`, `IMPROVEMENT`, `UNCHANGED`, `INCONCLUSIVE`).
- **Phase 7: Claim Intelligence & AI Explanation**: Ingests release notes/changelogs, maps claims to subsystems (Battery, Thermal, Startup, Memory, UI Jank, CPU), predicts risk bands, and generates LLM-powered root-cause impact explanations.

---

## Core Principle: *"Matched Evidence > More Evidence"*

$$\text{Same Physical Device} + \text{Same Workload} + \text{Same Configuration} + \text{Controlled Preconditions} \rightarrow \text{Direct Comparison } (V0 \leftrightarrow V1)$$

A single noisy benchmark is never called a regression. The unit of execution is the controlled workload run iteration ($n \ge 3$), eliminating thermal and battery confounders.

---

## Phase 5: Differential Experiment Engine

Phase 5 coordinates the transition between the baseline ($V0$) and the updated state ($V1$):

```
+-------------------------------------------------------------------------+
| IMMUTABLE V0 BASELINE EVIDENCE (Pre-Update OS / App State)              |
|   └── data/experiments/EXP-20260913-010/                                |
+------------------------------------+------------------------------------+
                                     |
                        Workload Configuration Lock
                                     |
                                     v
+-------------------------------------------------------------------------+
| UPDATE VERIFICATION & TRANSITION                                        |
|   ├── [OS Mode]:  Verify Android build transition (V0 -> V1)            |
|   │               Check probe app presence (com.example.iqoo_hexnil)    |
|   └── [APK Mode]: Safe replace (adb install -r -d <apk>)                |
+------------------------------------+------------------------------------+
                                     |
                          Stabilization & Snapshot
                                     |
                                     v
+-------------------------------------------------------------------------+
| CONTROLLED V1 EXECUTION (WorkloadExecutionEngine)                       |
|   ├── Execute exact same workloads (startup, cpu, memory, scroll, video)|
|   └── Capture unified V1 telemetry & raw diagnostics                    |
+------------------------------------+------------------------------------+
                                     |
                             Run Pair Matching
                                     |
                                     v
+-------------------------------------------------------------------------+
| RUN MATCHER & QUALITY AUDIT (hexnil.diff.matcher / quality)             |
|   ├── WorkloadRunMatcher: Pair (workload_id, iteration) -> MATCHED      |
|   ├── Contamination detection & environment drift comparison            |
|   └── ComparisonQualityReport: [TRUSTED_DIFFERENTIAL_EVIDENCE]          |
+------------------------------------+------------------------------------+
                                     |
                             Storage Persistence
                                     |
                                     v
+-------------------------------------------------------------------------+
| DIFFERENTIAL COMPARISON STORE (data/experiments/comparisons/CMP-*)      |
|   ├── comparison.json             (Master comparison record)            |
|   ├── v0_reference.json           (Immutable reference to V0 baseline)  |
|   ├── v1_software.json            (V1 verified OS / software identity)  |
|   ├── environment_comparison.json (Battery delta, thermal transitions)  |
|   ├── matched_pairs.json          (Iteration-level matched run pairs)   |
|   ├── quality.json                (ComparisonQualityReport audit)       |
|   ├── provenance.json             (SHA-256 integrity hashes)            |
|   ├── v1_telemetry/               (android.jsonl, adb.jsonl)            |
|   └── v1_artifacts/               (dumpsys, logcat diagnostic captures) |
+-------------------------------------------------------------------------+
```

---

## Quickstart & CLI Commands

### 1. Pre-Update OS Baseline ($V0$)
Run the standardized workload suite on the current OS build before updating:
```bash
# Run baseline experiment on connected device
python -m hexnil baseline run --serial <SERIAL> --iterations 3

# Inspect baseline quality
python -m hexnil baseline show <V0_EXPERIMENT_ID>
```

### 2. Differential Experiment ($V0 \rightarrow V1$)

#### Option A: Mobile OS Update Mode (Recommended for OS/OEM Validation)
After applying the system OS update / OTA to the device:
```bash
python -m hexnil diff run <V0_EXPERIMENT_ID> --os-update --serial <SERIAL> --iterations 3
```

#### Option B: Mobile App (APK) Update Mode
When testing a new release APK directly:
```bash
python -m hexnil diff run <V0_EXPERIMENT_ID> --apk path/to/v1.apk --serial <SERIAL> --iterations 3
```

#### Inspecting Differential Results:
```bash
# Show complete differential comparison record
python -m hexnil diff show <COMPARISON_ID>

# Show matched iteration pairs
python -m hexnil diff pairs <COMPARISON_ID>

# Show differential quality audit and contamination flags
python -m hexnil diff quality <COMPARISON_ID>
```

### 3. Statistical Analysis & Regression Detection (Phase 6)
```bash
# Inspect comparison readiness for statistical analysis
python -m hexnil diff stats inspect <COMPARISON_ID>

# Run deterministic statistical inference (paired t-tests, bootstrap CIs, Cohen's d)
python -m hexnil stats analyze <COMPARISON_ID> --correction fdr --seed 42

# View regression verdicts and severity breakdown
python -m hexnil stats show <COMPARISON_ID>

# View granular metric comparisons
python -m hexnil stats metrics <COMPARISON_ID>
```

### 4. Claim Intelligence & Prediction (Phase 7)
```bash
# Inspect OS release notes and extract candidate claims
python -m hexnil predict inspect "Optimized battery standby and smoother 120Hz display transitions."

# Generate prioritized workload plan and pre-update risk scores
python -m hexnil predict analyze path/to/release_notes.txt
```

### 5. AI Explanation & Root-Cause Analysis
```bash
# Generate AI explanation for detected regressions
python -m hexnil explain generate <COMPARISON_ID>

# Display synthesized report
python -m hexnil explain show <COMPARISON_ID>
```

### 6. Background Monitor & OS State Tracking (Phase 9)
```bash
# Snapshot current Android OS state
python -m hexnil monitor status

# Start continuous OS update polling session
python -m hexnil monitor start --device-serial <SERIAL> --poll-interval 10

# Detect OS update transitions and anomalies
python -m hexnil monitor detect --session-id <SESSION_ID>
```

### 7. Issue Classification & Prediction Evaluation (Phases 10 & 11)
```bash
# Cross-reference regressions against pre-update anomalies (classification)
# Evaluates whether an issue is an OS update regression, preexisting, or resolved
# Evaluates claim prediction accuracy (True Positive, False Negative, etc.)
```

### 8. Final Evidence Report (Phase 12)
```bash
# Generate comprehensive OS Update Impact Report
python -m hexnil report generate <COMPARISON_ID> --output report.json

# View formatted markdown report
python -m hexnil report show <REPORT_ID>
```

---

## Verification & Test Suite

### Full Automated Suite (347 passed)
```bash
python -m pytest tests/ -v
```

- **Phase 1 & 2**: Device selection, ADB client, parsers, metadata, telemetry schema (35 tests)
- **Phase 3**: Deterministic workloads, canonical hashing, preconditions, engine, persistence, registry (30 tests)
- **Phase 4**: Baseline extractor, models, orchestrator, statistics, baseline CLI (35 tests)
- **Phase 5**: Differential models, OS update orchestration, installer, environment comparison, run matcher, quality audit, comparison store, diff CLI (39 tests)
- **Phase 6**: Statistical models, metric registry, threshold configurations, statistical engine, classifier, store persistence, reproducibility, orchestrator, stats CLI (45 tests)
- **Phase 7 & Explain**: Claim ingestion, subsystem mapping, risk band prediction, validation planner, LLM explanation orchestrator, and fallback audits (58 tests)
- **Phase 9 (Monitor)**: Session models, OS state tracker, pre-update anomaly detector, persistence store (60 tests)
- **Phase 10 (Classify)**: Issue classification models and cross-reference classifier (22 tests)
- **Phase 11 (Evaluate)**: Prediction evaluation models and accuracy evaluator (16 tests)
- **Phase 12 (Report)**: Final evidence report models and generator (18 tests)

---

## Real Hardware Verification (iQOO / vivo I2302)
- **Target Device**: `vivo I2302` (Qualcomm Snapdragon / OriginOS / Android 16)
- **Tested Workloads**: `startup_01`, `cpu_01`, `memory_01`, `scroll_01`, `video_power_01`
- **Matched Execution**: 100% byte-for-byte configuration hash locks verified across all iterations
- **Verdict Integrity**: Deterministic statistical classification with zero false regression manufacturing

