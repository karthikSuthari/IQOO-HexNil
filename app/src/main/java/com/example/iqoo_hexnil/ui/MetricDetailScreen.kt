package com.example.iqoo_hexnil.ui

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.iqoo_hexnil.data.StatisticalMetricResult
import com.example.iqoo_hexnil.data.VerdictType
import com.example.iqoo_hexnil.ui.components.ResultBadge
import com.example.iqoo_hexnil.ui.components.SectionHeader
import com.example.iqoo_hexnil.ui.theme.HexnilAccentGlow
import com.example.iqoo_hexnil.ui.theme.HexnilBackground
import com.example.iqoo_hexnil.ui.theme.HexnilBorder
import com.example.iqoo_hexnil.ui.theme.HexnilCard
import com.example.iqoo_hexnil.ui.theme.HexnilError
import com.example.iqoo_hexnil.ui.theme.HexnilMainAccent
import com.example.iqoo_hexnil.ui.theme.HexnilPrimaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryCard
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSuccess
import com.example.iqoo_hexnil.ui.theme.HexnilWarning

@Composable
fun MetricDetailScreen(
    metric: StatisticalMetricResult,
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
        // Main Metric Verdict Header Card
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
                        text = metric.workloadId,
                        color = HexnilSecondaryText,
                        fontSize = 11.sp,
                        fontFamily = FontFamily.Monospace,
                        fontWeight = FontWeight.Bold
                    )
                    ResultBadge(verdict = metric.verdict)
                }

                Spacer(modifier = Modifier.height(6.dp))

                Text(
                    text = metric.displayName,
                    color = HexnilPrimaryText,
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Bold
                )

                Text(
                    text = "ID: ${metric.metricName} · Unit: ${metric.unit}",
                    color = HexnilSecondaryText,
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace
                )

                Spacer(modifier = Modifier.height(12.dp))

                // Verdict Reasoning Card
                Surface(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(8.dp),
                    color = HexnilSecondaryCard,
                    border = BorderStroke(1.dp, HexnilBorder)
                ) {
                    Column(modifier = Modifier.padding(12.dp)) {
                        Text(
                            text = "STATISTICAL VERDICT REASONING",
                            color = HexnilMainAccent,
                            fontSize = 10.sp,
                            fontWeight = FontWeight.Bold,
                            letterSpacing = 1.sp
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = metric.reason,
                            color = HexnilPrimaryText,
                            fontSize = 12.sp,
                            lineHeight = 16.sp
                        )
                    }
                }
            }
        }

        // Visual Comparison Representation (Proportional Magnitude Visualization)
        if (metric.v0Mean != null && metric.v1Mean != null && metric.v0Mean > 0 && metric.v1Mean > 0) {
            MetricComparisonVisualizer(
                v0Value = metric.v0Mean,
                v1Value = metric.v1Mean,
                unit = metric.unit,
                percentDelta = metric.percentDelta,
                verdict = metric.verdict
            )
        }

        // Statistical Summary Matrix
        SectionHeader(
            category = "STATISTICAL HYPOTHESIS TESTING",
            subtitle = "Rigorous paired differential analysis parameters and threshold gates."
        )

        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(12.dp))
                .border(1.dp, HexnilBorder, RoundedCornerShape(12.dp)),
            color = HexnilCard
        ) {
            Column(modifier = Modifier.padding(14.dp)) {
                MetricDetailRow("Metric Key", metric.key, isMonospace = true)
                MetricDetailRow("V0 Baseline Mean", if (metric.v0Mean != null) "${"%.3f".format(metric.v0Mean)} ${metric.unit}" else "N/A")
                MetricDetailRow("V1 Candidate Mean", if (metric.v1Mean != null) "${"%.3f".format(metric.v1Mean)} ${metric.unit}" else "N/A")
                MetricDetailRow("Absolute Shift Delta", if (metric.absoluteDelta != null) "${if (metric.absoluteDelta > 0) "+" else ""}${"%.3f".format(metric.absoluteDelta)} ${metric.unit}" else "N/A", isAccent = true)
                MetricDetailRow("Percentage Shift Delta", if (metric.percentDelta != null) "${if (metric.percentDelta > 0) "+" else ""}${"%.2f".format(metric.percentDelta)}%" else "N/A", isAccent = true)
                MetricDetailRow("Sample Iterations (n)", "${metric.sampleCount} paired runs")
                MetricDetailRow("Hypothesis Test", "Paired Student's t-test (two-sided)")
                MetricDetailRow("p-value", if (metric.pValue != null) "p = ${"%.5f".format(metric.pValue)} ${if (metric.pValue < 0.05) "(Significant)" else "(Not Significant)"}" else "N/A")
                MetricDetailRow("95% Confidence Interval", if (metric.ciLower != null && metric.ciUpper != null) "[${"%.3f".format(metric.ciLower)}, ${"%.3f".format(metric.ciUpper)}]" else "N/A")
                MetricDetailRow("Standardized Effect Size", if (metric.effectSize != null) "d_z = ${"%.3f".format(metric.effectSize)} (${metric.effectSizeMethod})" else "N/A")
                MetricDetailRow("Engineering Threshold", "${metric.thresholdPercent ?: 5.0}% meaningful delta")
                MetricDetailRow("Authoritative Verdict", metric.verdict.label)
                MetricDetailRow("Optimization Direction", metric.direction)
                MetricDetailRow("Evidence Comparison ID", metric.comparisonId, isMonospace = true)
            }
        }

        // Raw Run Observations Audit
        SectionHeader(
            category = "RAW RUN MEASUREMENTS AUDIT",
            subtitle = "Observations collected across deterministic paired physical runs."
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
                    text = "V0 Raw Measurements (${metric.v0Values.size} runs)",
                    color = HexnilSecondaryText,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = if (metric.v0Values.isNotEmpty()) metric.v0Values.joinToString(", ") { "${"%.3f".format(it)} ${metric.unit}" } else "No observations",
                    color = HexnilPrimaryText,
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace
                )

                Spacer(modifier = Modifier.height(10.dp))

                Text(
                    text = "V1 Raw Measurements (${metric.v1Values.size} runs)",
                    color = HexnilSecondaryText,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = if (metric.v1Values.isNotEmpty()) metric.v1Values.joinToString(", ") { "${"%.3f".format(it)} ${metric.unit}" } else "No observations",
                    color = HexnilPrimaryText,
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace
                )

                if (metric.pairedDifferences.isNotEmpty()) {
                    Spacer(modifier = Modifier.height(10.dp))
                    Text(
                        text = "Paired Differences (V1 - V0)",
                        color = HexnilSecondaryText,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = metric.pairedDifferences.joinToString(", ") { "${if (it > 0) "+" else ""}${"%.3f".format(it)}" },
                        color = HexnilAccentGlow,
                        fontSize = 11.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }

                Spacer(modifier = Modifier.height(12.dp))

                // Provenance Run Identifiers
                Text(
                    text = "MATCHED RUN LINEAGE",
                    color = HexnilSecondaryText,
                    fontSize = 10.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(4.dp))
                metric.v0RunIds.forEachIndexed { index, runId ->
                    val v1RunId = metric.v1RunIds.getOrNull(index) ?: ""
                    Text(
                        text = "Pair #${index + 1}: $runId ➔ $v1RunId",
                        color = HexnilSecondaryText,
                        fontSize = 9.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }
        }

        Spacer(modifier = Modifier.height(16.dp))
    }
}

@Composable
private fun MetricComparisonVisualizer(
    v0Value: Double,
    v1Value: Double,
    unit: String,
    percentDelta: Double?,
    verdict: VerdictType
) {
    val maxVal = maxOf(v0Value, v1Value) * 1.05
    val v0Ratio = (v0Value / maxVal).toFloat().coerceIn(0.05f, 1f)
    val v1Ratio = (v1Value / maxVal).toFloat().coerceIn(0.05f, 1f)

    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .border(1.dp, HexnilBorder, RoundedCornerShape(12.dp)),
        color = HexnilCard
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Text(
                text = "VISUAL COMPARISON (PROPORTIONAL BARS)",
                color = HexnilMainAccent,
                fontSize = 10.sp,
                fontWeight = FontWeight.Bold,
                letterSpacing = 1.sp
            )

            Spacer(modifier = Modifier.height(12.dp))

            // V0 Baseline Bar
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "V0",
                    color = HexnilSecondaryText,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.width(32.dp)
                )
                Box(
                    modifier = Modifier
                        .weight(1f)
                        .height(18.dp)
                        .clip(RoundedCornerShape(4.dp))
                        .background(HexnilSecondaryCard)
                ) {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth(v0Ratio)
                            .fillMaxHeight()
                            .background(HexnilBorder)
                    )
                }
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = "${"%.1f".format(v0Value)} $unit",
                    color = HexnilPrimaryText,
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace,
                    modifier = Modifier.width(75.dp)
                )
            }

            Spacer(modifier = Modifier.height(8.dp))

            // V1 Candidate Bar
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "V1",
                    color = HexnilAccentGlow,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.width(32.dp)
                )
                Box(
                    modifier = Modifier
                        .weight(1f)
                        .height(18.dp)
                        .clip(RoundedCornerShape(4.dp))
                        .background(HexnilSecondaryCard)
                ) {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth(v1Ratio)
                            .fillMaxHeight()
                            .background(if (verdict == VerdictType.REGRESSION) HexnilError else HexnilSuccess)
                    )
                }
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = "${"%.1f".format(v1Value)} $unit",
                    color = HexnilPrimaryText,
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace,
                    modifier = Modifier.width(75.dp)
                )
            }
        }
    }
}

@Composable
private fun MetricDetailRow(
    label: String,
    value: String,
    isAccent: Boolean = false,
    isMonospace: Boolean = false
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = label,
            color = HexnilSecondaryText,
            fontSize = 11.sp
        )
        Text(
            text = value,
            color = if (isAccent) HexnilMainAccent else HexnilPrimaryText,
            fontSize = 11.sp,
            fontWeight = if (isAccent) FontWeight.Bold else FontWeight.Medium,
            fontFamily = if (isMonospace) FontFamily.Monospace else FontFamily.Default
        )
    }
}
