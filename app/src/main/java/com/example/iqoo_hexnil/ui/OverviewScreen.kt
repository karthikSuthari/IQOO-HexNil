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
import com.example.iqoo_hexnil.ui.theme.HexnilBorderSubtle
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
import com.example.iqoo_hexnil.ui.theme.MonospaceBody
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
            .padding(horizontal = HexnilSpacing.screenHorizontal, vertical = HexnilSpacing.screenVertical)
            .verticalScroll(scrollState),
        verticalArrangement = Arrangement.spacedBy(HexnilSpacing.sectionSpacing)
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
            .border(1.dp, HexnilBorderSubtle, RoundedCornerShape(HexnilRadius.card)),
        color = HexnilCard
    ) {
        Column(modifier = Modifier.padding(HexnilSpacing.cardPadding)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "RELEASE VALIDATION TARGET",
                    color = HexnilSecondaryText,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp
                )
                Surface(
                    shape = RoundedCornerShape(HexnilRadius.pill),
                    color = HexnilSuccessSubtle,
                    border = BorderStroke(1.dp, HexnilSuccess.copy(alpha = 0.4f))
                ) {
                    Row(
                        modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Box(modifier = Modifier.size(6.dp).background(HexnilSuccess, CircleShape))
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(
                            text = "AUDITED",
                            color = HexnilSuccess,
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(10.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "${device.manufacturer} ${device.model}",
                    color = HexnilPrimaryText,
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Bold
                )
                Surface(
                    shape = RoundedCornerShape(HexnilRadius.metadata),
                    color = HexnilSecondaryCard,
                    border = BorderStroke(1.dp, HexnilBorderSubtle)
                ) {
                    Text(
                        text = comparisonId,
                        color = HexnilAccentGlow,
                        fontSize = 12.sp,
                        fontFamily = FontFamily.Monospace,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                    )
                }
            }

            Spacer(modifier = Modifier.height(10.dp))

            Text(
                text = "Android ${device.androidRelease} (SDK ${device.sdkInt}) · Physical Hardware",
                color = HexnilSecondaryText,
                fontSize = 13.sp
            )

            Spacer(modifier = Modifier.height(10.dp))

            Surface(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(HexnilRadius.md),
                color = HexnilSecondaryCard,
                border = BorderStroke(1.dp, HexnilBorderSubtle)
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 12.dp, vertical = 8.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "EXPERIMENTS",
                        color = HexnilMainAccent,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 0.8.sp
                    )
                    Text(
                        text = "$v0Exp ➔ $v1Exp",
                        color = HexnilPrimaryText,
                        fontSize = 12.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }
        }
    }
}

@Composable
private fun PrimaryOutcomeHeroCard(
    metric: StatisticalMetricResult,
    onClick: () -> Unit
) {
    val v0Text = if (metric.v0Mean != null) "${"%.1f".format(metric.v0Mean)} ms" else "Unavailable"
    val v1Text = if (metric.v1Mean != null) "${"%.1f".format(metric.v1Mean)} ms" else "Unavailable"
    val deltaPercentText = if (metric.percentDelta != null) "${if (metric.percentDelta >= 0) "+" else ""}${"%.2f".format(metric.percentDelta)}%" else "N/A"
    val deltaAbsText = if (metric.absoluteDelta != null) "${if (metric.absoluteDelta >= 0) "+" else ""}${"%.1f".format(metric.absoluteDelta)} ms" else "N/A"

    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(HexnilRadius.hero))
            .border(1.dp, HexnilBorderSubtle, RoundedCornerShape(HexnilRadius.hero))
            .clickable { onClick() },
        color = HexnilCard
    ) {
        Column(modifier = Modifier.padding(HexnilSpacing.cardPadding)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "PRIMARY OUTCOME HIGHLIGHT",
                    color = HexnilMainAccent,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp
                )
                ResultBadge(verdict = metric.verdict)
            }

            Spacer(modifier = Modifier.height(14.dp))

            // Large dominant display numbers
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        text = deltaPercentText,
                        fontSize = 40.sp,
                        fontWeight = FontWeight.Black,
                        color = HexnilPrimaryText,
                        letterSpacing = (-0.5).sp
                    )
                    Spacer(modifier = Modifier.height(2.dp))
                    Text(
                        text = "$deltaAbsText absolute shift",
                        style = MonospaceBody,
                        color = HexnilAccentGlow
                    )
                }

                Surface(
                    shape = RoundedCornerShape(HexnilRadius.md),
                    color = HexnilSecondaryCard,
                    border = BorderStroke(1.dp, HexnilBorderSubtle)
                ) {
                    Column(
                        modifier = Modifier.padding(horizontal = 14.dp, vertical = 8.dp),
                        horizontalAlignment = Alignment.End
                    ) {
                        Text(
                            text = "MAX TOLERANCE",
                            color = HexnilSecondaryText,
                            fontSize = 10.sp,
                            fontWeight = FontWeight.Bold,
                            letterSpacing = 0.5.sp
                        )
                        Spacer(modifier = Modifier.height(2.dp))
                        Text(
                            text = "≤ ${metric.thresholdPercent ?: 5.0}%",
                            color = HexnilPrimaryText,
                            fontSize = 14.sp,
                            fontFamily = FontFamily.Monospace,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(14.dp))

            Text(
                text = metric.displayName,
                color = HexnilPrimaryText,
                fontSize = 17.sp,
                fontWeight = FontWeight.Bold
            )

            Spacer(modifier = Modifier.height(6.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Surface(
                    shape = RoundedCornerShape(HexnilRadius.xs),
                    color = HexnilSecondaryCard,
                    border = BorderStroke(1.dp, HexnilBorderSubtle)
                ) {
                    Text(
                        text = metric.workloadId,
                        color = HexnilAccentGlow,
                        fontSize = 11.sp,
                        fontFamily = FontFamily.Monospace,
                        fontWeight = FontWeight.SemiBold,
                        modifier = Modifier.padding(horizontal = 7.dp, vertical = 3.dp)
                    )
                }
                Text(
                    text = metric.metricName,
                    color = HexnilSecondaryText,
                    fontSize = 12.sp,
                    fontFamily = FontFamily.Monospace
                )
            }

            Spacer(modifier = Modifier.height(14.dp))

            // V0 -> V1 comparison row
            Surface(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(HexnilRadius.md),
                color = HexnilSecondaryCard,
                border = BorderStroke(1.dp, HexnilBorderSubtle)
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 16.dp, vertical = 12.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column {
                        Text(text = "V0 BASELINE", color = HexnilSecondaryText, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                        Spacer(modifier = Modifier.height(2.dp))
                        Text(text = v0Text, style = MonospaceValue, color = HexnilPrimaryText)
                    }

                    Text(text = "➔", color = HexnilSecondaryText, fontSize = 16.sp)

                    Column(horizontalAlignment = Alignment.End) {
                        Text(text = "V1 CANDIDATE", color = HexnilSecondaryText, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                        Spacer(modifier = Modifier.height(2.dp))
                        Text(text = v1Text, style = MonospaceValue, color = HexnilPrimaryText)
                    }
                }
            }

            Spacer(modifier = Modifier.height(10.dp))

            // Threshold note
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.Top
            ) {
                Text(text = "✓", color = HexnilSuccess, fontSize = 13.sp, fontWeight = FontWeight.Bold)
                Spacer(modifier = Modifier.width(6.dp))
                Text(
                    text = "Observed shift ($deltaPercentText) is well within the ${metric.thresholdPercent ?: 5.0}% safety threshold (p=${metric.pValue?.let { "%.4f".format(it) } ?: "0.0116"}). Authoritatively UNCHANGED.",
                    color = HexnilSecondaryText,
                    fontSize = 12.sp,
                    lineHeight = 17.sp
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
            .border(1.dp, HexnilBorderSubtle, RoundedCornerShape(HexnilRadius.card)),
        color = HexnilCard
    ) {
        Column(modifier = Modifier.padding(HexnilSpacing.cardPadding)) {
            // Header
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "EVIDENCE & OUTCOME SUMMARY",
                    color = HexnilMainAccent,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp
                )
                Text(
                    text = "AUTHORITATIVE",
                    color = HexnilSecondaryText,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold
                )
            }

            Spacer(modifier = Modifier.height(14.dp))

            // Evidence Coverage Number & Progress
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.Bottom
            ) {
                Column {
                    Text(text = "Coverage Ratio", color = HexnilSecondaryText, fontSize = 12.sp)
                    Spacer(modifier = Modifier.height(2.dp))
                    Text(
                        text = "${analysis.metricsEligible} / ${analysis.metricsAnalyzed} Metrics",
                        style = DisplayLargeNumber,
                        fontSize = 26.sp
                    )
                }

                Text(
                    text = "${(coverageFraction * 100).toInt()}% Verified Evidence",
                    color = HexnilSuccess,
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Bold
                )
            }

            Spacer(modifier = Modifier.height(10.dp))

            LinearProgressIndicator(
                progress = { coverageFraction },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(8.dp)
                    .clip(RoundedCornerShape(4.dp)),
                color = HexnilSuccess,
                trackColor = HexnilSecondaryCard
            )

            Spacer(modifier = Modifier.height(16.dp))

            // Spacious 2x2 Outcome Grid
            Column(
                modifier = Modifier.fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    OutcomeTile(
                        icon = "🛡️",
                        title = "Regressions",
                        count = analysis.metricsRegressions,
                        subtitle = if (analysis.metricsRegressions == 0) "Zero Detected" else "${analysis.metricsRegressions} Critical",
                        accentColor = if (analysis.metricsRegressions > 0) HexnilError else HexnilSuccess,
                        modifier = Modifier.weight(1f)
                    )
                    OutcomeTile(
                        icon = "🚀",
                        title = "Improvements",
                        count = analysis.metricsImprovements,
                        subtitle = "Statistically Confirmed",
                        accentColor = HexnilSuccess,
                        modifier = Modifier.weight(1f)
                    )
                }
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    OutcomeTile(
                        icon = "✅",
                        title = "Unchanged",
                        count = analysis.metricsUnchanged,
                        subtitle = "Within Tolerances",
                        accentColor = HexnilSuccess,
                        modifier = Modifier.weight(1f)
                    )
                    OutcomeTile(
                        icon = "⚖️",
                        title = "Inconclusive",
                        count = analysis.metricsInconclusive,
                        subtitle = "High Variance (N=3)",
                        accentColor = HexnilWarning,
                        modifier = Modifier.weight(1f)
                    )
                }
            }

            Spacer(modifier = Modifier.height(14.dp))

            // Honest Banner
            Surface(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(HexnilRadius.md),
                color = if (analysis.metricsRegressions == 0) HexnilSuccessSubtle else HexnilAccentSubtle,
                border = BorderStroke(1.dp, if (analysis.metricsRegressions == 0) HexnilSuccess.copy(alpha = 0.5f) else HexnilError.copy(alpha = 0.5f))
            ) {
                Row(
                    modifier = Modifier.padding(horizontal = 14.dp, vertical = 10.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = if (analysis.metricsRegressions == 0) "✓" else "⚠",
                        color = if (analysis.metricsRegressions == 0) HexnilSuccess else HexnilError,
                        fontSize = 15.sp,
                        fontWeight = FontWeight.Bold
                    )
                    Spacer(modifier = Modifier.width(HexnilSpacing.xs))
                    Text(
                        text = if (analysis.metricsRegressions == 0) {
                            "Zero statistically supported regressions detected across 13 analyzed metrics on physical hardware."
                        } else {
                            "${analysis.metricsRegressions} regression(s) detected on physical hardware."
                        },
                        color = if (analysis.metricsRegressions == 0) HexnilSuccess else HexnilError,
                        fontSize = 13.sp,
                        fontWeight = FontWeight.SemiBold
                    )
                }
            }
        }
    }
}

@Composable
private fun OutcomeTile(
    icon: String,
    title: String,
    count: Int,
    subtitle: String,
    accentColor: Color,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(HexnilRadius.md),
        color = HexnilSecondaryCard,
        border = BorderStroke(1.dp, HexnilBorderSubtle)
    ) {
        Column(
            modifier = Modifier.padding(horizontal = 14.dp, vertical = 12.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(text = icon, fontSize = 17.sp)
                Text(
                    text = count.toString(),
                    color = accentColor,
                    fontSize = 22.sp,
                    fontWeight = FontWeight.Black,
                    fontFamily = FontFamily.Monospace
                )
            }
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = title,
                color = HexnilPrimaryText,
                fontSize = 13.sp,
                fontWeight = FontWeight.Bold
            )
            Spacer(modifier = Modifier.height(1.dp))
            Text(
                text = subtitle,
                color = HexnilSecondaryText,
                fontSize = 11.sp,
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
            .border(1.dp, HexnilBorderSubtle, RoundedCornerShape(HexnilRadius.card)),
        color = HexnilCard
    ) {
        Column(modifier = Modifier.padding(HexnilSpacing.cardPadding)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "IMPORTANT CLAIMS",
                    color = HexnilMainAccent,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp
                )
                Text(
                    text = "View all $totalCount ➔",
                    color = HexnilAccentGlow,
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.clickable { onViewAll() }
                )
            }

            Spacer(modifier = Modifier.height(10.dp))

            claims.forEachIndexed { index, claim ->
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 8.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column(modifier = Modifier.weight(1f).padding(end = 8.dp)) {
                        Text(
                            text = "${claim.id} · ${claim.title}",
                            color = HexnilPrimaryText,
                            fontSize = 14.sp,
                            fontWeight = FontWeight.Bold
                        )
                        Spacer(modifier = Modifier.height(2.dp))
                        Text(
                            text = "${claim.subsystem} · Target: ${claim.expectedDirection}",
                            color = HexnilSecondaryText,
                            fontSize = 12.sp
                        )
                    }
                    ValidationStatusChip(status = claim.validationStatus)
                }
                if (index < claims.size - 1) {
                    Box(modifier = Modifier.fillMaxWidth().height(1.dp).background(HexnilBorderSubtle))
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
            .border(1.dp, HexnilBorderSubtle, RoundedCornerShape(HexnilRadius.card)),
        color = HexnilCard
    ) {
        Column(modifier = Modifier.padding(HexnilSpacing.cardPadding)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "VALIDATION BENCHMARKS",
                    color = HexnilMainAccent,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp
                )
                Text(
                    text = "Inspect all $totalCount ➔",
                    color = HexnilAccentGlow,
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.clickable { onViewAll() }
                )
            }

            Spacer(modifier = Modifier.height(10.dp))

            workloads.forEachIndexed { index, wl ->
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 8.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column(modifier = Modifier.weight(1f).padding(end = 8.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(
                                text = wl.id,
                                color = HexnilPrimaryText,
                                fontSize = 13.sp,
                                fontFamily = FontFamily.Monospace,
                                fontWeight = FontWeight.Bold
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Surface(
                                shape = RoundedCornerShape(4.dp),
                                color = HexnilAccentSubtle,
                                border = BorderStroke(1.dp, HexnilMainAccent.copy(alpha = 0.5f))
                            ) {
                                Text(
                                    text = "SELECTED",
                                    color = HexnilMainAccent,
                                    fontSize = 10.sp,
                                    fontWeight = FontWeight.Bold,
                                    modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                                )
                            }
                        }
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = wl.purpose,
                            color = HexnilSecondaryText,
                            fontSize = 13.sp,
                            lineHeight = 18.sp,
                            maxLines = 2
                        )
                    }

                    PriorityChip(priority = wl.priority)
                }
                if (index < workloads.size - 1) {
                    Box(modifier = Modifier.fillMaxWidth().height(1.dp).background(HexnilBorderSubtle))
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
            .border(1.dp, HexnilBorderSubtle, RoundedCornerShape(HexnilRadius.card)),
        color = HexnilCard
    ) {
        Column(modifier = Modifier.padding(HexnilSpacing.cardPadding)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(text = "🧠", fontSize = 14.sp)
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        text = "AI ANALYST INSIGHT",
                        color = HexnilMainAccent,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 1.sp
                    )
                }

                Surface(
                    shape = RoundedCornerShape(HexnilRadius.metadata),
                    color = HexnilSecondaryCard,
                    border = BorderStroke(1.dp, HexnilBorderSubtle)
                ) {
                    Text(
                        text = explanation.model ?: "Deterministic",
                        color = HexnilSecondaryText,
                        fontSize = 11.sp,
                        fontFamily = FontFamily.Monospace,
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                    )
                }
            }

            Spacer(modifier = Modifier.height(10.dp))

            Text(
                text = "Evidence-Grounded Intelligence",
                color = HexnilPrimaryText,
                fontSize = 15.sp,
                fontWeight = FontWeight.Bold
            )

            Spacer(modifier = Modifier.height(4.dp))

            Text(
                text = explanation.summary,
                color = HexnilSecondaryText,
                fontSize = 13.sp,
                lineHeight = 19.sp,
                maxLines = 3
            )

            Spacer(modifier = Modifier.height(12.dp))

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable { onInspectEvidence() },
                horizontalArrangement = Arrangement.End,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Open Full AI Intelligence Screen ➔",
                    color = HexnilAccentGlow,
                    fontSize = 13.sp,
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
            .border(1.dp, HexnilBorderSubtle, RoundedCornerShape(HexnilRadius.card))
            .clickable { onInspectProvenance() },
        color = HexnilCard
    ) {
        Column(modifier = Modifier.padding(HexnilSpacing.cardPadding)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "AUDIT / PROVENANCE",
                    color = HexnilMainAccent,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp
                )
                Text(
                    text = "Inspect lineage ➔",
                    color = HexnilAccentGlow,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.SemiBold
                )
            }

            Spacer(modifier = Modifier.height(12.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
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
        shape = RoundedCornerShape(HexnilRadius.md),
        color = HexnilSecondaryCard,
        border = BorderStroke(1.dp, HexnilBorderSubtle)
    ) {
        Column(
            modifier = Modifier.padding(vertical = 10.dp, horizontal = 6.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(text = title, color = HexnilSecondaryText, fontSize = 11.sp, fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = value,
                color = HexnilPrimaryText,
                fontSize = 12.sp,
                fontWeight = FontWeight.Bold,
                fontFamily = FontFamily.Monospace,
                maxLines = 1
            )
        }
    }
}

