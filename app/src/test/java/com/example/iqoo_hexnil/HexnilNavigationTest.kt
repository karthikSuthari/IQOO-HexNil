package com.example.iqoo_hexnil

import com.example.iqoo_hexnil.ui.AppDestination
import com.example.iqoo_hexnil.ui.BottomTab
import org.junit.Assert.assertEquals
import org.junit.Test

class HexnilNavigationTest {

    @Test
    fun testBottomTabProperties() {
        assertEquals(4, BottomTab.values().size)
        assertEquals("Overview", BottomTab.OVERVIEW.label)
        assertEquals("Validation", BottomTab.VALIDATION.label)
        assertEquals("Results", BottomTab.RESULTS.label)
        assertEquals("Device", BottomTab.DEVICE.label)
    }

    @Test
    fun testAppDestinationTitles() {
        assertEquals("Update Intelligence Overview", AppDestination.Overview.title)
        assertEquals("Deterministic Workload Engine", AppDestination.Validation.title)
        assertEquals("Statistical Comparison & Verdicts", AppDestination.Results.title)
        assertEquals("Hardware Identity & Telemetry", AppDestination.Device.title)
        assertEquals("Release Claims (Phase 7 Foundation)", AppDestination.Claims.title)
        assertEquals("V0 vs V1 Differential Comparison", AppDestination.V0V1Comparison.title)
        assertEquals("Metric Evidence & Statistics", AppDestination.MetricDetail("startup_01_startup_duration_ms").title)
        assertEquals("Experiment Audit & Provenance", AppDestination.ExperimentDetail.title)
        assertEquals("Evidence & AI Interpretation", AppDestination.AiExplanation.title)
        assertEquals("Settings & Methodology", AppDestination.SettingsAbout.title)
    }
}
