package com.example.iqoo_hexnil.ui.components

import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
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
import com.example.iqoo_hexnil.data.MetricStatus
import com.example.iqoo_hexnil.data.StatisticalMetricResult
import com.example.iqoo_hexnil.ui.theme.HexnilBorder
import com.example.iqoo_hexnil.ui.theme.HexnilCard
import com.example.iqoo_hexnil.ui.theme.HexnilMainAccent
import com.example.iqoo_hexnil.ui.theme.HexnilPrimaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryCard
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText

@Composable
fun MetricCard(
    metric: StatisticalMetricResult,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .border(1.dp, HexnilBorder, RoundedCornerShape(12.dp))
            .clickable { onClick() },
        color = HexnilCard
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            // Header: Workload & Verdict Badge
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
                    fontWeight = FontWeight.Medium
                )
                ResultBadge(verdict = metric.verdict, isCompact = true)
            }

            Spacer(modifier = Modifier.height(4.dp))

            // Metric Display Name
            Text(
                text = metric.displayName,
                color = HexnilPrimaryText,
                fontSize = 14.sp,
                fontWeight = FontWeight.Bold
            )

            Spacer(modifier = Modifier.height(10.dp))

            // Values Box: V0 vs V1
            Surface(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(8.dp),
                color = HexnilSecondaryCard,
                border = androidx.compose.foundation.BorderStroke(1.dp, HexnilBorder)
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 10.dp, vertical = 8.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column {
                        Text(
                            text = "V0 BASELINE",
                            color = HexnilSecondaryText,
                            fontSize = 9.sp,
                            fontWeight = FontWeight.Bold
                        )
                        Text(
                            text = if (metric.v0Mean != null) {
                                "${"%.1f".format(metric.v0Mean)} ${metric.unit}"
                            } else if (metric.v0Values.isNotEmpty()) {
                                "${"%.1f".format(metric.v0Values.first())} ${metric.unit}"
                            } else "N/A",
                            color = HexnilPrimaryText,
                            fontSize = 12.sp,
                            fontWeight = FontWeight.SemiBold,
                            fontFamily = FontFamily.Monospace
                        )
                    }

                    Text(
                        text = "➔",
                        color = HexnilSecondaryText,
                        fontSize = 13.sp
                    )

                    Column {
                        Text(
                            text = "V1 CANDIDATE",
                            color = HexnilSecondaryText,
                            fontSize = 9.sp,
                            fontWeight = FontWeight.Bold
                        )
                        Text(
                            text = if (metric.v1Mean != null) {
                                "${"%.1f".format(metric.v1Mean)} ${metric.unit}"
                            } else if (metric.v1Values.isNotEmpty()) {
                                "${"%.1f".format(metric.v1Values.first())} ${metric.unit}"
                            } else "N/A",
                            color = HexnilPrimaryText,
                            fontSize = 12.sp,
                            fontWeight = FontWeight.SemiBold,
                            fontFamily = FontFamily.Monospace
                        )
                    }

                    Column(horizontalAlignment = Alignment.End) {
                        Text(
                            text = "DELTA",
                            color = HexnilSecondaryText,
                            fontSize = 9.sp,
                            fontWeight = FontWeight.Bold
                        )
                        Text(
                            text = if (metric.percentDelta != null) {
                                "${if (metric.percentDelta > 0) "+" else ""}${"%.1f".format(metric.percentDelta)}%"
                            } else if (metric.status == MetricStatus.UNSUPPORTED) {
                                "UNSUPPORTED"
                            } else "INSUFFICIENT",
                            color = HexnilMainAccent,
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Bold,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            // Footer info & tap CTA
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = if (metric.pValue != null) {
                        "p=${"%.4f".format(metric.pValue)} · d=${"%.2f".format(metric.effectSize ?: 0.0)}"
                    } else if (metric.status == MetricStatus.UNSUPPORTED) {
                        "Hardware Capability Unsupported"
                    } else {
                        "Sample count n=${metric.sampleCount} (< 3 required)"
                    },
                    color = HexnilSecondaryText,
                    fontSize = 10.sp,
                    fontFamily = FontFamily.Monospace
                )

                Text(
                    text = "Evidence ➔",
                    color = HexnilMainAccent,
                    fontSize = 10.sp,
                    fontWeight = FontWeight.Bold
                )
            }
        }
    }
}
