package com.example.iqoo_hexnil.ui

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
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
fun ExperimentDetailScreen(
    analysis: ComparisonAnalysis,
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
        // Audit Header Card
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
                        text = "AUDIT TRAIL & PROVENANCE",
                        color = HexnilMainAccent,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 1.sp
                    )
                    Surface(
                        shape = RoundedCornerShape(4.dp),
                        color = HexnilSecondaryCard,
                        border = BorderStroke(1.dp, HexnilSuccess.copy(alpha = 0.5f))
                    ) {
                        Text(
                            text = "INTEGRITY VERIFIED",
                            color = HexnilSuccess,
                            fontSize = 9.sp,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                        )
                    }
                }

                Spacer(modifier = Modifier.height(6.dp))
                Text(
                    text = "Cryptographic Reproducibility",
                    color = HexnilPrimaryText,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = "Every observation traces back to immutable experiment IDs, artifact storage directories, APK SHA-256 signatures, and deterministic configuration hashes.",
                    color = HexnilSecondaryText,
                    fontSize = 12.sp,
                    lineHeight = 16.sp
                )
            }
        }

        // Full Evidence Lineage Chain
        SectionHeader(
            category = "TRACEABLE EVIDENCE LINEAGE",
            subtitle = "Comparison ➔ V0 Baseline ➔ V1 Candidate ➔ Workloads ➔ Telemetry ➔ Evidence"
        )

        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(12.dp))
                .border(1.dp, HexnilBorder, RoundedCornerShape(12.dp)),
            color = HexnilCard
        ) {
            Column(modifier = Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                LineageStepNode(
                    stepNumber = "1",
                    stepName = "COMPARISON LEVEL",
                    identifier = analysis.comparisonId,
                    description = "Matched differential experiment paired on identical device hardware (${analysis.deviceModel})."
                )
                LineageStepNode(
                    stepNumber = "2",
                    stepName = "EXPERIMENT IDENTIFIERS",
                    identifier = "V0: ${analysis.v0ExperimentId} ➔ V1: ${analysis.v1ExperimentId}",
                    description = "Locked baseline and candidate execution runs with isolated software deltas."
                )
                LineageStepNode(
                    stepNumber = "3",
                    stepName = "WORKLOAD BENCHMARKS",
                    identifier = "5 Locked Suites (Startup, CPU, Memory, Scroll, Video)",
                    description = "Deterministic iterations executed with locked seed (42) and capability-aware telemetry."
                )
                LineageStepNode(
                    stepNumber = "4",
                    stepName = "RAW TELEMETRY AUDIT",
                    identifier = "13 Metric Series (9 Eligible, 8 Unchanged, 5 Inconclusive)",
                    description = "Pairwise differences computed per iteration. Zero regressions detected below 5% threshold."
                )
                LineageStepNode(
                    stepNumber = "5",
                    stepName = "IMMUTABLE STORAGE ARTIFACTS",
                    identifier = "data/experiments/comparisons/${analysis.comparisonId}/",
                    description = "Full statistical analysis JSON and cryptographically sealed package.",
                    isLast = true
                )
            }
        }

        // Experiment Identifiers Matrix
        SectionHeader(
            category = "EXPERIMENT IDENTIFIERS",
            subtitle = "Canonical records from Hexnil Phase 4, 5, and 6 engines."
        )

        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(12.dp))
                .border(1.dp, HexnilBorder, RoundedCornerShape(12.dp)),
            color = HexnilCard
        ) {
            Column(modifier = Modifier.padding(14.dp)) {
                ProvenanceRow("Comparison ID", analysis.comparisonId, isAccent = true)
                ProvenanceRow("Analysis ID", analysis.analysisId)
                ProvenanceRow("V0 Baseline Exp", analysis.v0ExperimentId)
                ProvenanceRow("V1 Candidate Exp", analysis.v1ExperimentId)
                ProvenanceRow("Device Serial", analysis.deviceSerial)
                ProvenanceRow("Target Device", analysis.deviceModel)
                ProvenanceRow("Statistical Policy", "Pairwise Significance (alpha = 0.05)")
                ProvenanceRow("Engineering Threshold", "5.0% meaningful shift")
                ProvenanceRow("Random Seed", "42 (Deterministic)")
                ProvenanceRow("Evidence State", analysis.evidenceState)
                ProvenanceRow("Record Timestamp", analysis.recordTimestamp)
            }
        }

        // APK Cryptographic Signatures
        SectionHeader(
            category = "APK CRYPTOGRAPHIC SIGNATURES",
            subtitle = "SHA-256 package fingerprints guaranteeing build integrity."
        )

        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(12.dp))
                .border(1.dp, HexnilBorder, RoundedCornerShape(12.dp)),
            color = HexnilCard
        ) {
            Column(modifier = Modifier.padding(14.dp)) {
                Text(text = "V0 BASELINE APK SHA-256", color = HexnilSecondaryText, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                Spacer(modifier = Modifier.height(2.dp))
                Text(
                    text = analysis.v0ApkSha256,
                    color = HexnilPrimaryText,
                    fontSize = 10.sp,
                    fontFamily = FontFamily.Monospace,
                    lineHeight = 14.sp
                )

                Spacer(modifier = Modifier.height(10.dp))

                Text(text = "V1 CANDIDATE APK SHA-256", color = HexnilSecondaryText, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                Spacer(modifier = Modifier.height(2.dp))
                Text(
                    text = analysis.v1ApkSha256,
                    color = HexnilAccentGlow,
                    fontSize = 10.sp,
                    fontFamily = FontFamily.Monospace,
                    lineHeight = 14.sp
                )

                Spacer(modifier = Modifier.height(10.dp))

                Text(text = "SYSTEM FINGERPRINT", color = HexnilSecondaryText, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                Spacer(modifier = Modifier.height(2.dp))
                Text(
                    text = analysis.buildFingerprint,
                    color = HexnilPrimaryText,
                    fontSize = 10.sp,
                    fontFamily = FontFamily.Monospace,
                    lineHeight = 14.sp
                )
            }
        }

        // Artifact Storage Trail
        SectionHeader(
            category = "PHYSICAL STORAGE PATHS",
            subtitle = "Raw telemetry records and statistical analysis JSON artifacts."
        )

        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(12.dp))
                .border(1.dp, HexnilBorder, RoundedCornerShape(12.dp)),
            color = HexnilCard
        ) {
            Column(modifier = Modifier.padding(14.dp)) {
                Text(
                    text = "data/experiments/comparisons/${analysis.comparisonId}/",
                    color = HexnilAccentGlow,
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(6.dp))
                Text(
                    text = "├── comparison.json\n├── metric_results.json\n├── quality.json\n└── statistical_analysis/\n    ├── analysis.json\n    └── comparison_summary.json",
                    color = HexnilSecondaryText,
                    fontSize = 10.sp,
                    fontFamily = FontFamily.Monospace,
                    lineHeight = 14.sp
                )
            }
        }

        Spacer(modifier = Modifier.height(16.dp))
    }
}

@Composable
private fun LineageStepNode(
    stepNumber: String,
    stepName: String,
    identifier: String,
    description: String,
    isLast: Boolean = false
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.Top
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Box(
                modifier = Modifier
                    .size(22.dp)
                    .background(HexnilSecondaryCard, CircleShape)
                    .border(1.dp, HexnilMainAccent, CircleShape),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = stepNumber,
                    color = HexnilMainAccent,
                    fontSize = 10.sp,
                    fontWeight = FontWeight.Bold
                )
            }
            if (!isLast) {
                Box(
                    modifier = Modifier
                        .width(1.dp)
                        .height(36.dp)
                        .background(HexnilBorder)
                )
            }
        }

        Spacer(modifier = Modifier.width(10.dp))

        Column {
            Text(text = stepName, color = HexnilSecondaryText, fontSize = 9.sp, fontWeight = FontWeight.Bold)
            Text(
                text = identifier,
                color = HexnilPrimaryText,
                fontSize = 11.sp,
                fontWeight = FontWeight.Bold,
                fontFamily = FontFamily.Monospace
            )
            Text(
                text = description,
                color = HexnilSecondaryText,
                fontSize = 10.sp,
                lineHeight = 13.sp
            )
        }
    }
}

@Composable
private fun ProvenanceRow(
    label: String,
    value: String,
    isAccent: Boolean = false
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 3.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(text = label, color = HexnilSecondaryText, fontSize = 11.sp)
        Text(
            text = value,
            color = if (isAccent) HexnilMainAccent else HexnilPrimaryText,
            fontSize = 11.sp,
            fontWeight = if (isAccent) FontWeight.Bold else FontWeight.Medium,
            fontFamily = FontFamily.Monospace
        )
    }
}
