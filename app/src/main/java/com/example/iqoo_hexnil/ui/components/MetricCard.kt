package com.example.iqoo_hexnil.ui.components

import androidx.compose.foundation.background
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
import com.example.iqoo_hexnil.data.VerdictType
import com.example.iqoo_hexnil.ui.theme.HexnilAccentGlow
import com.example.iqoo_hexnil.ui.theme.HexnilBorder
import com.example.iqoo_hexnil.ui.theme.HexnilBorderSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilCard
import com.example.iqoo_hexnil.ui.theme.HexnilError
import com.example.iqoo_hexnil.ui.theme.HexnilMainAccent
import com.example.iqoo_hexnil.ui.theme.HexnilMutedText
import com.example.iqoo_hexnil.ui.theme.HexnilPrimaryText
import com.example.iqoo_hexnil.ui.theme.HexnilRadius
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryCard
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSpacing
import com.example.iqoo_hexnil.ui.theme.HexnilSuccess
import com.example.iqoo_hexnil.ui.theme.HexnilWarning

@Composable
fun MetricCard(
    metric: StatisticalMetricResult,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(HexnilRadius.card))
            .border(1.dp, HexnilBorderSubtle, RoundedCornerShape(HexnilRadius.card))
            .clickable { onClick() },
        color = HexnilCard
    ) {
        Column(modifier = Modifier.padding(HexnilSpacing.cardPadding)) {
            // Row 1: Metric Name + Verdict
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column(modifier = Modifier.weight(1f).padding(end = 8.dp)) {
                    Text(
                        text = metric.displayName,
                        color = HexnilPrimaryText,
                        fontSize = 16.sp,
                        fontWeight = FontWeight.Bold
                    )
                    Spacer(modifier = Modifier.height(2.dp))
                    Text(
                        text = metric.workloadId,
                        color = HexnilSecondaryText,
                        fontSize = 12.sp,
                        fontFamily = FontFamily.Monospace,
                        fontWeight = FontWeight.Medium
                    )
                }
                ResultBadge(verdict = metric.verdict, isCompact = false)
            }

            Spacer(modifier = Modifier.height(12.dp))

            // Values Row (Clean inline strip without nested border)
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(HexnilSecondaryCard, RoundedCornerShape(HexnilRadius.md))
                    .padding(horizontal = 14.dp, vertical = 10.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                // V0
                Column {
                    Text(
                        text = "V0 BASELINE",
                        color = HexnilSecondaryText,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 0.5.sp
                    )
                    Spacer(modifier = Modifier.height(2.dp))
                    Text(
                        text = if (metric.v0Mean != null) {
                            "${"%.1f".format(metric.v0Mean)} ${metric.unit}"
                        } else if (metric.v0Values.isNotEmpty()) {
                            "${"%.1f".format(metric.v0Values.first())} ${metric.unit}"
                        } else "—",
                        color = HexnilPrimaryText,
                        fontSize = 14.sp,
                        fontWeight = FontWeight.SemiBold,
                        fontFamily = FontFamily.Monospace
                    )
                }

                Text(
                    text = "➔",
                    color = HexnilSecondaryText,
                    fontSize = 14.sp
                )

                // V1
                Column {
                    Text(
                        text = "V1 CANDIDATE",
                        color = HexnilSecondaryText,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 0.5.sp
                    )
                    Spacer(modifier = Modifier.height(2.dp))
                    Text(
                        text = if (metric.v1Mean != null) {
                            "${"%.1f".format(metric.v1Mean)} ${metric.unit}"
                        } else if (metric.v1Values.isNotEmpty()) {
                            "${"%.1f".format(metric.v1Values.first())} ${metric.unit}"
                        } else "—",
                        color = HexnilPrimaryText,
                        fontSize = 14.sp,
                        fontWeight = FontWeight.SemiBold,
                        fontFamily = FontFamily.Monospace
                    )
                }

                // DELTA + PERCENTAGE
                Column(horizontalAlignment = Alignment.End) {
                    Text(
                        text = "DELTA",
                        color = HexnilSecondaryText,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 0.5.sp
                    )
                    Spacer(modifier = Modifier.height(2.dp))
                    val deltaText = if (metric.percentDelta != null) {
                        "${if (metric.percentDelta > 0) "+" else ""}${"%.2f".format(metric.percentDelta)}%"
                    } else if (metric.status == MetricStatus.UNSUPPORTED) {
                        "UNSUPPORTED"
                    } else "INSUFFICIENT"

                    val deltaColor = when (metric.verdict) {
                        VerdictType.REGRESSION -> HexnilError
                        VerdictType.IMPROVEMENT -> HexnilSuccess
                        VerdictType.UNCHANGED -> HexnilPrimaryText
                        VerdictType.INCONCLUSIVE -> HexnilWarning
                        else -> HexnilSecondaryText
                    }

                    Text(
                        text = deltaText,
                        color = deltaColor,
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }

            Spacer(modifier = Modifier.height(10.dp))

            // Evidence line & drilldown prompt
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = if (metric.pValue != null) {
                        "p=${"%.4f".format(metric.pValue)} · CI [${"%.1f".format(metric.ciLower ?: 0.0)}, ${"%.1f".format(metric.ciUpper ?: 0.0)}]"
                    } else if (metric.status == MetricStatus.UNSUPPORTED) {
                        "Restricted on device (Android 16)"
                    } else {
                        "Insufficient sample observations"
                    },
                    color = HexnilMutedText,
                    fontSize = 12.sp,
                    fontFamily = FontFamily.Monospace
                )

                Text(
                    text = "Details ➔",
                    color = HexnilAccentGlow,
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Bold
                )
            }
        }
    }
}
