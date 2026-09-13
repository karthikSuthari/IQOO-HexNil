package com.example.iqoo_hexnil

import com.example.iqoo_hexnil.data.ClaimRiskLevel
import com.example.iqoo_hexnil.data.ExplanationSource
import com.example.iqoo_hexnil.data.HardwareEvidenceState
import com.example.iqoo_hexnil.data.HexnilRepository
import com.example.iqoo_hexnil.data.MetricStatus
import com.example.iqoo_hexnil.data.VerdictType
import com.example.iqoo_hexnil.data.WorkloadPriority
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class HexnilRepositoryTest {

    @Test
    fun testComparisonAnalysisIntegrity() {
        val analysis = HexnilRepository.getComparisonAnalysis()

        assertEquals("STATS-CMP-20260913-001", analysis.analysisId)
        assertEquals("CMP-20260913-001", analysis.comparisonId)
        assertEquals("EXP-20260913-010", analysis.v0ExperimentId)
        assertEquals("EXP-20260913-012", analysis.v1ExperimentId)
        assertEquals(13, analysis.metricsAnalyzed)
        assertEquals(9, analysis.metricsEligible)
        assertEquals(8, analysis.metricsUnchanged)
        assertEquals(5, analysis.metricsInconclusive)
        assertEquals(0, analysis.metricsRegressions)
        assertEquals(0, analysis.metricsImprovements)
        assertEquals(1, analysis.metricsUnsupported)
        assertEquals("9 / 13", analysis.evidenceCoverage)
    }

    @Test
    fun testMetricResultsSemantics() {
        val metrics = HexnilRepository.getMetricResults()
        assertEquals(13, metrics.size)

        // Video Workload Duration: UNCHANGED (+3.05% < 5.0% threshold)
        val videoWorkload = metrics.find { it.workloadId == "video_power_01" && it.metricName == "workload_duration_ms" }
        assertNotNull(videoWorkload)
        assertEquals(VerdictType.UNCHANGED, videoWorkload!!.verdict)
        assertEquals(3.05, videoWorkload.percentDelta!!, 0.01)
        assertEquals(0.01158, videoWorkload.pValue!!, 0.0001)

        // Startup Latency: INCONCLUSIVE (p=0.2196 >= 0.05)
        val startupDuration = metrics.find { it.workloadId == "startup_01" && it.metricName == "startup_duration_ms" }
        assertNotNull(startupDuration)
        assertEquals(VerdictType.INCONCLUSIVE, startupDuration!!.verdict)
        assertEquals(22.86, startupDuration.percentDelta!!, 0.01)
        assertTrue(startupDuration.ciLower!! < 0 && startupDuration.ciUpper!! > 0)

        // Frame Jank: UNSUPPORTED
        val frameJank = metrics.find { it.workloadId == "scroll_01" && it.metricName == "ui_frame_jank_percent" }
        assertNotNull(frameJank)
        assertEquals(MetricStatus.UNSUPPORTED, frameJank!!.status)
        assertEquals(VerdictType.INCONCLUSIVE, frameJank.verdict)
        assertEquals(0, frameJank.sampleCount)
    }

    @Test
    fun testWorkloadDefinitions() {
        val workloads = HexnilRepository.getWorkloads()
        assertEquals(5, workloads.size)

        val workloadIds = workloads.map { it.id }.toSet()
        val expected = setOf("startup_01", "cpu_01", "memory_01", "scroll_01", "video_power_01")
        assertEquals(expected, workloadIds)

        workloads.forEach { workload ->
            assertTrue(workload.matchedRunsCount >= 3)
            assertNotNull(workload.configHash)
            assertTrue(workload.priority in setOf(WorkloadPriority.HIGH, WorkloadPriority.MEDIUM, WorkloadPriority.LOW))
        }
    }

    @Test
    fun testReleaseClaimsContracts() {
        val claims = HexnilRepository.getReleaseClaims()
        assertEquals(5, claims.size)

        val claim1 = claims.find { it.id == "CLM-001" }
        assertNotNull(claim1)
        assertEquals(ClaimRiskLevel.HIGH, claim1!!.riskLevel)
        assertEquals("video_power_01", claim1.recommendedWorkload)
        assertEquals("Battery / Power", claim1.subsystem)
    }

    @Test
    fun testDeviceHardwareInfoHonestFallbacks() {
        val device = HexnilRepository.getDeviceHardwareInfo(null)
        // Must NEVER fabricate 98%, DISCHARGING, or NORMAL (0) without live Android context
        assertNull("Battery percent must be null when context is unavailable", device.batteryPercent)
        assertEquals("NO_LIVE_EVIDENCE", device.chargingState)
        assertEquals("NO_LIVE_EVIDENCE", device.thermalStatus)
        assertEquals(HardwareEvidenceState.UNAVAILABLE, device.evidenceState)
        assertEquals(false, device.adbConnected)
    }

    @Test
    fun testComparisonAnalysisEvidenceState() {
        val analysis = HexnilRepository.getComparisonAnalysis()
        assertEquals("HISTORICAL_VERIFIED", analysis.evidenceState)
        assertEquals("2026-09-13T09:00:00Z", analysis.recordTimestamp)
        assertEquals("CMP-20260913-001", analysis.comparisonId)
    }

    @Test
    fun testAiExplanationContracts() {
        val detExplanation = HexnilRepository.getAiExplanation(overrideSource = ExplanationSource.DETERMINISTIC_ANALYSIS)
        assertEquals(ExplanationSource.DETERMINISTIC_ANALYSIS, detExplanation.source)
        assertEquals("COMPLETED", detExplanation.verdict)
        assertEquals("NONE", detExplanation.severity)
        assertTrue(detExplanation.summary.contains("Zero regressions"))
        assertTrue(detExplanation.observedChanges.isNotEmpty())
        assertTrue(detExplanation.claimAssessments.isNotEmpty())
        assertTrue(detExplanation.evidenceReferences.isNotEmpty())

        val groqExplanation = HexnilRepository.getAiExplanation(overrideSource = ExplanationSource.GROQ_AI)
        assertEquals(ExplanationSource.GROQ_AI, groqExplanation.source)
        assertEquals("llama-3.3-70b-versatile", groqExplanation.model)
        assertEquals("COMPLETED", groqExplanation.verdict)

        val fallbackExplanation = HexnilRepository.getAiExplanation(overrideSource = ExplanationSource.DETERMINISTIC_FALLBACK)
        assertEquals(ExplanationSource.DETERMINISTIC_FALLBACK, fallbackExplanation.source)
        assertTrue(fallbackExplanation.summary.contains("fallback"))
    }

}
