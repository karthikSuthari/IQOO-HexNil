package com.example.iqoo_hexnil.ui.components

import androidx.compose.foundation.border
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
import com.example.iqoo_hexnil.data.StatisticalMetricResult
import com.example.iqoo_hexnil.ui.theme.HexnilAccentGlow
import com.example.iqoo_hexnil.ui.theme.HexnilBorder
import com.example.iqoo_hexnil.ui.theme.HexnilCard
import com.example.iqoo_hexnil.ui.theme.HexnilMainAccent
import com.example.iqoo_hexnil.ui.theme.HexnilPrimaryText
import com.example.iqoo_hexnil.ui.theme.HexnilRadius
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryCard
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSpacing
import com.example.iqoo_hexnil.ui.theme.HexnilSuccess

@Composable
fun ComparisonCard(
    metric: StatisticalMetricResult,
    v0ExpId: String,
    v1ExpId: String,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(HexnilRadius.card))
            .border(1.dp, HexnilBorder, RoundedCornerShape(HexnilRadius.card)),
        color = HexnilCard
    ) {
        Column(modifier = Modifier.padding(HexnilSpacing.cardPadding)) {
            // Header
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column(modifier = Modifier.weight(1f).padding(end = 8.dp)) {
                    Text(
                        text = metric.workloadId,
                        color = HexnilSecondaryText,
                        fontSize = 12.sp,
                        fontFamily = FontFamily.Monospace
                    )
                    Spacer(modifier = Modifier.height(2.dp))
                    Text(
                        text = metric.displayName,
                        color = HexnilPrimaryText,
                        fontSize = 17.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
                ResultBadge(verdict = metric.verdict, isCompact = false)
            }

            Spacer(modifier = Modifier.height(14.dp))

            // Matched Experiment Comparison Block (No nested borders)
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                // V0 Column
                Surface(
                    modifier = Modifier.weight(1f),
                    shape = RoundedCornerShape(HexnilRadius.md),
                    color = HexnilSecondaryCard
                ) {
                    Column(modifier = Modifier.padding(12.dp)) {
                        Text(
                            text = "V0 BASELINE",
                            color = HexnilSecondaryText,
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold
                        )
                        Spacer(modifier = Modifier.height(2.dp))
                        Text(
                            text = v0ExpId,
                            color = HexnilAccentGlow,
                            fontSize = 11.sp,
                            fontFamily = FontFamily.Monospace
                        )
                        Spacer(modifier = Modifier.height(6.dp))
                        Text(
                            text = if (metric.v0Mean != null) "${"%.1f".format(metric.v0Mean)} ${metric.unit}" else "N/A",
                            color = HexnilPrimaryText,
                            fontSize = 16.sp,
                            fontWeight = FontWeight.Bold,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                }

                // V1 Column
                Surface(
                    modifier = Modifier.weight(1f),
                    shape = RoundedCornerShape(HexnilRadius.md),
                    color = HexnilSecondaryCard
                ) {
                    Column(modifier = Modifier.padding(12.dp)) {
                        Text(
                            text = "V1 CANDIDATE",
                            color = HexnilSecondaryText,
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold
                        )
                        Spacer(modifier = Modifier.height(2.dp))
                        Text(
                            text = v1ExpId,
                            color = HexnilAccentGlow,
                            fontSize = 11.sp,
                            fontFamily = FontFamily.Monospace
                        )
                        Spacer(modifier = Modifier.height(6.dp))
                        Text(
                            text = if (metric.v1Mean != null) "${"%.1f".format(metric.v1Mean)} ${metric.unit}" else "N/A",
                            color = HexnilPrimaryText,
                            fontSize = 16.sp,
                            fontWeight = FontWeight.Bold,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(14.dp))

            // Statistical summary row
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Delta: ${if (metric.percentDelta != null) "${if (metric.percentDelta > 0) "+" else ""}${"%.1f".format(metric.percentDelta)}%" else "N/A"}",
                    color = HexnilMainAccent,
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace
                )

                if (metric.ciLower != null && metric.ciUpper != null) {
                    Text(
                        text = "95% CI: [${"%.1f".format(metric.ciLower)}, ${"%.1f".format(metric.ciUpper)}]",
                        color = HexnilSecondaryText,
                        fontSize = 12.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }
        }
    }
}

