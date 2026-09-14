package com.example.iqoo_hexnil.ui

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.iqoo_hexnil.data.ComparisonAnalysis
import com.example.iqoo_hexnil.data.DeviceHardwareInfo
import com.example.iqoo_hexnil.data.HexnilLifecycleState
import com.example.iqoo_hexnil.data.HexnilRepository
import com.example.iqoo_hexnil.ui.components.ExecutiveVerdictCard
import com.example.iqoo_hexnil.ui.components.HexnilPrimaryButton
import com.example.iqoo_hexnil.ui.components.IssueClassificationCard
import com.example.iqoo_hexnil.ui.components.PredictionOutcomeCard
import com.example.iqoo_hexnil.ui.components.SectionHeader
import com.example.iqoo_hexnil.ui.components.UpdateTimeline
import com.example.iqoo_hexnil.ui.components.UpdateTransitionHero
import com.example.iqoo_hexnil.ui.theme.HexnilAccentGlow
import com.example.iqoo_hexnil.ui.theme.HexnilAccentSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilBackground
import com.example.iqoo_hexnil.ui.theme.HexnilBorder
import com.example.iqoo_hexnil.ui.theme.HexnilBorderFocus
import com.example.iqoo_hexnil.ui.theme.HexnilBorderSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilCard
import com.example.iqoo_hexnil.ui.theme.HexnilCyan
import com.example.iqoo_hexnil.ui.theme.HexnilCyanSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilMainAccent
import com.example.iqoo_hexnil.ui.theme.HexnilPrimaryText
import com.example.iqoo_hexnil.ui.theme.HexnilRadius
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryCard
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSpacing
import com.example.iqoo_hexnil.ui.theme.HexnilSuccess

@Composable
fun OverviewScreen(
    analysis: ComparisonAnalysis,
    device: DeviceHardwareInfo,
    onNavigateToMonitor: () -> Unit,
    onNavigateToUpdates: () -> Unit,
    onNavigateToResults: () -> Unit,
    onNavigateToDevice: () -> Unit,
    onNavigateToComparison: () -> Unit,
    onNavigateToReport: () -> Unit,
    onNavigateToMetricDetail: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    val scrollState = rememberScrollState()
    val lifecycleState = remember { HexnilRepository.getLifecycleState() }
    val transition = remember { HexnilRepository.getUpdateTransition() }
    val issueReport = remember { HexnilRepository.getIssueReport() }
    val predictionSummary = remember { HexnilRepository.getPredictionEvaluationSummary() }

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(HexnilBackground)
            .padding(horizontal = HexnilSpacing.screenHorizontal, vertical = HexnilSpacing.screenVertical)
            .verticalScroll(scrollState),
        verticalArrangement = Arrangement.spacedBy(HexnilSpacing.sectionSpacing)
    ) {
        // 1. Platform Brand & Positioning Hero
        PlatformBrandHero(device = device, onNavigateToDevice = onNavigateToDevice)

        // 2. 14-Step OS Update Lifecycle Timeline
        UpdateTimeline(currentState = lifecycleState)

        // 3. Central V0 -> Real Update -> V1 Hero Component
        UpdateTransitionHero(
            transition = transition,
            onClick = onNavigateToUpdates
        )

        // 4. Executive Verdict Card
        val report = remember { HexnilRepository.getFinalEvidenceReport() }
        ExecutiveVerdictCard(
            verdict = report.executiveVerdict,
            evidenceCoverage = report.evidenceCoverage,
            regressionsCount = issueReport.newRegressionsCount,
            improvementsCount = issueReport.improvementsCount,
            persistedCount = issueReport.persistedCount,
            unchangedCount = issueReport.unchangedCount,
            inconclusiveCount = issueReport.inconclusiveCount
        )

        // 5. Action Hub: Direct Links to Investigation Drill-downs
        ActionHub(
            onNavigateToReport = onNavigateToReport,
            onNavigateToComparison = onNavigateToComparison,
            onNavigateToMonitor = onNavigateToMonitor
        )

        // 6. Key Issue Classification Highlights (Pre-Existing vs New Regressions)
        SectionHeader(
            title = "CLASSIFIED UPDATE ISSUES",
            actionLabel = "View All (${issueReport.totalClassified})",
            onActionClick = onNavigateToResults
        )

        // Show notable issues (e.g. Persisted startup jitter vs Unchanged stability)
        val notableIssues = issueReport.classifications.filter {
            it.preUpdateAnomalyExisted || it.percentDelta != null
        }.take(2)

        notableIssues.forEach { issue ->
            IssueClassificationCard(
                issue = issue,
                onClick = { onNavigateToMetricDetail("${issue.workloadId}_${issue.metricName}") }
            )
        }

        // 7. Prediction vs Actual Outcome Summary
        SectionHeader(
            title = "PREDICTION VS OUTCOME",
            actionLabel = "${predictionSummary.totalEvaluated} Evaluated",
            onActionClick = onNavigateToResults
        )

        predictionSummary.outcomes.take(2).forEach { outcome ->
            PredictionOutcomeCard(outcome = outcome)
        }

        Spacer(modifier = Modifier.height(16.dp))
    }
}

@Composable
private fun PlatformBrandHero(
    device: DeviceHardwareInfo,
    onNavigateToDevice: () -> Unit
) {
    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(HexnilRadius.card))
            .border(BorderStroke(1.dp, HexnilBorderSubtle), RoundedCornerShape(HexnilRadius.card))
            .clickable { onNavigateToDevice() },
        color = HexnilCard
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        text = "HEXNIL",
                        color = HexnilPrimaryText,
                        fontSize = 20.sp,
                        fontWeight = FontWeight.Black,
                        letterSpacing = 1.5.sp
                    )
                    Text(
                        text = "OS UPDATE IMPACT INTELLIGENCE",
                        color = HexnilMainAccent,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 1.sp
                    )
                }

                Surface(
                    shape = RoundedCornerShape(HexnilRadius.badge),
                    color = HexnilCyanSubtle,
                    border = BorderStroke(1.dp, HexnilCyan.copy(alpha = 0.4f))
                ) {
                    Text(
                        text = "TARGET: ${device.model}",
                        color = HexnilCyan,
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace,
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 3.dp)
                    )
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                text = "Android ${device.androidRelease} (SDK ${device.sdkInt}) • Build: ${device.buildId} • Patch: 2026-09-01",
                color = HexnilSecondaryText,
                fontSize = 11.sp,
                fontFamily = FontFamily.Monospace
            )
        }
    }
}

@Composable
private fun ActionHub(
    onNavigateToReport: () -> Unit,
    onNavigateToComparison: () -> Unit,
    onNavigateToMonitor: () -> Unit
) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        HexnilPrimaryButton(
            text = "📄 VIEW FINAL EVIDENCE REPORT",
            onClick = onNavigateToReport,
            modifier = Modifier.fillMaxWidth()
        )

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Surface(
                modifier = Modifier
                    .weight(1f)
                    .clip(RoundedCornerShape(HexnilRadius.sm))
                    .border(BorderStroke(1.dp, HexnilBorder), RoundedCornerShape(HexnilRadius.sm))
                    .clickable { onNavigateToComparison() },
                color = HexnilSecondaryCard
            ) {
                Column(
                    modifier = Modifier.padding(10.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text(text = "⚖️ V0 ➔ V1 DIFF", color = HexnilPrimaryText, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                    Text(text = "Matched Iterations", color = HexnilSecondaryText, fontSize = 9.sp)
                }
            }

            Surface(
                modifier = Modifier
                    .weight(1f)
                    .clip(RoundedCornerShape(HexnilRadius.sm))
                    .border(BorderStroke(1.dp, HexnilBorder), RoundedCornerShape(HexnilRadius.sm))
                    .clickable { onNavigateToMonitor() },
                color = HexnilSecondaryCard
            ) {
                Column(
                    modifier = Modifier.padding(10.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text(text = "📡 MONITORING", color = HexnilPrimaryText, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                    Text(text = "Anomalies & Baseline", color = HexnilSecondaryText, fontSize = 9.sp)
                }
            }
        }
    }
}
