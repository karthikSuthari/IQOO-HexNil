package com.example.iqoo_hexnil

import com.example.iqoo_hexnil.ui.AppDestination
import com.example.iqoo_hexnil.ui.BottomTab
import org.junit.Assert.assertEquals
import org.junit.Test

class HexnilNavigationTest {

    @Test
    fun testBottomTabProperties() {
        assertEquals(5, BottomTab.values().size)
        assertEquals("Overview", BottomTab.OVERVIEW.label)
        assertEquals("Monitor", BottomTab.MONITOR.label)
        assertEquals("Updates", BottomTab.UPDATES.label)
        assertEquals("Results", BottomTab.RESULTS.label)
        assertEquals("Device", BottomTab.DEVICE.label)
    }

    @Test
    fun testAppDestinationTitles() {
        assertEquals("OS Update Impact Intelligence", AppDestination.Overview.title)
        assertEquals("OS Monitoring & Anomaly Engine", AppDestination.Monitor.title)
        assertEquals("OS Update Lifecycle & Transitions", AppDestination.Updates.title)
        assertEquals("Statistical Verification & Issues", AppDestination.Results.title)
        assertEquals("Hardware & Telemetry Capabilities", AppDestination.Device.title)
        assertEquals("Pre-Update Baseline (V0)", AppDestination.V0Baseline.title)
        assertEquals("Waiting for System Update", AppDestination.AwaitingUpdate.title)
        assertEquals("System Update Detected", AppDestination.UpdateDetected.title)
        assertEquals("V0 vs V1 Differential Comparison", AppDestination.V0V1Comparison.title)
        assertEquals("Metric Evidence & Statistics", AppDestination.MetricDetail("startup_01_startup_duration_ms").title)
        assertEquals("OS Update Impact Report", AppDestination.FinalEvidenceReport.title)
        assertEquals("AI Root-Cause Advisor", AppDestination.AiExplanation.title)
        assertEquals("Workload Measurement Probes", AppDestination.Validation.title)
        assertEquals("Release Claims & Risk Forecast", AppDestination.Claims.title)
        assertEquals("Experiment Audit & Provenance", AppDestination.ExperimentDetail.title)
        assertEquals("Methodology & Settings", AppDestination.SettingsAbout.title)
    }
}

