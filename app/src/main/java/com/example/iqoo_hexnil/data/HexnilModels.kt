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
    val targetMetric: String
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
    val lastDurationMs: Double? = null
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
    val metricResults: List<StatisticalMetricResult>
)

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
    val adbConnected: Boolean
)
