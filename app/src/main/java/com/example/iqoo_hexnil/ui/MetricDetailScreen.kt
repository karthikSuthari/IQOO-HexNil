package com.example.iqoo_hexnil.ui

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
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
import com.example.iqoo_hexnil.data.StatisticalMetricResult
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
                    text = "Identifier: ${metric.metricName} (${metric.unit})",
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

        // Statistical Summary Matrix
        SectionHeader(
            category = "STATISTICAL PARAMETERS",
            subtitle = "Rigorous hypothesis testing results and effect size estimates."
        )

        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(12.dp))
                .border(1.dp, HexnilBorder, RoundedCornerShape(12.dp)),
            color = HexnilCard
        ) {
            Column(modifier = Modifier.padding(14.dp)) {
                MetricDetailRow("V0 Mean Baseline", if (metric.v0Mean != null) "${"%.2f".format(metric.v0Mean)} ${metric.unit}" else "N/A")
                MetricDetailRow("V1 Mean Candidate", if (metric.v1Mean != null) "${"%.2f".format(metric.v1Mean)} ${metric.unit}" else "N/A")
                MetricDetailRow("Absolute Shift Delta", if (metric.absoluteDelta != null) "${if (metric.absoluteDelta > 0) "+" else ""}${"%.2f".format(metric.absoluteDelta)} ${metric.unit}" else "N/A", isAccent = true)
                MetricDetailRow("Percentage Shift Delta", if (metric.percentDelta != null) "${if (metric.percentDelta > 0) "+" else ""}${"%.2f".format(metric.percentDelta)}%" else "N/A", isAccent = true)
                MetricDetailRow("95% Confidence Interval", if (metric.ciLower != null && metric.ciUpper != null) "[${"%.2f".format(metric.ciLower)}, ${"%.2f".format(metric.ciUpper)}]" else "N/A")
                MetricDetailRow("Paired t-test p-value", if (metric.pValue != null) "p = ${"%.5f".format(metric.pValue)}" else "N/A")
                MetricDetailRow("Standardized Effect Size", if (metric.effectSize != null) "d_z = ${"%.2f".format(metric.effectSize)} (${metric.effectSizeMethod})" else "N/A")
                MetricDetailRow("Engineering Threshold", "${metric.thresholdPercent ?: 5.0}% meaningful change")
                MetricDetailRow("Optimization Direction", metric.direction)
            }
        }

        // Raw Run Observations Audit
        SectionHeader(
            category = "RAW RUN MEASUREMENTS AUDIT",
            subtitle = "Observations collected across deterministic paired iterations."
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
                    text = if (metric.v0Values.isNotEmpty()) metric.v0Values.joinToString(", ") { "${"%.2f".format(it)} ${metric.unit}" } else "No observations",
                    color = HexnilPrimaryText,
                    fontSize = 12.sp,
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
                    text = if (metric.v1Values.isNotEmpty()) metric.v1Values.joinToString(", ") { "${"%.2f".format(it)} ${metric.unit}" } else "No observations",
                    color = HexnilPrimaryText,
                    fontSize = 12.sp,
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
                        text = metric.pairedDifferences.joinToString(", ") { "${if (it > 0) "+" else ""}${"%.2f".format(it)}" },
                        color = HexnilAccentGlow,
                        fontSize = 12.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }

                Spacer(modifier = Modifier.height(12.dp))

                // Provenance Run IDs
                Text(
                    text = "PROVENANCE RUN IDENTIFIERS",
                    color = HexnilSecondaryText,
                    fontSize = 10.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(4.dp))
                metric.v0RunIds.forEachIndexed { index, runId ->
                    val v1RunId = metric.v1RunIds.getOrNull(index) ?: ""
                    Text(
                        text = "Pair #${index + 1}: $runId vs $v1RunId",
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
private fun MetricDetailRow(
    label: String,
    value: String,
    isAccent: Boolean = false
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
            fontSize = 12.sp
        )
        Text(
            text = value,
            color = if (isAccent) HexnilMainAccent else HexnilPrimaryText,
            fontSize = 12.sp,
            fontWeight = if (isAccent) FontWeight.Bold else FontWeight.Medium,
            fontFamily = FontFamily.Monospace
        )
    }
}
