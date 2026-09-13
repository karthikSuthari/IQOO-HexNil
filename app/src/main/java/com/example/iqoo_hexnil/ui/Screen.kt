package com.example.iqoo_hexnil.ui

enum class AppScreen(
    val title: String,
    val tabLabel: String,
    val iconSymbol: String
) {
    DASHBOARD(
        title = "Hexnil Dashboard",
        tabLabel = "Dashboard",
        iconSymbol = "⚡"
    ),
    TELEMETRY(
        title = "Live Telemetry",
        tabLabel = "Telemetry",
        iconSymbol = "📊"
    ),
    WORKLOADS(
        title = "Workload Engine",
        tabLabel = "Workloads",
        iconSymbol = "⚙"
    ),
    STATS(
        title = "Statistical Analysis",
        tabLabel = "Stats",
        iconSymbol = "📈"
    )
}
