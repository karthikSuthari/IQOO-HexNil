package com.example.iqoo_hexnil.ui

enum class BottomTab(
    val label: String,
    val iconSymbol: String,
    val title: String
) {
    OVERVIEW("Overview", "⚡", "Update Intelligence Overview"),
    VALIDATION("Validation", "⚙", "Deterministic Workload Engine"),
    RESULTS("Results", "📈", "Statistical Comparison & Verdicts"),
    DEVICE("Device", "📱", "Hardware Identity & Telemetry")
}

sealed class AppDestination(val title: String) {
    // Bottom tab primary roots
    data object Overview : AppDestination("Update Intelligence Overview")
    data object Validation : AppDestination("Deterministic Workload Engine")
    data object Results : AppDestination("Statistical Comparison & Verdicts")
    data object Device : AppDestination("Hardware Identity & Telemetry")

    // Nested / Drill-down screens
    data object Claims : AppDestination("Release Claims (Phase 7 Foundation)")
    data object V0V1Comparison : AppDestination("V0 vs V1 Differential Comparison")
    data class MetricDetail(val metricKey: String) : AppDestination("Metric Evidence & Statistics")
    data object ExperimentDetail : AppDestination("Experiment Audit & Provenance")
    data object AiExplanation : AppDestination("Evidence & AI Interpretation")
    data object SettingsAbout : AppDestination("Settings & Methodology")
}
