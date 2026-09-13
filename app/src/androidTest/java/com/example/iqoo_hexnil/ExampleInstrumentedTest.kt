package com.example.iqoo_hexnil

import android.content.Context
import android.os.BatteryManager
import android.os.Build
import android.os.PowerManager
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.example.iqoo_hexnil.data.HexnilRepository
import com.example.iqoo_hexnil.data.VerdictType
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith

/**
 * Instrumented tests executing live on the physical Android device (vivo I2302, Android 16, SDK 36).
 */
@RunWith(AndroidJUnit4::class)
class ExampleInstrumentedTest {

    @Test
    fun useAppContext() {
        val appContext = InstrumentationRegistry.getInstrumentation().targetContext
        assertEquals("com.example.iqoo_hexnil", appContext.packageName)
    }

    @Test
    fun testRealDeviceHardwareEnvironment() {
        val appContext = InstrumentationRegistry.getInstrumentation().targetContext
        
        // Verify system service availability on physical device
        val powerManager = appContext.getSystemService(Context.POWER_SERVICE) as? PowerManager
        assertNotNull("PowerManager must be accessible on physical device", powerManager)
        assertTrue("Device screen state should be queryable", powerManager!!.isInteractive || !powerManager.isInteractive)

        val batteryManager = appContext.getSystemService(Context.BATTERY_SERVICE) as? BatteryManager
        assertNotNull("BatteryManager must be accessible on physical device", batteryManager)
        
        // Verify physical vivo device characteristics
        assertTrue("Build SDK must be at least 34 (detected: ${Build.VERSION.SDK_INT})", Build.VERSION.SDK_INT >= 34)
        assertNotNull(Build.MANUFACTURER)
        assertNotNull(Build.MODEL)

        // Live hardware info queried through HexnilRepository with real Android Context
        val liveHardware = HexnilRepository.getDeviceHardwareInfo(appContext)
        assertNotNull(liveHardware)
        assertEquals("I2302", liveHardware.model)
        assertEquals("vivo", liveHardware.manufacturer.lowercase())
    }

    @Test
    fun testHexnilDataLayerOnDeviceRuntime() {
        val analysis = HexnilRepository.getComparisonAnalysis()
        assertNotNull(analysis)
        assertEquals("STATS-CMP-20260913-001", analysis.analysisId)
        assertEquals(13, analysis.metricsAnalyzed)
        assertEquals(0, analysis.metricsRegressions)

        val metrics = HexnilRepository.getMetricResults()
        assertTrue(metrics.isNotEmpty())
        assertEquals(13, metrics.size)

        val videoMetric = metrics.firstOrNull { it.workloadId == "video_power_01" }
        assertNotNull(videoMetric)
        assertEquals(VerdictType.UNCHANGED, videoMetric?.verdict)

        val claims = HexnilRepository.getReleaseClaims()
        assertEquals(5, claims.size)
        assertTrue(claims.any { it.id == "CLM-001" })

        val workloads = HexnilRepository.getWorkloads()
        assertEquals(5, workloads.size)
    }

    @Test
    fun testAiIntelligenceContractsOnDevice() {
        val primaryExplanation = HexnilRepository.getAiExplanation()
        assertNotNull(primaryExplanation)
        assertTrue(primaryExplanation.summary.contains("Zero regressions"))
        assertEquals("COMPLETED", primaryExplanation.verdict)
    }
}