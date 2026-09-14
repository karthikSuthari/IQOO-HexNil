package com.example.iqoo_hexnil.data

enum class VerdictType(val label: String) {
    IMPROVEMENT("IMPROVEMENT"),
    REGRESSION("REGRESSION"),
    UNCHANGED("UNCHANGED"),
    INCONCLUSIVE("INCONCLUSIVE"),
    INVALID("INVALID")
}

enum class MetricStatus {
    VALID,
    INCONCLUSIVE,
    UNSUPPORTED
}

enum class SeverityLevel {
    NONE,
    LOW,
    MEDIUM,
    HIGH,
    CRITICAL
}

enum class ClaimRiskLevel(val label: String) {
    HIGH("High Risk"),
    MODERATE("Moderate Risk"),
    LOW("Low Risk")
}

enum class WorkloadPriority(val label: String) {
    HIGH("HIGH"),
    MEDIUM("MEDIUM"),
    LOW("LOW")
}

enum class WorkloadStatus(val label: String) {
    COMPLETED("Completed"),
    RUNNING("Running"),
    QUEUED("Queued"),
    SKIPPED("Skipped"),
    INCONCLUSIVE("Inconclusive"),
    FAILED("Failed")
}

data class ReleaseClaim(
    val id: String,
    val title: String,
    val description: String,
    val subsystem: String,
    val expectedDirection: String,
    val riskLevel: ClaimRiskLevel,
    val recommendedWorkload: String,
    val predictionSource: String,
    val targetMetric: String,
    val validationStatus: String = "UNCHANGED",
    val priority: WorkloadPriority = WorkloadPriority.MEDIUM
)

data class WorkloadDefinition(
    val id: String,
    val name: String,
    val description: String,
    val priority: WorkloadPriority,
    val status: WorkloadStatus,
    val matchedRunsCount: Int,
    val action: String,
    val configHash: String,
    val lastDurationMs: Double? = null,
    val purpose: String = description,
    val isSelected: Boolean = true,
    val evidenceAvailability: String = "AVAILABLE"
)

data class StatisticalMetricResult(
    val workloadId: String,
    val metricName: String,
    val displayName: String,
    val unit: String,
    val direction: String,
    val sampleCount: Int,
    val v0Mean: Double?,
    val v1Mean: Double?,
    val v0Median: Double?,
    val v1Median: Double?,
    val v0Values: List<Double>,
    val v1Values: List<Double>,
    val pairedDifferences: List<Double>,
    val absoluteDelta: Double?,
    val percentDelta: Double?,
    val ciLower: Double?,
    val ciUpper: Double?,
    val pValue: Double?,
    val effectSize: Double?,
    val effectSizeMethod: String,
    val thresholdPercent: Double?,
    val thresholdAbsolute: Double?,
    val verdict: VerdictType,
    val severity: SeverityLevel,
    val reason: String,
    val status: MetricStatus,
    val v0RunIds: List<String>,
    val v1RunIds: List<String>,
    val comparisonId: String
) {
    val key: String get() = "${workloadId}_${metricName}"
}

data class ComparisonAnalysis(
    val analysisId: String,
    val comparisonId: String,
    val v0ExperimentId: String,
    val v1ExperimentId: String,
    val deviceModel: String,
    val deviceSerial: String,
    val buildFingerprint: String,
    val v0ApkSha256: String,
    val v1ApkSha256: String,
    val metricsAnalyzed: Int,
    val metricsEligible: Int,
    val metricsInconclusive: Int,
    val metricsUnchanged: Int,
    val metricsRegressions: Int,
    val metricsImprovements: Int,
    val metricsUnsupported: Int,
    val evidenceCoverage: String,
    val summaryVerdict: String,
    val metricResults: List<StatisticalMetricResult>,
    val evidenceState: String = "HISTORICAL_VERIFIED",
    val recordTimestamp: String = "2026-09-13T09:00:00Z"
)

enum class HardwareEvidenceState {
    LIVE,
    UNAVAILABLE,
    UNSUPPORTED,
    STALE_CACHED
}

data class DeviceHardwareInfo(
    val manufacturer: String,
    val model: String,
    val codename: String,
    val androidRelease: String,
    val sdkInt: Int,
    val buildId: String,
    val abi: String,
    val fingerprint: String,
    val batteryPercent: Int?,
    val chargingState: String,
    val thermalStatus: String,
    val universalMetricsCount: Int,
    val conditionalMetricsCount: Int,
    val unsupportedMetricsCount: Int,
    val adbConnected: Boolean,
    val evidenceState: HardwareEvidenceState = HardwareEvidenceState.UNAVAILABLE
)

// Phase 8: Evidence-Grounded AI Analyst Models

enum class ExplanationSource(val label: String) {
    GROQ_AI("AI EXPLANATION — GROQ"),
    DETERMINISTIC_ANALYSIS("DETERMINISTIC ANALYSIS"),
    DETERMINISTIC_FALLBACK("DETERMINISTIC FALLBACK")
}

data class ClaimAssessment(
    val claimId: String,
    val claimText: String,
    val targetMetric: String,
    val status: String, // "SUPPORTED", "CONTRADICTED", "INCONCLUSIVE", "UNSUPPORTED_METRIC"
    val explanation: String
)

data class EvidenceReference(
    val referenceId: String,
    val type: String, // "metric", "workload", "comparison", "experiment", "claim"
    val identifier: String,
    val artifactPath: String?,
    val description: String
)

data class AiExplanation(
    val explanationId: String,
    val comparisonId: String,
    val source: ExplanationSource,
    val model: String?,
    val verdict: String,
    val severity: String,
    val summary: String,
    val claimAssessments: List<ClaimAssessment>,
    val observedChanges: List<String>,
    val statisticalInterpretation: String,
    val limitations: List<String>,
    val recommendedNextStep: String,
    val evidenceReferences: List<EvidenceReference>,
    val isCached: Boolean,
    val createdAt: String
)

// =========================================================================
// OS Update Impact Intelligence Platform Models (Phases 9 - 14)
// =========================================================================

enum class HexnilLifecycleState(val step: Int, val label: String, val description: String) {
    DEVICE_CONNECTED(1, "Device Connected", "Physical Android target discovered and ADB bridge established"),
    MONITORING(2, "Monitoring Active", "Background observation tracking system props and idle thermals"),
    BASELINE_BUILDING(3, "Building Baseline", "Capturing ambient device noise, memory pressure, and stability"),
    PREDICTION_READY(4, "Prediction Ready", "OS release claims parsed into risk bands and prioritized workloads"),
    V0_LOCKED(5, "V0 Baseline Locked", "Pre-update state and repeated workload runs cryptographically locked"),
    AWAITING_UPDATE(6, "Awaiting Update", "Observing device for real OS, firmware, or security patch transition"),
    UPDATE_DETECTED(7, "Update Detected", "Genuine OS transition detected via boot count and build properties"),
    POST_UPDATE_STABILIZATION(8, "Stabilizing Device", "Post-reboot cooldown, thermal recovery, and runtime settling"),
    VALIDATING(9, "Validating Probes", "Executing matched workload probes under byte-locked configurations"),
    ANALYZING(10, "Statistical Analysis", "Paired differences, Student's t-tests, bootstrap CIs, and FDR control"),
    CLASSIFYING(11, "Issue Classification", "Cross-referencing regressions against pre-update baseline anomalies"),
    EVALUATING(12, "Evaluating Predictions", "Validating pre-update claim forecasts against observed evidence"),
    REPORT_READY(13, "Report Ready", "Comprehensive 10-point OS Update Impact Evidence Dossier available"),
    HISTORICAL_RESULTS(14, "Historical Record", "Update transition archived into device lifetime update memory")
}

enum class TransitionType(val label: String) {
    MAJOR_OS("Major OS Upgrade"),
    MINOR_OTA("Minor OTA Update"),
    SECURITY_PATCH("Security Patch Level"),
    BUILD_INCREMENT("System Build Increment"),
    VENDOR_UPDATE("Vendor / Kernel Update"),
    UNKNOWN("Unknown Transition")
}

data class DeviceOsIdentity(
    val manufacturer: String,
    val model: String,
    val codename: String,
    val androidVersion: String,
    val sdkInt: Int,
    val buildId: String,
    val securityPatchLevel: String,
    val buildFingerprint: String,
    val kernelVersion: String = "6.1.75-android16-11-g897f1a",
    val bootCount: Int = 42,
    val capturedAt: String = "2026-09-14T08:00:00Z"
)

data class UpdateTransition(
    val transitionId: String,
    val transitionType: TransitionType,
    val preState: DeviceOsIdentity,
    val postState: DeviceOsIdentity,
    val detectedAt: String,
    val rebootContext: String,
    val durationMinutes: Int = 12
)

enum class AnomalyType(val label: String) {
    BATTERY_DRAIN("Battery Drain Spike"),
    THERMAL_THROTTLE("Thermal Throttle Watch"),
    JANK_SPIKE("Frame Jank Spike"),
    MEMORY_LEAK("Memory Allocation Drift"),
    STARTUP_DEGRADATION("Cold Launch Jitter"),
    CPU_SPIKE("Background CPU Spike")
}

data class PreUpdateAnomaly(
    val anomalyId: String,
    val anomalyType: AnomalyType,
    val metricName: String,
    val severity: SeverityLevel,
    val description: String,
    val baselineMean: Double,
    val observedZScore: Double,
    val sampleTimestamp: String
)

enum class IssueCategory(val label: String, val isRegression: Boolean) {
    NEW_REGRESSION("New OS Regression", true),
    FIXED("Resolved by Update", false),
    PERSISTED("Pre-existing (Persisted)", false),
    PERSISTED_WORSENED("Pre-existing (Worsened)", true),
    NEW_IMPROVEMENT("New Improvement", false),
    UNCHANGED("Unchanged / Stable", false),
    INSUFFICIENT_EVIDENCE("Insufficient Evidence", false)
}

data class IssueClassification(
    val classificationId: String,
    val metricName: String,
    val displayName: String,
    val workloadId: String,
    val category: IssueCategory,
    val preUpdateAnomalyExisted: Boolean,
    val preUpdateAnomalyDescription: String? = null,
    val postUpdateVerdict: VerdictType,
    val postUpdateSeverity: SeverityLevel,
    val percentDelta: Double?,
    val pValue: Double?,
    val explanation: String
)

data class IssueReportSummary(
    val reportId: String,
    val totalClassified: Int,
    val newRegressionsCount: Int,
    val fixedCount: Int,
    val persistedCount: Int,
    val improvementsCount: Int,
    val unchangedCount: Int,
    val inconclusiveCount: Int,
    val classifications: List<IssueClassification>
)

enum class EvaluationHit(val label: String, val isAccurate: Boolean) {
    TRUE_POSITIVE("True Positive (Correctly Predicted)", true),
    TRUE_NEGATIVE("True Negative (Correct Stability)", true),
    FALSE_POSITIVE("False Alarm (Overestimated Risk)", false),
    FALSE_NEGATIVE("Unpredicted Issue (Underestimated)", false)
}

data class PredictionOutcome(
    val claimId: String,
    val claimText: String,
    val targetMetric: String,
    val predictedRisk: ClaimRiskLevel,
    val actualVerdict: VerdictType,
    val hitType: EvaluationHit,
    val explanation: String
)

data class PredictionEvaluationSummary(
    val totalEvaluated: Int,
    val truePositives: Int,
    val trueNegatives: Int,
    val falsePositives: Int,
    val falseNegatives: Int,
    val accuracyPercent: Double,
    val precisionPercent: Double,
    val recallPercent: Double,
    val f1Score: Double,
    val outcomes: List<PredictionOutcome>
)

enum class ExecutiveVerdict(val label: String, val summary: String) {
    SAFE_TO_ROLLOUT("SAFE TO ROLLOUT", "No regressions detected across key subsystems. Metrics verified stable within engineering tolerances."),
    UPDATE_HAS_REGRESSIONS("UPDATE HAS REGRESSIONS", "Statistically significant regressions detected in one or more subsystems."),
    CRITICAL_REGRESSIONS("CRITICAL REGRESSIONS", "High-severity performance or stability regressions detected. Rollback recommended."),
    INCONCLUSIVE("INCONCLUSIVE", "High physical noise or insufficient iteration power prevents definitive sign-off.")
}

data class FinalEvidenceReport(
    val reportId: String,
    val generatedAt: String,
    val deviceSerial: String,
    val deviceModel: String,
    val transition: UpdateTransition,
    val executiveVerdict: ExecutiveVerdict,
    val evidenceCoverage: String,
    val preUpdateSummary: String,
    val preUpdateAnomalies: List<PreUpdateAnomaly>,
    val predictionsSummary: PredictionEvaluationSummary,
    val issueReport: IssueReportSummary,
    val statisticalComparison: ComparisonAnalysis,
    val recommendations: List<String>
)

data class HistoricalUpdateRecord(
    val updateId: String,
    val transitionType: TransitionType,
    val fromBuild: String,
    val toBuild: String,
    val patchDate: String,
    val timestamp: String,
    val verdict: ExecutiveVerdict,
    val regressionsCount: Int,
    val improvementsCount: Int,
    val resolvedCount: Int
)

