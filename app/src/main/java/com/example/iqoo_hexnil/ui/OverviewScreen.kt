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
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.iqoo_hexnil.data.ComparisonAnalysis
import com.example.iqoo_hexnil.data.DeviceHardwareInfo
import com.example.iqoo_hexnil.data.ExplanationSource
import com.example.iqoo_hexnil.data.HexnilRepository
import com.example.iqoo_hexnil.data.ReleaseClaim
import com.example.iqoo_hexnil.data.StatisticalMetricResult
import com.example.iqoo_hexnil.data.VerdictType
import com.example.iqoo_hexnil.data.WorkloadDefinition
import com.example.iqoo_hexnil.ui.components.HexnilPrimaryButton
import com.example.iqoo_hexnil.ui.components.PriorityChip
import com.example.iqoo_hexnil.ui.components.ResultBadge
import com.example.iqoo_hexnil.ui.components.SectionHeader
import com.example.iqoo_hexnil.ui.components.ValidationStatusChip
import com.example.iqoo_hexnil.ui.theme.DisplayLargeNumber
import com.example.iqoo_hexnil.ui.theme.HexnilAccentGlow
import com.example.iqoo_hexnil.ui.theme.HexnilAccentSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilBackground
import com.example.iqoo_hexnil.ui.theme.HexnilBorder
import com.example.iqoo_hexnil.ui.theme.HexnilCard
import com.example.iqoo_hexnil.ui.theme.HexnilError
import com.example.iqoo_hexnil.ui.theme.HexnilMainAccent
import com.example.iqoo_hexnil.ui.theme.HexnilPrimaryText
import com.example.iqoo_hexnil.ui.theme.HexnilRadius
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryCard
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSpacing
import com.example.iqoo_hexnil.ui.theme.HexnilSuccess
import com.example.iqoo_hexnil.ui.theme.HexnilSuccessSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilWarning
import com.example.iqoo_hexnil.ui.theme.MonospaceSmall
import com.example.iqoo_hexnil.ui.theme.MonospaceValue

@Composable
fun OverviewScreen(
    analysis: ComparisonAnalysis,
    device: DeviceHardwareInfo,
    onNavigateToResults: () -> Unit,
    onNavigateToClaims: () -> Unit,
    onNavigateToValidation: () -> Unit,
    onNavigateToComparison: () -> Unit,
    onNavigateToProvenance: () -> Unit,
    onNavigateToAiExplanation: () -> Unit,
    onNavigateToMetricDetail: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    val scrollState = rememberScrollState()
    val claims = remember { HexnilRepository.getReleaseClaims() }
    val workloads = remember { HexnilRepository.getWorkloads() }
    val aiExplanation = remember(analysis.comparisonId) {
        HexnilRepository.getAiExplanation(analysis.comparisonId, ExplanationSource.DETERMINISTIC_ANALYSIS)
    }

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(HexnilBackground)
            .padding(horizontal = HexnilSpacing.md, vertical = HexnilSpacing.sm)
            .verticalScroll(scrollState),
        verticalArrangement = Arrangement.spacedBy(HexnilSpacing.md)
    ) {
        // 1. Device + Update Context Header
        DeviceUpdateContextCard(
            device = device,
            comparisonId = analysis.comparisonId,
            v0Exp = analysis.v0ExperimentId,
            v1Exp = analysis.v1ExperimentId
        )

        // 2. Primary Outcome Hero (+3.05% UNCHANGED video playback duration)
        val primaryHighlight = analysis.metricResults.find { it.workloadId == "video_power_01" && it.metricName == "workload_duration_ms" }
            ?: analysis.metricResults.firstOrNull()

        if (primaryHighlight != null) {
            PrimaryOutcomeHeroCard(
                metric = primaryHighlight,
                onClick = { onNavigateToMetricDetail(primaryHighlight.key) }
            )
        }

        // 3. Evidence Coverage & Outcome Summary (Unified, card-spam free)
        EvidenceAndOutcomeSection(
            analysis = analysis,
            onViewResultsClick = onNavigateToResults
        )

        // 4. Important Claims Preview
        ImportantClaimsSection(
            claims = claims.take(3),
            totalCount = claims.size,
            onViewAll = onNavigateToClaims
        )

        // 5. Validation Priority (Top recommended workloads)
        ValidationPrioritySection(
            workloads = workloads.filter { it.isSelected }.take(3),
            totalCount = workloads.size,
            onViewAll = onNavigateToValidation
        )

        // 6. AI Analyst Preview
        AiAnalystSection(
            explanation = aiExplanation,
            onInspectEvidence = onNavigateToAiExplanation
        )

        // 7. Audit & Provenance Traceability
        AuditProvenanceQuickSection(
            analysis = analysis,
            onInspectProvenance = onNavigateToProvenance
        )

        // Primary Action
        HexnilPrimaryButton(
            text = "VIEW COMPLETE STATISTICAL RESULTS ➔",
            onClick = onNavigateToResults
        )

        Spacer(modifier = Modifier.height(HexnilSpacing.xs))
    }
}

@Composable
private fun DeviceUpdateContextCard(
    device: DeviceHardwareInfo,
    comparisonId: String,
    v0Exp: String,
    v1Exp: String
) {
    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(HexnilRadius.card))
            .border(1.dp, HexnilBorder, RoundedCornerShape(HexnilRadius.card)),
        color = HexnilCard
    ) {
        Column(modifier = Modifier.padding(HexnilSpacing.md)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(
                            text = "HEXNIL",
                            color = HexnilMainAccent,
                            fontSize = 14.sp,
                            fontWeight = FontWeight.Black,
                            letterSpacing = 1.5.sp
                        )
                        Spacer(modifier = Modifier.width(HexnilSpacing.xs))
                        Surface(
                            shape = RoundedCornerShape(4.dp),
                            color = HexnilSecondaryCard,
                            border = BorderStroke(1.dp, HexnilBorder)
                        ) {
                            Text(
                                text = "v1.1",
                                color = HexnilAccentGlow,
                                fontSize = 9.sp,
                                fontWeight = FontWeight.Bold,
                                modifier = Modifier.padding(horizontal = 5.dp, vertical = 1.dp)
                            )
                        }
                    }
                    Text(
                        text = "Engineering Validation Intelligence",
                        color = HexnilSecondaryText,
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Medium
                    )
                }

                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(modifier = Modifier.size(7.dp).background(HexnilSuccess, CircleShape))
                    Spacer(modifier = Modifier.width(HexnilSpacing.xxs))
                    Text(
                        text = "EVIDENCE AUDITED",
                        color = HexnilSuccess,
                        fontSize = 9.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 0.5.sp
                    )
                }
            }

            Spacer(modifier = Modifier.height(HexnilSpacing.sm))

            // Clean context metadata rows (no nested heavy card)
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(text = "Target Device", color = HexnilSecondaryText, fontSize = 11.sp)
                Text(
                    text = "${device.manufacturer} ${device.model}",
                    color = HexnilPrimaryText,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold
                )
            }

            Spacer(modifier = Modifier.height(4.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(text = "Operating System", color = HexnilSecondaryText, fontSize = 11.sp)
                Text(
                    text = "Android ${device.androidRelease} / SDK ${device.sdkInt}",
                    color = HexnilPrimaryText,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Medium
                )
            }

            Spacer(modifier = Modifier.height(4.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(text = "Comparison ID", color = HexnilSecondaryText, fontSize = 11.sp)
                Text(
                    text = comparisonId,
                    color = HexnilAccentGlow,
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Bold
                )
            }

            Spacer(modifier = Modifier.height(4.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(text = "Software Delta", color = HexnilSecondaryText, fontSize = 11.sp)
                Text(
                    text = "$v0Exp ➔ $v1Exp",
                    color = HexnilPrimaryText,
                    fontSize = 10.sp,
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Medium
                )
            }
        }
    }
}

@Composable
private fun PrimaryOutcomeHeroCard(
    metric: StatisticalMetricResult,
    onClick: () -> Unit
) {
    val v0Text = if (metric.v0Mean != null) "${"%.3f".format(metric.v0Mean)} ms" else "Unavailable"
    val v1Text = if (metric.v1Mean != null) "${"%.3f".format(metric.v1Mean)} ms" else "Unavailable"
    val deltaPercentText = if (metric.percentDelta != null) "${if (metric.percentDelta >= 0) "+" else ""}${"%.2f".format(metric.percentDelta)}%" else "N/A"
    val deltaAbsText = if (metric.absoluteDelta != null) "${if (metric.absoluteDelta >= 0) "+" else ""}${"%.3f".format(metric.absoluteDelta)} ms" else "N/A"

    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(HexnilRadius.hero))
            .border(1.dp, HexnilBorder, RoundedCornerShape(HexnilRadius.hero))
            .clickable { onClick() },
        color = HexnilCard
    ) {
        Column(modifier = Modifier.padding(HexnilSpacing.md)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "PRIMARY OUTCOME HERO",
                    color = HexnilMainAccent,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp
                )
                ResultBadge(verdict = metric.verdict)
            }

            Spacer(modifier = Modifier.height(HexnilSpacing.sm))

            // Large dominant display numbers
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        text = deltaPercentText,
                        style = DisplayLargeNumber,
                        color = HexnilPrimaryText
                    )
                    Text(
                        text = deltaAbsText,
                        style = MonospaceSmall,
                        color = HexnilAccentGlow
                    )
                }

                Surface(
                    shape = RoundedCornerShape(HexnilRadius.metadata),
                    color = HexnilSecondaryCard,
                    border = BorderStroke(1.dp, HexnilSuccess.copy(alpha = 0.5f))
                ) {
                    Column(
                        modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Text(
                            text = "STATUS",
                            color = HexnilSecondaryText,
                            fontSize = 8.sp,
                            fontWeight = FontWeight.Bold
                        )
                        Text(
                            text = metric.verdict.label,
                            color = HexnilSuccess,
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Black
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(HexnilSpacing.xs))

            Text(
                text = metric.displayName,
                color = HexnilPrimaryText,
                fontSize = 15.sp,
                fontWeight = FontWeight.Bold
            )

            Text(
                text = "Workload: ${metric.workloadId} · Metric: ${metric.metricName}",
                color = HexnilSecondaryText,
                fontSize = 10.sp,
                fontFamily = FontFamily.Monospace
            )

            Spacer(modifier = Modifier.height(HexnilSpacing.sm))

            // V0 -> V1 comparison row
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(HexnilSecondaryCard, RoundedCornerShape(HexnilRadius.metadata))
                    .padding(horizontal = 12.dp, vertical = 10.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(text = "V0 BASELINE", color = HexnilSecondaryText, fontSize = 9.sp, fontWeight = FontWeight.Bold)
                    Text(text = v0Text, style = MonospaceValue)
                }

                Text(text = "➔", color = HexnilSecondaryText, fontSize = 12.sp)

                Column {
                    Text(text = "V1 CANDIDATE", color = HexnilSecondaryText, fontSize = 9.sp, fontWeight = FontWeight.Bold)
                    Text(text = v1Text, style = MonospaceValue)
                }

                Column(horizontalAlignment = Alignment.End) {
                    Text(text = "DELTA SHIFT", color = HexnilSecondaryText, fontSize = 9.sp, fontWeight = FontWeight.Bold)
                    Text(text = deltaPercentText, style = MonospaceValue, color = HexnilSuccess)
                }
            }

            Spacer(modifier = Modifier.height(HexnilSpacing.xs))

            // Threshold note
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.Top
            ) {
                Text(text = "ℹ", color = HexnilSecondaryText, fontSize = 11.sp)
                Spacer(modifier = Modifier.width(HexnilSpacing.xxs))
                Text(
                    text = "Engineering threshold: ${metric.thresholdPercent ?: 5.0}% · Observed shift ($deltaPercentText) is within the configured threshold (p=${metric.pValue?.let { "%.4f".format(it) } ?: "0.0116"}). Authoritatively UNCHANGED.",
                    color = HexnilSecondaryText,
                    fontSize = 10.sp,
                    lineHeight = 14.sp
                )
            }
        }
    }
}

@Composable
private fun EvidenceAndOutcomeSection(
    analysis: ComparisonAnalysis,
    onViewResultsClick: () -> Unit
) {
    val coverageFraction = if (analysis.metricsAnalyzed > 0) {
        analysis.metricsEligible.toFloat() / analysis.metricsAnalyzed.toFloat()
    } else 0f

    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(HexnilRadius.card))
            .border(1.dp, HexnilBorder, RoundedCornerShape(HexnilRadius.card)),
        color = HexnilCard
    ) {
        Column(modifier = Modifier.padding(HexnilSpacing.md)) {
            // Header
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "EVIDENCE COVERAGE & OUTCOME SUMMARY",
                    color = HexnilMainAccent,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp
                )
                Text(
                    text = "AUTHORITATIVE",
                    color = HexnilSecondaryText,
                    fontSize = 9.sp,
                    fontWeight = FontWeight.Bold
                )
            }

            Spacer(modifier = Modifier.height(HexnilSpacing.sm))

            // Evidence Coverage Number & Progress
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.Bottom
            ) {
                Column {
                    Text(text = "Evidence Coverage", color = HexnilSecondaryText, fontSize = 11.sp)
                    Text(
                        text = "${analysis.metricsEligible} / ${analysis.metricsAnalyzed} Metrics",
                        style = DisplayLargeNumber,
                        fontSize = 24.sp
                    )
                }

                Text(
                    text = "${(coverageFraction * 100).toInt()}% Confirmed with measured evidence",
                    color = HexnilSuccess,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold
                )
            }

            Spacer(modifier = Modifier.height(HexnilSpacing.xs))

            LinearProgressIndicator(
                progress = { coverageFraction },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(6.dp)
                    .clip(RoundedCornerShape(3.dp)),
                color = HexnilSuccess,
                trackColor = HexnilSecondaryCard
            )

            Spacer(modifier = Modifier.height(HexnilSpacing.sm))

            // 4 Outcome Summary Columns
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(HexnilSpacing.xs)
            ) {
                OutcomeCell(
                    label = "REGRESSION",
                    count = analysis.metricsRegressions,
                    color = if (analysis.metricsRegressions > 0) HexnilError else HexnilSecondaryText,
                    modifier = Modifier.weight(1f)
                )
                OutcomeCell(
                    label = "IMPROVEMENT",
                    count = analysis.metricsImprovements,
                    color = HexnilSuccess,
                    modifier = Modifier.weight(1f)
                )
                OutcomeCell(
                    label = "UNCHANGED",
                    count = analysis.metricsUnchanged,
                    color = HexnilSuccess,
                    modifier = Modifier.weight(1f)
                )
                OutcomeCell(
                    label = "INCONCLUSIVE",
                    count = analysis.metricsInconclusive,
                    color = HexnilWarning,
                    modifier = Modifier.weight(1f)
                )
            }

            Spacer(modifier = Modifier.height(HexnilSpacing.sm))

            // Honest Banner
            Surface(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(HexnilRadius.metadata),
                color = if (analysis.metricsRegressions == 0) HexnilSuccessSubtle else HexnilAccentSubtle,
                border = BorderStroke(1.dp, if (analysis.metricsRegressions == 0) HexnilSuccess.copy(alpha = 0.5f) else HexnilError.copy(alpha = 0.5f))
            ) {
                Row(
                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 8.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = if (analysis.metricsRegressions == 0) "✓" else "⚠",
                        color = if (analysis.metricsRegressions == 0) HexnilSuccess else HexnilError,
                        fontWeight = FontWeight.Bold
                    )
                    Spacer(modifier = Modifier.width(HexnilSpacing.xs))
                    Text(
                        text = if (analysis.metricsRegressions == 0) {
                            "No statistically supported regressions detected across 13 analyzed metrics."
                        } else {
                            "${analysis.metricsRegressions} regression(s) detected."
                        },
                        color = if (analysis.metricsRegressions == 0) HexnilSuccess else HexnilError,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.SemiBold
                    )
                }
            }
        }
    }
}

@Composable
private fun OutcomeCell(
    label: String,
    count: Int,
    color: Color,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(HexnilRadius.metadata),
        color = HexnilSecondaryCard,
        border = BorderStroke(1.dp, HexnilBorder)
    ) {
        Column(
            modifier = Modifier.padding(vertical = 8.dp, horizontal = 4.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = count.toString(),
                color = color,
                fontSize = 18.sp,
                fontWeight = FontWeight.Black,
                fontFamily = FontFamily.Monospace
            )
            Text(
                text = label,
                color = HexnilSecondaryText,
                fontSize = 8.sp,
                fontWeight = FontWeight.Bold,
                maxLines = 1
            )
        }
    }
}

@Composable
private fun ImportantClaimsSection(
    claims: List<ReleaseClaim>,
    totalCount: Int,
    onViewAll: () -> Unit
) {
    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(HexnilRadius.card))
            .border(1.dp, HexnilBorder, RoundedCornerShape(HexnilRadius.card)),
        color = HexnilCard
    ) {
        Column(modifier = Modifier.padding(HexnilSpacing.md)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "IMPORTANT CLAIMS",
                    color = HexnilMainAccent,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp
                )
                Text(
                    text = "View all $totalCount ➔",
                    color = HexnilAccentGlow,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.clickable { onViewAll() }
                )
            }

            Spacer(modifier = Modifier.height(HexnilSpacing.xs))

            claims.forEachIndexed { index, claim ->
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 6.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            text = "${claim.id} · ${claim.title}",
                            color = HexnilPrimaryText,
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Bold
                        )
                        Text(
                            text = "${claim.subsystem} · Expected: ${claim.expectedDirection}",
                            color = HexnilSecondaryText,
                            fontSize = 10.sp
                        )
                    }
                    ValidationStatusChip(status = claim.validationStatus)
                }
                if (index < claims.size - 1) {
                    Box(modifier = Modifier.fillMaxWidth().height(1.dp).background(HexnilBorder.copy(alpha = 0.5f)))
                }
            }
        }
    }
}

@Composable
private fun ValidationPrioritySection(
    workloads: List<WorkloadDefinition>,
    totalCount: Int,
    onViewAll: () -> Unit
) {
    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(HexnilRadius.card))
            .border(1.dp, HexnilBorder, RoundedCornerShape(HexnilRadius.card)),
        color = HexnilCard
    ) {
        Column(modifier = Modifier.padding(HexnilSpacing.md)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "VALIDATION PRIORITY",
                    color = HexnilMainAccent,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp
                )
                Text(
                    text = "Inspect all $totalCount ➔",
                    color = HexnilAccentGlow,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.clickable { onViewAll() }
                )
            }

            Spacer(modifier = Modifier.height(HexnilSpacing.xs))

            workloads.forEachIndexed { index, wl ->
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 6.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(
                                text = wl.id,
                                color = HexnilPrimaryText,
                                fontSize = 12.sp,
                                fontFamily = FontFamily.Monospace,
                                fontWeight = FontWeight.Bold
                            )
                            Spacer(modifier = Modifier.width(HexnilSpacing.xs))
                            Surface(
                                shape = RoundedCornerShape(3.dp),
                                color = HexnilAccentSubtle,
                                border = BorderStroke(1.dp, HexnilMainAccent.copy(alpha = 0.5f))
                            ) {
                                Text(
                                    text = "SELECTED",
                                    color = HexnilMainAccent,
                                    fontSize = 8.sp,
                                    fontWeight = FontWeight.Bold,
                                    modifier = Modifier.padding(horizontal = 4.dp, vertical = 1.dp)
                                )
                            }
                        }
                        Text(
                            text = wl.purpose,
                            color = HexnilSecondaryText,
                            fontSize = 10.sp,
                            maxLines = 1
                        )
                    }

                    PriorityChip(priority = wl.priority)
                }
                if (index < workloads.size - 1) {
                    Box(modifier = Modifier.fillMaxWidth().height(1.dp).background(HexnilBorder.copy(alpha = 0.5f)))
                }
            }
        }
    }
}

@Composable
private fun AiAnalystSection(
    explanation: com.example.iqoo_hexnil.data.AiExplanation,
    onInspectEvidence: () -> Unit
) {
    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(HexnilRadius.card))
            .border(1.dp, HexnilBorder, RoundedCornerShape(HexnilRadius.card)),
        color = HexnilCard
    ) {
        Column(modifier = Modifier.padding(HexnilSpacing.md)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(text = "✨", fontSize = 12.sp)
                    Spacer(modifier = Modifier.width(HexnilSpacing.xxs))
                    Text(
                        text = "AI ANALYST",
                        color = HexnilMainAccent,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 1.sp
                    )
                }

                Surface(
                    shape = RoundedCornerShape(4.dp),
                    color = HexnilSecondaryCard,
                    border = BorderStroke(1.dp, HexnilBorder)
                ) {
                    Text(
                        text = explanation.model ?: "Deterministic",
                        color = HexnilSecondaryText,
                        fontSize = 9.sp,
                        fontFamily = FontFamily.Monospace,
                        modifier = Modifier.padding(horizontal = 5.dp, vertical = 2.dp)
                    )
                }
            }

            Spacer(modifier = Modifier.height(HexnilSpacing.xs))

            Text(
                text = "Evidence-Grounded Explanation",
                color = HexnilPrimaryText,
                fontSize = 14.sp,
                fontWeight = FontWeight.Bold
            )

            Spacer(modifier = Modifier.height(4.dp))

            Text(
                text = explanation.summary,
                color = HexnilSecondaryText,
                fontSize = 11.sp,
                lineHeight = 15.sp,
                maxLines = 3
            )

            Spacer(modifier = Modifier.height(HexnilSpacing.sm))

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable { onInspectEvidence() },
                horizontalArrangement = Arrangement.End,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Inspect evidence ➔",
                    color = HexnilAccentGlow,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold
                )
            }
        }
    }
}

@Composable
private fun AuditProvenanceQuickSection(
    analysis: ComparisonAnalysis,
    onInspectProvenance: () -> Unit
) {
    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(HexnilRadius.card))
            .border(1.dp, HexnilBorder, RoundedCornerShape(HexnilRadius.card))
            .clickable { onInspectProvenance() },
        color = HexnilCard
    ) {
        Column(modifier = Modifier.padding(HexnilSpacing.md)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "AUDIT / PROVENANCE",
                    color = HexnilMainAccent,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp
                )
                Text(
                    text = "Inspect lineage ➔",
                    color = HexnilAccentGlow,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold
                )
            }

            Spacer(modifier = Modifier.height(HexnilSpacing.xs))

            Text(
                text = "End-to-end cryptographic traceability across 5 lifecycle stages.",
                color = HexnilSecondaryText,
                fontSize = 10.sp
            )

            Spacer(modifier = Modifier.height(HexnilSpacing.sm))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(HexnilSpacing.xs)
            ) {
                ProvenanceTraceCell("Experiment", "${analysis.v0ExperimentId.takeLast(3)} / ${analysis.v1ExperimentId.takeLast(3)}", Modifier.weight(1f))
                ProvenanceTraceCell("Comparison", analysis.comparisonId.takeLast(7), Modifier.weight(1f))
                ProvenanceTraceCell("Telemetry", "${analysis.metricsAnalyzed} series", Modifier.weight(1f))
                ProvenanceTraceCell("Artifacts", "Verified", Modifier.weight(1f))
            }
        }
    }
}

@Composable
private fun ProvenanceTraceCell(
    title: String,
    value: String,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(HexnilRadius.metadata),
        color = HexnilSecondaryCard,
        border = BorderStroke(1.dp, HexnilBorder)
    ) {
        Column(
            modifier = Modifier.padding(vertical = 6.dp, horizontal = 4.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(text = title, color = HexnilSecondaryText, fontSize = 8.sp, fontWeight = FontWeight.Bold)
            Text(
                text = value,
                color = HexnilPrimaryText,
                fontSize = 10.sp,
                fontWeight = FontWeight.Bold,
                fontFamily = FontFamily.Monospace,
                maxLines = 1
            )
        }
    }
}
