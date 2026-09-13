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
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.iqoo_hexnil.data.ComparisonAnalysis
import com.example.iqoo_hexnil.data.DeviceHardwareInfo
import com.example.iqoo_hexnil.data.StatisticalMetricResult
import com.example.iqoo_hexnil.data.VerdictType
import com.example.iqoo_hexnil.ui.components.EvidenceCoverageCard
import com.example.iqoo_hexnil.ui.components.HexnilPrimaryButton
import com.example.iqoo_hexnil.ui.components.ResultBadge
import com.example.iqoo_hexnil.ui.components.SectionHeader
import com.example.iqoo_hexnil.ui.theme.HexnilAccentGlow
import com.example.iqoo_hexnil.ui.theme.HexnilBackground
import com.example.iqoo_hexnil.ui.theme.HexnilBorder
import com.example.iqoo_hexnil.ui.theme.HexnilCard
import com.example.iqoo_hexnil.ui.theme.HexnilMainAccent
import com.example.iqoo_hexnil.ui.theme.HexnilPrimaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryCard
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSuccess

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

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(HexnilBackground)
            .padding(horizontal = 16.dp, vertical = 12.dp)
            .verticalScroll(scrollState),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        // Hero Context Card: Device + Release Update Identity
        HeroUpdateIdentityCard(
            device = device,
            v0Exp = analysis.v0ExperimentId,
            v1Exp = analysis.v1ExperimentId
        )

        // Primary Result Section: Update Validation & Evidence Coverage
        EvidenceCoverageCard(analysis = analysis)

        // Hero Measured Change Highlight: Derived dynamically from repository analysis
        val highlightMetric = analysis.metricResults.find { it.workloadId == "video_power_01" }
            ?: analysis.metricResults.firstOrNull()

        if (highlightMetric != null) {
            HeroMeasuredChangeCard(
                metric = highlightMetric,
                onClick = { onNavigateToMetricDetail(highlightMetric.key) }
            )
        }

        // CTA: View Full Results
        HexnilPrimaryButton(
            text = "VIEW COMPLETE RESULTS & EVIDENCE ➔",
            onClick = onNavigateToResults
        )

        Spacer(modifier = Modifier.height(4.dp))

        // Navigation Drill-Down Hub
        SectionHeader(
            category = "AUDIT & EXPLORATION HUB",
            subtitle = "Direct access to deterministic workloads, comparison matrices, and provenance."
        )

        QuickNavigationTile(
            title = "Release Claims & Hypotheses",
            subtitle = "5 Subsystem performance claims prepared for Phase 7 prediction intelligence.",
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
            badge = "CMP-001",
            onClick = onNavigateToComparison
        )

        QuickNavigationTile(
            title = "Measured Evidence vs AI Interpretation",
            subtitle = "Deterministic statistical analysis paired with evidence-grounded AI analyst.",
            icon = "✨",
            badge = "AI ANALYST",
            onClick = onNavigateToAiExplanation
        )

        QuickNavigationTile(
            title = "Experiment Audit Trail & Provenance",
            subtitle = "APK SHA-256 signatures, hardware fingerprints, and artifact hashes.",
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
                Text(
                    text = "RELEASE VALIDATION PIPELINE",
                    color = HexnilMainAccent,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp
                )
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(modifier = Modifier.size(6.dp).background(HexnilSuccess, CircleShape))
                    Spacer(modifier = Modifier.width(4.dp))
                    Text(
                        text = "HARDWARE PAIRED",
                        color = HexnilSuccess,
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
            }

            Spacer(modifier = Modifier.height(10.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        text = "TARGET DEVICE",
                        color = HexnilSecondaryText,
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        text = "${device.manufacturer} ${device.model}",
                        color = HexnilPrimaryText,
                        fontSize = 16.sp,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        text = "Android ${device.androidRelease} · SDK ${device.sdkInt}",
                        color = HexnilSecondaryText,
                        fontSize = 11.sp
                    )
                }

                Surface(
                    shape = RoundedCornerShape(8.dp),
                    color = HexnilSecondaryCard,
                    border = BorderStroke(1.dp, HexnilBorder)
                ) {
                    Column(
                        modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp),
                        horizontalAlignment = Alignment.End
                    ) {
                        Text(
                            text = "SOFTWARE DELTA",
                            color = HexnilSecondaryText,
                            fontSize = 9.sp,
                            fontWeight = FontWeight.Bold
                        )
                        Text(
                            text = "V0 ➔ V1",
                            color = HexnilAccentGlow,
                            fontSize = 14.sp,
                            fontWeight = FontWeight.Black,
                            fontFamily = FontFamily.Monospace
                        )
                        Text(
                            text = "$v0Exp → $v1Exp",
                            color = HexnilSecondaryText,
                            fontSize = 9.sp,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun HeroMeasuredChangeCard(
    metric: StatisticalMetricResult,
    onClick: () -> Unit
) {
    val v0Text = if (metric.v0Mean != null) "${"%.1f".format(metric.v0Mean / 1000.0)} s" else "Unavailable"
    val v1Text = if (metric.v1Mean != null) "${"%.1f".format(metric.v1Mean / 1000.0)} s" else "Unavailable"
    val deltaText = if (metric.percentDelta != null) "${if (metric.percentDelta >= 0) "+" else ""}${"%.1f".format(metric.percentDelta)}%" else "Unavailable"

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
                    text = "PRIMARY MEASURED HIGHLIGHT",
                    color = HexnilMainAccent,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp
                )
                ResultBadge(verdict = metric.verdict, isCompact = true)
            }

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                text = "${metric.displayName} (${metric.workloadId})",
                color = HexnilPrimaryText,
                fontSize = 14.sp,
                fontWeight = FontWeight.Bold
            )

            Spacer(modifier = Modifier.height(10.dp))

            // Comparison row
            Surface(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(8.dp),
                color = HexnilSecondaryCard,
                border = BorderStroke(1.dp, HexnilBorder)
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 12.dp, vertical = 10.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column {
                        Text(text = "V0 BASELINE", color = HexnilSecondaryText, fontSize = 9.sp, fontWeight = FontWeight.Bold)
                        Text(
                            text = v0Text,
                            color = HexnilPrimaryText,
                            fontSize = 16.sp,
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
                            fontSize = 16.sp,
                            fontWeight = FontWeight.Bold,
                            fontFamily = FontFamily.Monospace
                        )
                    }

                    Column(horizontalAlignment = Alignment.End) {
                        Text(text = "DELTA", color = HexnilSecondaryText, fontSize = 9.sp, fontWeight = FontWeight.Bold)
                        Text(
                            text = deltaText,
                            color = HexnilMainAccent,
                            fontSize = 16.sp,
                            fontWeight = FontWeight.Bold,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(10.dp))

            // Why section
            Surface(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(6.dp),
                color = HexnilSecondaryCard
            ) {
                Row(modifier = Modifier.padding(10.dp)) {
                    Text(text = "Why? ", color = HexnilMainAccent, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                    Text(
                        text = metric.reason,
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
