package com.example.iqoo_hexnil.ui.components

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.LinearProgressIndicator
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
import com.example.iqoo_hexnil.data.ComparisonAnalysis
import com.example.iqoo_hexnil.ui.theme.HexnilAccentGlow
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
import com.example.iqoo_hexnil.ui.theme.HexnilWarning

@Composable
fun EvidenceCoverageCard(
    analysis: ComparisonAnalysis,
    modifier: Modifier = Modifier
) {
    val coverageFraction = if (analysis.metricsAnalyzed > 0) {
        analysis.metricsEligible.toFloat() / analysis.metricsAnalyzed.toFloat()
    } else 0f

    Surface(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(HexnilRadius.hero))
            .border(1.dp, HexnilBorder, RoundedCornerShape(HexnilRadius.hero)),
        color = HexnilCard
    ) {
        Column(modifier = Modifier.padding(HexnilSpacing.cardPadding)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "UPDATE VALIDATION EVIDENCE",
                    color = HexnilMainAccent,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp
                )
                Text(
                    text = analysis.comparisonId,
                    color = HexnilAccentGlow,
                    fontSize = 12.sp,
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Bold
                )
            }

            Spacer(modifier = Modifier.height(12.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.Bottom
            ) {
                Column {
                    Text(
                        text = "Evidence Coverage",
                        color = HexnilSecondaryText,
                        fontSize = 13.sp
                    )
                    Spacer(modifier = Modifier.height(2.dp))
                    Text(
                        text = "${analysis.metricsEligible} / ${analysis.metricsAnalyzed} Metrics",
                        color = HexnilPrimaryText,
                        fontSize = 22.sp,
                        fontWeight = FontWeight.Bold
                    )
                }

                Text(
                    text = "${(coverageFraction * 100).toInt()}% Confirmed",
                    color = HexnilSuccess,
                    fontSize = 14.sp,
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

            Spacer(modifier = Modifier.height(14.dp))

            // Verdict breakdown badges
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                CoverageVerdictBadge(
                    label = "UNCHANGED",
                    count = analysis.metricsUnchanged,
                    color = HexnilSuccess,
                    modifier = Modifier.weight(1f)
                )
                CoverageVerdictBadge(
                    label = "INCONCLUSIVE",
                    count = analysis.metricsInconclusive,
                    color = HexnilWarning,
                    modifier = Modifier.weight(1f)
                )
                CoverageVerdictBadge(
                    label = "REGRESSION",
                    count = analysis.metricsRegressions,
                    color = if (analysis.metricsRegressions > 0) HexnilError else HexnilSecondaryText,
                    modifier = Modifier.weight(1f)
                )
            }

            Spacer(modifier = Modifier.height(12.dp))
            Text(
                text = "No statistically and engineering-significant regression detected in measured evidence.",
                color = HexnilSecondaryText,
                fontSize = 13.sp,
                lineHeight = 19.sp
            )
        }
    }
}

@Composable
fun CoverageVerdictBadge(
    label: String,
    count: Int,
    color: Color,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier
            .clip(RoundedCornerShape(HexnilRadius.md))
            .border(1.dp, HexnilBorder, RoundedCornerShape(HexnilRadius.md)),
        color = HexnilSecondaryCard
    ) {
        Column(
            modifier = Modifier.padding(vertical = 10.dp, horizontal = 6.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = "$count",
                color = color,
                fontSize = 16.sp,
                fontWeight = FontWeight.Bold,
                fontFamily = FontFamily.Monospace
            )
            Spacer(modifier = Modifier.height(2.dp))
            Text(
                text = label,
                color = HexnilSecondaryText,
                fontSize = 11.sp,
                fontWeight = FontWeight.Bold,
                letterSpacing = 0.5.sp,
                maxLines = 1
            )
        }
    }
}

