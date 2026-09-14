package com.example.iqoo_hexnil

import com.example.iqoo_hexnil.data.ClaimRiskLevel
import com.example.iqoo_hexnil.data.ExplanationSource
import com.example.iqoo_hexnil.data.HardwareEvidenceState
import com.example.iqoo_hexnil.data.HexnilRepository
import com.example.iqoo_hexnil.data.MetricStatus
import com.example.iqoo_hexnil.data.VerdictType
import com.example.iqoo_hexnil.data.WorkloadPriority
import com.example.iqoo_hexnil.data.WorkloadStatus
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class HexnilUiLogicTest {

    @Test
    fun testRegressionSummaryCountsAreHonest() {
        val analysis = HexnilRepository.getComparisonAnalysis()

        // Critical Phase 9 requirement: Regression must be 0, never manufactured
        assertEquals("Zero regressions must be reported", 0, analysis.metricsRegressions)
        assertEquals("Zero improvements must be reported", 0, analysis.metricsImprovements)
        assertEquals(8, analysis.metricsUnchanged)
        assertEquals(5, analysis.metricsInconclusive)
        assertEquals(13, analysis.metricsAnalyzed)

        // Verify that sum of breakdown equals total
        val totalCategorized = analysis.metricsUnchanged + analysis.metricsInconclusive + analysis.metricsRegressions + analysis.metricsImprovements
        assertEquals(13, totalCategorized)
    }

    @Test
    fun testStatusSemanticsCriticalDistinctions() {
        val metrics = HexnilRepository.getMetricResults()

        // 1. Positive delta below threshold must remain UNCHANGED (not regression)
        val videoMetric = metrics.first { it.workloadId == "video_power_01" && it.metricName == "workload_duration_ms" }
        assertEquals(VerdictType.UNCHANGED, videoMetric.verdict)
        assertEquals(3.05, videoMetric.percentDelta!!, 0.01)
        assertTrue(videoMetric.percentDelta!! < (videoMetric.thresholdPercent ?: 5.0))
        assertNotEquals(VerdictType.REGRESSION, videoMetric.verdict)

        // 2. High variance crossing zero must remain INCONCLUSIVE (not regression)
        val startupMetric = metrics.first { it.workloadId == "startup_01" && it.metricName == "startup_duration_ms" }
        assertEquals(VerdictType.INCONCLUSIVE, startupMetric.verdict)
        assertNotEquals(VerdictType.REGRESSION, startupMetric.verdict)

        // 3. Unsupported hardware metric must remain UNSUPPORTED (not zero, not regression)
        val jankMetric = metrics.first { it.workloadId == "scroll_01" && it.metricName == "ui_frame_jank_percent" }
        assertEquals(MetricStatus.UNSUPPORTED, jankMetric.status)
        assertEquals(VerdictType.INCONCLUSIVE, jankMetric.verdict)
        assertEquals(0, jankMetric.sampleCount)
        assertNull(jankMetric.percentDelta)
    }

    @Test
    fun testWorkloadAttributesAndExecutionIntegrity() {
        val workloads = HexnilRepository.getWorkloads()
        assertEquals(5, workloads.size)

        val expectedIds = listOf("startup_01", "cpu_01", "memory_01", "scroll_01", "video_power_01")
        assertEquals(expectedIds, workloads.map { it.id })

        workloads.forEach { wl ->
            assertTrue(wl.name.isNotBlank())
            assertTrue(wl.purpose.isNotBlank())
            assertTrue(wl.isSelected)
            assertEquals("AVAILABLE", wl.evidenceAvailability)
            assertTrue(wl.matchedRunsCount >= 3)
            assertNotNull(wl.lastDurationMs)
            assertTrue(wl.lastDurationMs!! > 0.0) // Valid duration, never 0
        }
    }

    @Test
    fun testReleaseClaimsValidationStates() {
        val claims = HexnilRepository.getReleaseClaims()
        assertEquals(5, claims.size)

        val clm001 = claims.first { it.id == "CLM-001" }
        assertEquals("UNCHANGED", clm001.validationStatus)
        assertEquals(WorkloadPriority.HIGH, clm001.priority)
        assertEquals(ClaimRiskLevel.HIGH, clm001.riskLevel)
        assertEquals("video_power_01", clm001.recommendedWorkload)

        val clm002 = claims.first { it.id == "CLM-002" }
        assertEquals("INCONCLUSIVE", clm002.validationStatus)
        assertEquals(WorkloadPriority.HIGH, clm002.priority)

        val clm003 = claims.first { it.id == "CLM-003" }
        assertEquals("UNCHANGED", clm003.validationStatus)

        val clm004 = claims.first { it.id == "CLM-004" }
        assertEquals("INCONCLUSIVE", clm004.validationStatus)

        val clm005 = claims.first { it.id == "CLM-005" }
        assertEquals("UNCHANGED", clm005.validationStatus)
    }

    @Test
    fun testDeviceHonestFallbacksNeverFabricateNumbers() {
        val deviceInfo = HexnilRepository.getDeviceHardwareInfo(null)

        // Never fabricate 98%, DISCHARGING, or NORMAL (0)
        assertNull(deviceInfo.batteryPercent)
        assertEquals("NO_LIVE_EVIDENCE", deviceInfo.chargingState)
        assertEquals("NO_LIVE_EVIDENCE", deviceInfo.thermalStatus)
        assertEquals(HardwareEvidenceState.UNAVAILABLE, deviceInfo.evidenceState)
    }

    @Test
    fun testAiExplanationDeterministicFallbackPresentation() {
        val fallback = HexnilRepository.getAiExplanation(overrideSource = ExplanationSource.DETERMINISTIC_FALLBACK)
        assertEquals(ExplanationSource.DETERMINISTIC_FALLBACK, fallback.source)
        assertTrue(fallback.summary.contains("fallback") || fallback.summary.contains("Zero regressions"))
        assertEquals("COMPLETED", fallback.verdict)
        assertEquals("NONE", fallback.severity)
        assertTrue(fallback.observedChanges.isNotEmpty())
        assertTrue(fallback.claimAssessments.isNotEmpty())
        assertTrue(fallback.evidenceReferences.isNotEmpty())
    }

    @Test
    fun testPreExistingAnomalyDistinctionFromRegression() {
        val issueReport = HexnilRepository.getIssueReport()
        val startupIssue = issueReport.classifications.first { it.metricName == "startup_duration_ms" }

        // Must be PERSISTED, not NEW_REGRESSION
        assertEquals(com.example.iqoo_hexnil.data.IssueCategory.PERSISTED, startupIssue.category)
        assertTrue("Must flag that pre-update anomaly existed in V0", startupIssue.preUpdateAnomalyExisted)
        assertNotNull(startupIssue.preUpdateAnomalyDescription)
        assertFalse("Persisted issue must not be marked as regression", startupIssue.category.isRegression)

        // Verify that zero new regressions were created
        assertEquals(0, issueReport.newRegressionsCount)
    }

    @Test
    fun testLifecycleStateStepMonotonicity() {
        val states = com.example.iqoo_hexnil.data.HexnilLifecycleState.values()
        assertEquals(14, states.size)
        states.forEachIndexed { index, state ->
            assertEquals(index + 1, state.step)
            assertTrue(state.label.isNotBlank())
            assertTrue(state.description.isNotBlank())
        }
    }
}

