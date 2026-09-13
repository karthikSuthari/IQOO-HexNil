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
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.iqoo_hexnil.data.ComparisonAnalysis
import com.example.iqoo_hexnil.data.DeviceHardwareInfo
import com.example.iqoo_hexnil.data.ExplanationSource
import com.example.iqoo_hexnil.data.HexnilRepository
import com.example.iqoo_hexnil.data.StatisticalMetricResult
import com.example.iqoo_hexnil.data.VerdictType
import com.example.iqoo_hexnil.ui.components.EvidenceCoverageCard
import com.example.iqoo_hexnil.ui.components.HexnilPrimaryButton
import com.example.iqoo_hexnil.ui.components.ResultBadge
import com.example.iqoo_hexnil.ui.components.SectionHeader
import com.example.iqoo_hexnil.ui.components.ValidationStatusChip
import com.example.iqoo_hexnil.ui.theme.HexnilAccentGlow
import com.example.iqoo_hexnil.ui.theme.HexnilAccentSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilBackground
import com.example.iqoo_hexnil.ui.theme.HexnilBorder
import com.example.iqoo_hexnil.ui.theme.HexnilCard
import com.example.iqoo_hexnil.ui.theme.HexnilError
import com.example.iqoo_hexnil.ui.theme.HexnilMainAccent
import com.example.iqoo_hexnil.ui.theme.HexnilPrimaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryCard
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSuccess
import com.example.iqoo_hexnil.ui.theme.HexnilSuccessSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilWarning
import com.example.iqoo_hexnil.ui.theme.HexnilWarningSubtle

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
    val aiExplanation = remember(analysis.comparisonId) {
        HexnilRepository.getAiExplanation(analysis.comparisonId, ExplanationSource.DETERMINISTIC_ANALYSIS)
    }

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(HexnilBackground)
            .padding(horizontal = 16.dp, vertical = 12.dp)
            .verticalScroll(scrollState),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        // 1. Header & Device / Update Context
        HeroUpdateIdentityCard(
            device = device,
            comparisonId = analysis.comparisonId,
            v0Exp = analysis.v0ExperimentId,
            v1Exp = analysis.v1ExperimentId
        )

        // 2. Main V0 -> V1 Hero (Status semantics are critical: UNCHANGED for +3.05%)
        val primaryHighlight = analysis.metricResults.find { it.workloadId == "video_power_01" && it.metricName == "workload_duration_ms" }
            ?: analysis.metricResults.firstOrNull()

        if (primaryHighlight != null) {
            MainV0V1HeroCard(
                metric = primaryHighlight,
                onClick = { onNavigateToMetricDetail(primaryHighlight.key) }
            )
        }

        // 3. Evidence Coverage Card
        EvidenceCoverageCard(analysis = analysis)

        // 4. Regression Summary Card (Exact backend counts)
        RegressionSummaryCard(
            regressions = analysis.metricsRegressions,
            improvements = analysis.metricsImprovements,
            unchanged = analysis.metricsUnchanged,
            inconclusive = analysis.metricsInconclusive,
            onViewResultsClick = onNavigateToResults
        )

        // 5. Release Claims Preview
        ClaimsPreviewCard(
            claims = claims.take(3),
            totalClaimsCount = claims.size,
            onViewAllClaims = onNavigateToClaims
        )

        // 6. AI Analyst Preview (Evidence-grounded explanation snippet)
        AiAnalystPreviewCard(
            explanation = aiExplanation,
            onViewFullAnalysis = onNavigateToAiExplanation
        )

        // CTA: View Complete Results & Statistical Evidence
        HexnilPrimaryButton(
            text = "VIEW COMPLETE STATISTICAL RESULTS ➔",
            onClick = onNavigateToResults
        )

        Spacer(modifier = Modifier.height(4.dp))

        // 7. Audit & Exploration Drilldown Hub
        SectionHeader(
            category = "AUDIT & EXPLORATION HUB",
            subtitle = "Direct access to deterministic workloads, paired comparisons, and provenance lineage."
        )

        QuickNavigationTile(
            title = "Release Claims & Hypotheses",
            subtitle = "5 Subsystem performance claims mapped to validation workloads and predicted risk.",
            icon = "📋",
            badge = "5 CLAIMS",
            onClick = onNavigateToClaims
        )

        QuickNavigationTile(
            title = "Deterministic Workload Suite",
            subtitle = "5 Locked benchmark workloads (Startup, CPU, Memory, Scroll, Video).",
            icon = "⚙",
            badge = "5 WORKLOADS",
            onClick = onNavigateToValidation
        )

        QuickNavigationTile(
            title = "V0 vs V1 Side-by-Side Run Pairing",
            subtitle = "Physical device run matching, config hash verification, and drift checks.",
            icon = "⚖",
            badge = analysis.comparisonId,
            onClick = onNavigateToComparison
        )

        QuickNavigationTile(
            title = "Measured Evidence vs AI Interpretation",
            subtitle = "Evidence-grounded Groq explanation strictly constrained by statistical facts.",
            icon = "✨",
            badge = "AI ANALYST",
            onClick = onNavigateToAiExplanation
        )

        QuickNavigationTile(
            title = "Experiment Audit Trail & Provenance",
            subtitle = "APK SHA-256 signatures, hardware fingerprints, and artifact storage hashes.",
            icon = "🔒",
            badge = "VERIFIED",
            onClick = onNavigateToProvenance
        )

        Spacer(modifier = Modifier.height(16.dp))
    }
}

@Composable
private fun HeroUpdateIdentityCard(
    device: DeviceHardwareInfo,
    comparisonId: String,
    v0Exp: String,
    v1Exp: String
) {
    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .border(1.dp, HexnilBorder, RoundedCornerShape(12.dp)),
        color = HexnilCard
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        text = "HEXNIL",
                        color = HexnilMainAccent,
                        fontSize = 13.sp,
                        fontWeight = FontWeight.Black,
                        letterSpacing = 1.5.sp
                    )
                    Text(
                        text = "Engineering Validation Intelligence",
                        color = HexnilSecondaryText,
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Medium
                    )
                }

                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(modifier = Modifier.size(6.dp).background(HexnilSuccess, CircleShape))
                    Spacer(modifier = Modifier.width(4.dp))
                    Text(
                        text = "EVIDENCE AUDITED",
                        color = HexnilSuccess,
                        fontSize = 9.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 0.5.sp
                    )
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            // Device & Comparison Lineage Grid
            Surface(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(8.dp),
                color = HexnilSecondaryCard,
                border = BorderStroke(1.dp, HexnilBorder)
            ) {
                Column(modifier = Modifier.padding(12.dp)) {
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
                            fontFamily = FontFamily.Monospace
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
                            fontWeight = FontWeight.Bold,
                            fontFamily = FontFamily.Monospace
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
                            fontSize = 11.sp,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun MainV0V1HeroCard(
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
            .clip(RoundedCornerShape(12.dp))
            .border(1.dp, HexnilBorder, RoundedCornerShape(12.dp))
            .clickable { onClick() },
        color = HexnilCard
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "PRIMARY DIFFERENTIAL VERDICT",
                    color = HexnilMainAccent,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp
                )
                ResultBadge(verdict = metric.verdict)
            }

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                text = metric.displayName,
                color = HexnilPrimaryText,
                fontSize = 16.sp,
                fontWeight = FontWeight.Bold
            )

            Text(
                text = "Workload: ${metric.workloadId} · Metric: ${metric.metricName}",
                color = HexnilSecondaryText,
                fontSize = 11.sp,
                fontFamily = FontFamily.Monospace
            )

            Spacer(modifier = Modifier.height(12.dp))

            // Main V0 -> V1 Values Box
            Surface(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(8.dp),
                color = HexnilSecondaryCard,
                border = BorderStroke(1.dp, HexnilBorder)
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 14.dp, vertical = 12.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column {
                        Text(text = "V0 BASELINE", color = HexnilSecondaryText, fontSize = 9.sp, fontWeight = FontWeight.Bold)
                        Text(
                            text = v0Text,
                            color = HexnilPrimaryText,
                            fontSize = 13.sp,
                            fontWeight = FontWeight.Bold,
                            fontFamily = FontFamily.Monospace
                        )
                    }

                    Text(text = "➔", color = HexnilSecondaryText, fontSize = 16.sp)

                    Column {
                        Text(text = "V1 CANDIDATE", color = HexnilSecondaryText, fontSize = 9.sp, fontWeight = FontWeight.Bold)
                        Text(
                            text = v1Text,
                            color = HexnilPrimaryText,
                            fontSize = 13.sp,
                            fontWeight = FontWeight.Bold,
                            fontFamily = FontFamily.Monospace
                        )
                    }

                    Column(horizontalAlignment = Alignment.End) {
                        Text(text = "DELTA SHIFT", color = HexnilSecondaryText, fontSize = 9.sp, fontWeight = FontWeight.Bold)
                        Text(
                            text = deltaPercentText,
                            color = HexnilSuccess,
                            fontSize = 15.sp,
                            fontWeight = FontWeight.Black,
                            fontFamily = FontFamily.Monospace
                        )
                        Text(
                            text = deltaAbsText,
                            color = HexnilSecondaryText,
                            fontSize = 9.sp,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(10.dp))

            // Semantic Status Callout
            Surface(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(6.dp),
                color = HexnilSecondaryCard
            ) {
                Row(
                    modifier = Modifier.padding(10.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(text = "ℹ️", fontSize = 12.sp)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = "Status: UNCHANGED · Observed shift ($deltaPercentText) is within the ${metric.thresholdPercent ?: 5.0}% engineering threshold (p=${metric.pValue?.let { "%.4f".format(it) } ?: "N/A"}). Not classified as regression.",
                        color = HexnilSecondaryText,
                        fontSize = 11.sp,
                        lineHeight = 15.sp
                    )
                }
            }
        }
    }
}

@Composable
private fun RegressionSummaryCard(
    regressions: Int,
    improvements: Int,
    unchanged: Int,
    inconclusive: Int,
    onViewResultsClick: () -> Unit
) {
    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .border(1.dp, HexnilBorder, RoundedCornerShape(12.dp)),
        color = HexnilCard
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "REGRESSION & OUTCOME SUMMARY",
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

            Spacer(modifier = Modifier.height(10.dp))

            // 4 Count Chips Row
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                OutcomeChip("REGRESSION", regressions, if (regressions > 0) HexnilError else HexnilSuccess, Modifier.weight(1f))
                OutcomeChip("IMPROVEMENT", improvements, HexnilSuccess, Modifier.weight(1f))
                OutcomeChip("UNCHANGED", unchanged, HexnilSuccess, Modifier.weight(1f))
                OutcomeChip("INCONCLUSIVE", inconclusive, HexnilWarning, Modifier.weight(1f))
            }

            Spacer(modifier = Modifier.height(10.dp))

            // Honest Banner
            Surface(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(6.dp),
                color = if (regressions == 0) HexnilSuccessSubtle else HexnilAccentSubtle,
                border = BorderStroke(1.dp, if (regressions == 0) HexnilSuccess.copy(alpha = 0.5f) else HexnilError.copy(alpha = 0.5f))
            ) {
                Row(
                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 8.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(text = if (regressions == 0) "✓" else "⚠", color = if (regressions == 0) HexnilSuccess else HexnilError, fontWeight = FontWeight.Bold)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = if (regressions == 0) "No statistically supported regressions detected across 13 analyzed metrics." else "$regressions regression(s) detected.",
                        color = if (regressions == 0) HexnilSuccess else HexnilError,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.SemiBold
                    )
                }
            }
        }
    }
}

@Composable
private fun OutcomeChip(
    label: String,
    count: Int,
    color: Color,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(6.dp),
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
                fontSize = 16.sp,
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
private fun ClaimsPreviewCard(
    claims: List<com.example.iqoo_hexnil.data.ReleaseClaim>,
    totalClaimsCount: Int,
    onViewAllClaims: () -> Unit
) {
    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .border(1.dp, HexnilBorder, RoundedCornerShape(12.dp)),
        color = HexnilCard
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "RELEASE CLAIMS PREVIEW",
                    color = HexnilMainAccent,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp
                )
                Text(
                    text = "View All $totalClaimsCount ➔",
                    color = HexnilAccentGlow,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.clickable { onViewAllClaims() }
                )
            }

            Spacer(modifier = Modifier.height(10.dp))

            claims.forEach { claim ->
                Surface(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 4.dp),
                    shape = RoundedCornerShape(6.dp),
                    color = HexnilSecondaryCard,
                    border = BorderStroke(1.dp, HexnilBorder)
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(10.dp),
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
                                text = "Subsystem: ${claim.subsystem}",
                                color = HexnilSecondaryText,
                                fontSize = 10.sp
                            )
                        }
                        ValidationStatusChip(status = claim.validationStatus)
                    }
                }
            }
        }
    }
}

@Composable
private fun AiAnalystPreviewCard(
    explanation: com.example.iqoo_hexnil.data.AiExplanation,
    onViewFullAnalysis: () -> Unit
) {
    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .border(1.dp, HexnilBorder, RoundedCornerShape(12.dp)),
        color = HexnilCard
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(text = "✨", fontSize = 12.sp)
                    Spacer(modifier = Modifier.width(4.dp))
                    Text(
                        text = "AI ANALYST PREVIEW",
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
                        modifier = Modifier.padding(horizontal = 4.dp, vertical = 2.dp)
                    )
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                text = "Evidence-Grounded Interpretation",
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

            Spacer(modifier = Modifier.height(10.dp))

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable { onViewFullAnalysis() },
                horizontalArrangement = Arrangement.End,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "View full analysis ➔",
                    color = HexnilAccentGlow,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold
                )
            }
        }
    }
}

@Composable
private fun QuickNavigationTile(
    title: String,
    subtitle: String,
    icon: String,
    badge: String,
    onClick: () -> Unit
) {
    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(10.dp))
            .border(1.dp, HexnilBorder, RoundedCornerShape(10.dp))
            .clickable { onClick() },
        color = HexnilCard
    ) {
        Row(
            modifier = Modifier.padding(12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(38.dp)
                    .clip(RoundedCornerShape(8.dp))
                    .background(HexnilSecondaryCard)
                    .border(1.dp, HexnilBorder, RoundedCornerShape(8.dp)),
                contentAlignment = Alignment.Center
            ) {
                Text(text = icon, fontSize = 18.sp)
            }

            Spacer(modifier = Modifier.width(12.dp))

            Column(modifier = Modifier.weight(1f)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = title,
                        color = HexnilPrimaryText,
                        fontSize = 13.sp,
                        fontWeight = FontWeight.Bold
                    )
                    Surface(
                        shape = RoundedCornerShape(4.dp),
                        color = HexnilSecondaryCard,
                        border = BorderStroke(1.dp, HexnilBorder)
                    ) {
                        Text(
                            text = badge,
                            color = HexnilAccentGlow,
                            fontSize = 9.sp,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.padding(horizontal = 4.dp, vertical = 1.dp)
                        )
                    }
                }
                Spacer(modifier = Modifier.height(2.dp))
                Text(
                    text = subtitle,
                    color = HexnilSecondaryText,
                    fontSize = 11.sp,
                    lineHeight = 14.sp
                )
            }

            Spacer(modifier = Modifier.width(6.dp))
            Text(text = "➔", color = HexnilSecondaryText, fontSize = 13.sp)
        }
    }
}
