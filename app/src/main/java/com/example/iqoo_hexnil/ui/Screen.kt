package com.example.iqoo_hexnil.ui

enum class BottomTab(
    val label: String,
    val iconSymbol: String,
    val title: String
) {
    OVERVIEW("Overview", "⚡", "OS Update Impact Intelligence"),
    MONITOR("Monitor", "📡", "OS Monitoring & Anomaly Engine"),
    UPDATES("Updates", "🔄", "OS Update Lifecycle & Transitions"),
    RESULTS("Results", "📊", "Statistical Verification & Issues"),
    DEVICE("Device", "📱", "Hardware & Telemetry Capabilities")
}

sealed class AppDestination(val title: String) {
    // Bottom tab primary roots
    data object Overview : AppDestination("OS Update Impact Intelligence")
    data object Monitor : AppDestination("OS Monitoring & Anomaly Engine")
    data object Updates : AppDestination("OS Update Lifecycle & Transitions")
    data object Results : AppDestination("Statistical Verification & Issues")
    data object Device : AppDestination("Hardware & Telemetry Capabilities")

    // Core Lifecycle & Investigation Screens
    data object V0Baseline : AppDestination("Pre-Update Baseline (V0)")
    data object AwaitingUpdate : AppDestination("Waiting for System Update")
    data object UpdateDetected : AppDestination("System Update Detected")
    data object V0V1Comparison : AppDestination("V0 vs V1 Differential Comparison")
    data class MetricDetail(val metricKey: String) : AppDestination("Metric Evidence & Statistics")
    data object IssueClassification : AppDestination("Issue Classification & Regressions")
    data object PredictionEvaluation : AppDestination("Prediction Accuracy vs Outcome")
    data object FinalEvidenceReport : AppDestination("OS Update Impact Report")
    data object AiExplanation : AppDestination("AI Root-Cause Advisor")
    data object Validation : AppDestination("Workload Measurement Probes")
    data object Claims : AppDestination("Release Claims & Risk Forecast")
    data object ExperimentDetail : AppDestination("Experiment Audit & Provenance")
    data object SettingsAbout : AppDestination("Methodology & Settings")
}

