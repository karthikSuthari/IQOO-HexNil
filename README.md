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
- **Phase 4**: V0 Baseline Experiment (Software identity, environment snapshot, stabilization policy, baseline extraction, 95% Student's t CI, quality auditing, provenance hashes).
- **Phase 5**: V0 → V1 Differential Experiment (Safe APK update orchestration, identity verification, workload configuration lock, iteration-level run pairing, raw evidence preservation, differential quality audit).
- **Phase 6**: Statistical Comparison & Regression Detection (Run-level sample independence, matched difference analysis, metric direction registry, Student's t and deterministic bootstrap CIs, paired t-tests, Cohen's d effect sizes, versioned engineering thresholds, deterministic verdicts & severities, multiple-comparison policies, audit store).

---

## Phase 5: V0 → V1 Differential Experiment

The central principle of Phase 5 is:
> **MATCHED EVIDENCE > MORE EVIDENCE**
> 
> *SAME DEVICE + SAME WORKLOAD + SAME CONFIGURATION + CONTROLLED CONDITIONS $\rightarrow$ COMPARE V0 WITH V1*

Phase 5 is an **EXPERIMENT AND EVIDENCE LINKAGE** phase. It preserves the completed V0 evidence unchanged, applies the target V1 APK update via safe ADB package replacement, verifies the installed identity, executes the exact same locked workload configurations, captures V1 telemetry and raw diagnostics, links V0 and V1 runs iteration-by-iteration into `ComparisonRunPair`, and produces an audited comparison package.

> [!NOTE]
> Phase 5 prepares clean matched evidence. Final statistical regression detection, hypothesis testing, effect sizes, and p-values belong strictly to **Phase 6**.

### Phase 5 Architecture

```
+-------------------------------------------------------------------------+
| IMMUTABLE V0 BASELINE EVIDENCE (Read-Only)                              |
|   └── data/experiments/EXP-20260913-010/ (v0_software, runs, telemetry) |
+------------------------------------+------------------------------------+
                                     |
                       Workload Configuration Lock
                                     |
                                     v
+-------------------------------------------------------------------------+
| TARGET V1 APK UPDATE ORCHESTRATION (hexnil.diff.installer)              |
|   ├── Pre-install SHA-256 calculation & validation                      |
|   ├── Safe replace: adb install -r -d <apk>                             |
|   └── Post-install verification (dumpsys package, pm path, sha256sum)   |
+------------------------------------+------------------------------------+
                                     |
                         Stabilization & Snapshot
                                     |
                                     v
+-------------------------------------------------------------------------+
| CONTROLLED V1 EXECUTION (WorkloadExecutionEngine)                       |
|   ├── Execute exact same 5 workloads (startup, cpu, memory, scroll, vid)|
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
|   ├── v1_software.json            (V1 verified software identity)       |
|   ├── environment_comparison.json (Battery delta, thermal transitions)  |
|   ├── matched_pairs.json          (15 iteration-level matched run pairs)|
|   ├── quality.json                (ComparisonQualityReport audit)       |
|   ├── provenance.json             (SHA-256 integrity hashes)            |
|   ├── v1_telemetry/               (android.jsonl, adb.jsonl)            |
|   └── v1_artifacts/               (dumpsys, logcat diagnostic captures) |
+-------------------------------------------------------------------------+
```

### Differential CLI Commands

```bash
# 1. Inspect V0 baseline readiness for comparison
python -m hexnil diff inspect <V0_EXPERIMENT_ID>

# 2. Run complete V0 -> V1 differential experiment with APK update
python -m hexnil diff run <V0_EXPERIMENT_ID> --apk <V1_APK_PATH> --serial <SERIAL> --iterations 3

# 3. Show full differential comparison record
python -m hexnil diff show <COMPARISON_ID>

# 4. Show iteration-level matched run pairs
python -m hexnil diff pairs <COMPARISON_ID>

# 5. Show differential comparison quality audit and contamination flags
python -m hexnil diff quality <COMPARISON_ID>
```

---

## Verification & Testing

### Complete Test Suite (136 passed in 1.90s)
```bash
python -m pytest tests/ -v
```
- **Phase 1 & 2**: Device selection, ADB client, parsers, metadata, telemetry schema (35 tests)
- **Phase 3**: Deterministic workloads, canonical hashing, preconditions, engine, persistence, registry (30 tests)
- **Phase 4**: Baseline extractor, models, orchestrator, statistics, baseline CLI (35 tests)
- **Phase 5**: Differential models, installer, environment comparison, run matcher, quality audit, comparison store, orchestrator, diff CLI (36 tests)

### Real Hardware Differential Verification (vivo I2302)
- **Comparison ID**: `CMP-20260913-001`
- **V0 Baseline ID**: `EXP-20260913-010`
  - Version: `1.0` (Code `1`)
  - APK SHA-256: `c02a0430aa40552bf313cb04ffa1d33bacd063a96b98aee7ff5f773922f27fc8`
- **V1 Update ID**: `EXP-20260913-012`
  - Version: `1.1` (Code `2`)
  - APK SHA-256: `585523f10197d413c7938412769e0951bb631ea3483b78d54d8ce6067e19905c`
  - Install Outcome: `SUCCESS` (duration: 9632.8 ms)
- **Device**: `vivo I2302` (`adb-10BE38254U0003T-PJiTJm._adb-tls-connect._tcp`, Android 16 / SDK 36)
- **Workload Hashes**: 5/5 matched byte-for-byte (`startup_01`, `cpu_01`, `memory_01`, `scroll_01`, `video_power_01`)
- **Matched Run Pairs**: 15/15 matched (`PairStatus.MATCHED`), 0 unmatched, 0 invalid
- **Evidence Coverage**: `5/5 workloads have matched V0/V1 evidence`
- **Quality Verdict**: `[TRUSTED_DIFFERENTIAL_EVIDENCE]` (Clean Comparison: `YES`)
- **Evidence Artifacts**: Persisted under `data/experiments/comparisons/CMP-20260913-001/`

---

## Phase 6: Statistical Comparison & Regression Detection

The central principle of Phase 6 is:
> **STATISTICAL EVIDENCE > SINGLE MEASUREMENTS**
> 
> *A single noisy before/after measurement must not be called a regression.*
> 
> *The unit of execution is the workload run ($n=3$), NOT individual telemetry timestamps or frame events.*

Phase 6 is the **ANALYSIS AND REGRESSION DETECTION** layer that converts trusted matched V0/V1 run pairs into deterministic, auditable engineering verdicts.

### Supported Verdicts
- **`IMPROVEMENT`**: Statistical evidence supports improvement AND effect exceeds engineering threshold.
- **`REGRESSION`**: Statistical evidence supports deterioration AND effect exceeds engineering threshold.
- **`UNCHANGED`**: Evidence demonstrates effect does not exceed meaningful engineering threshold.
- **`INCONCLUSIVE`**: Insufficient samples ($n < 3$), high statistical uncertainty, non-significant p-value, or unknown metric direction.
- **`INVALID`**: Corrupted observations, unmatched pairs, or capability mismatches.

### Phase 6 Architecture

```
+-------------------------------------------------------------------------+
| PHASE 5 MATCHED DIFFERENTIAL EVIDENCE (Read-Only)                       |
|   └── data/experiments/comparisons/CMP-20260913-001/                    |
+------------------------------------+------------------------------------+
                                     |
                         Sample Extraction & Cleaning
                                     |
                                     v
+-------------------------------------------------------------------------+
| METRIC REGISTRY & ELIGIBILITY (hexnil.stats.registry)                   |
|   ├── LOWER_IS_BETTER: durations, heap MB, jank %, battery drop         |
|   ├── HIGHER_IS_BETTER: device memory available MB                      |
|   └── SUPPORTED_AND_ELIGIBLE vs INSUFFICIENT_DATA vs UNSUPPORTED        |
+------------------------------------+------------------------------------+
                                     |
                        Run-Level Paired Inference
                                     |
                                     v
+-------------------------------------------------------------------------+
| STATISTICAL ENGINE (hexnil.stats.engine)                                |
|   ├── Paired differences: D_i = V1_i - V0_i                             |
|   ├── Absolute & safe percentage deltas (guarded against zero/near-zero)|
|   ├── Effect size: Cohen's d_z for matched continuous pairs             |
|   ├── Uncertainty: Paired Student's t 95% CI & Deterministic Bootstrap  |
|   ├── Hypothesis testing: Paired Student's t-test (p-value, alpha=0.05) |
|   └── Multi-comparison correction: NONE, HOLM, FDR                      |
+------------------------------------+------------------------------------+
                                     |
                        Threshold & Verdict Decision
                                     |
                                     v
+-------------------------------------------------------------------------+
| VERDICT & SEVERITY CLASSIFIER (hexnil.stats.classifier / thresholds)    |
|   ├── Versioned thresholds: 5.0% minimum meaningful engineering change  |
|   ├── Severity bands: LOW (5%), MEDIUM (10%), HIGH (20%), CRITICAL (40%)|
|   └── Deterministic classification: REGRESSION / IMPROVEMENT / UNCHANGED|
+------------------------------------+------------------------------------+
                                     |
                             Storage Persistence
                                     |
                                     v
+-------------------------------------------------------------------------+
| STATISTICAL ANALYSIS STORE (CMP-*/statistical_analysis/)                |
|   ├── analysis.json       (Master statistical analysis document)        |
|   ├── metric_results.json (Individual metric evaluations & tests)       |
|   ├── exclusions.json     (Excluded pairs & reasons)                    |
|   ├── configuration.json  (Threshold & analysis versioning, seed)       |
|   └── provenance.json     (SHA-256 integrity hashes & input lineage)    |
+------------------------------------+------------------------------------+
```

### Statistical CLI Commands

```bash
# 1. Inspect comparison package readiness for statistical analysis
python -m hexnil stats inspect <COMPARISON_ID>

# 2. Run deterministic statistical analysis with optional correction and seed
python -m hexnil stats analyze <COMPARISON_ID> [--correction {none,holm,fdr}] [--seed 42]

# 3. Show persisted statistical analysis summary and verdict table
python -m hexnil stats show <COMPARISON_ID>

# 4. Show detailed metric comparisons and hypothesis test breakdown
python -m hexnil stats metrics <COMPARISON_ID> [--workload WORKLOAD_ID]

# 5. Show statistical analysis quality audit and evidence coverage
python -m hexnil stats quality <COMPARISON_ID>
```

---

## Verification & Testing

### Complete Test Suite (181 passed in 2.29s)
```bash
python -m pytest tests/ -q
```
- **Phase 1 & 2**: Device selection, ADB client, parsers, metadata, telemetry schema (35 tests)
- **Phase 3**: Deterministic workloads, canonical hashing, preconditions, engine, persistence, registry (30 tests)
- **Phase 4**: Baseline extractor, models, orchestrator, statistics, baseline CLI (35 tests)
- **Phase 5**: Differential models, installer, environment comparison, run matcher, quality audit, comparison store, orchestrator, diff CLI (36 tests)
- **Phase 6**: Statistical models, metric registry, threshold configurations, statistical engine, classifier, store persistence, reproducibility, orchestrator, stats CLI (45 tests)

### Real Hardware Statistical Validation (vivo I2302)
- **Comparison ID**: `CMP-20260913-001`
- **Analysis ID**: `STATS-CMP-20260913-001`
- **Device**: `vivo I2302` (Android 16 / SDK 36)
- **Evidence Coverage**: `9/13 claims/metrics with sufficient measured evidence`
- **Verdicts Breakdown**:
  - `UNCHANGED`: 8 metrics
  - `INCONCLUSIVE`: 5 metrics
  - `REGRESSION`: 0 (honestly reported; no manufactured regression)
  - `IMPROVEMENT`: 0
  - `INVALID`: 0
- **Key Engineering Decisions**:
  - `video_power_01` duration (+377.2 ms, +3.0%): $p=0.0116$ is statistically significant, but the +3.0% effect is below the 5.0% engineering threshold $\rightarrow$ **`[UNCHANGED]`**.
  - `startup_01` startup duration (+225.9 ms, +22.9%): raw delta looks large, but high sample variance results in $p=0.2196$ (non-significant, 95% CI spans zero: [-324.9, +776.6]) $\rightarrow$ **`[INCONCLUSIVE]`**.
  - `cpu_01` compute duration (-22.5 ms, -0.7%, $p=0.7648$) $\rightarrow$ **`[UNCHANGED]`**.
  - `scroll_01` scroll duration (-72.0 ms, -1.6%, $p=0.5099$) $\rightarrow$ **`[UNCHANGED]`**.
- **Determinism & Reproducibility**: Tested with fixed random seed `42` $\rightarrow$ **100% byte-for-byte identical output verified**.
- **Evidence Artifacts**: Persisted under `data/experiments/comparisons/CMP-20260913-001/statistical_analysis/`

