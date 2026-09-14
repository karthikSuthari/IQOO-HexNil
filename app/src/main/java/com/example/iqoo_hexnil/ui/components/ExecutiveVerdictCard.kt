package com.example.iqoo_hexnil.ui.components

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
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
import com.example.iqoo_hexnil.data.ExecutiveVerdict
import com.example.iqoo_hexnil.ui.theme.HexnilBorder
import com.example.iqoo_hexnil.ui.theme.HexnilCard
import com.example.iqoo_hexnil.ui.theme.HexnilCyan
import com.example.iqoo_hexnil.ui.theme.HexnilError
import com.example.iqoo_hexnil.ui.theme.HexnilErrorSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilFixed
import com.example.iqoo_hexnil.ui.theme.HexnilFixedSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilPreExisting
import com.example.iqoo_hexnil.ui.theme.HexnilPreExistingSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilPrimaryText
import com.example.iqoo_hexnil.ui.theme.HexnilRadius
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryCard
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText
import com.example.iqoo_hexnil.ui.theme.HexnilWarning
import com.example.iqoo_hexnil.ui.theme.HexnilWarningSubtle

@Composable
fun ExecutiveVerdictCard(
    verdict: ExecutiveVerdict,
    evidenceCoverage: String,
    regressionsCount: Int,
    improvementsCount: Int,
    persistedCount: Int,
    unchangedCount: Int,
    inconclusiveCount: Int,
    modifier: Modifier = Modifier
) {
    val verdictColor = when (verdict) {
        ExecutiveVerdict.SAFE_TO_ROLLOUT -> HexnilFixed
        ExecutiveVerdict.UPDATE_HAS_REGRESSIONS -> HexnilWarning
        ExecutiveVerdict.CRITICAL_REGRESSIONS -> HexnilError
        ExecutiveVerdict.INCONCLUSIVE -> HexnilWarning
    }

    val verdictBg = when (verdict) {
        ExecutiveVerdict.SAFE_TO_ROLLOUT -> HexnilFixedSubtle
        ExecutiveVerdict.UPDATE_HAS_REGRESSIONS -> HexnilWarningSubtle
        ExecutiveVerdict.CRITICAL_REGRESSIONS -> HexnilErrorSubtle
        ExecutiveVerdict.INCONCLUSIVE -> HexnilWarningSubtle
    }

    Surface(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(HexnilRadius.hero))
            .border(BorderStroke(1.5.dp, verdictColor), RoundedCornerShape(HexnilRadius.hero)),
        color = HexnilCard
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            // Header: Title & Coverage
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "EXECUTIVE ROLLOUT VERDICT",
                    color = HexnilSecondaryText,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp
                )

                Surface(
                    shape = RoundedCornerShape(HexnilRadius.badge),
                    color = HexnilSecondaryCard,
                    border = BorderStroke(1.dp, HexnilBorder)
                ) {
                    Text(
                        text = "COVERAGE: $evidenceCoverage",
                        color = HexnilCyan,
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace,
                        modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                    )
                }
            }

            Spacer(modifier = Modifier.height(10.dp))

            // Large Verdict Banner
            Surface(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(HexnilRadius.md),
                color = verdictBg,
                border = BorderStroke(1.dp, verdictColor.copy(alpha = 0.5f))
            ) {
                Column(modifier = Modifier.padding(12.dp)) {
                    Text(
                        text = verdict.label,
                        color = verdictColor,
                        fontSize = 18.sp,
                        fontWeight = FontWeight.Black,
                        letterSpacing = 0.5.sp
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = verdict.summary,
                        color = HexnilPrimaryText,
                        fontSize = 12.sp,
                        lineHeight = 17.sp
                    )
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            // Breakdown Chips
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                VerdictCountPill(label = "Regressions", count = regressionsCount, color = if (regressionsCount > 0) HexnilError else HexnilSecondaryText, modifier = Modifier.weight(1f))
                VerdictCountPill(label = "Pre-Existing", count = persistedCount, color = if (persistedCount > 0) HexnilPreExisting else HexnilSecondaryText, modifier = Modifier.weight(1f))
                VerdictCountPill(label = "Improvements", count = improvementsCount, color = if (improvementsCount > 0) HexnilFixed else HexnilSecondaryText, modifier = Modifier.weight(1f))
                VerdictCountPill(label = "Stable", count = unchangedCount, color = HexnilPrimaryText, modifier = Modifier.weight(1f))
            }
        }
    }
}

@Composable
private fun VerdictCountPill(
    label: String,
    count: Int,
    color: androidx.compose.ui.graphics.Color,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(HexnilRadius.xs),
        color = HexnilSecondaryCard,
        border = BorderStroke(1.dp, HexnilBorder)
    ) {
        Column(
            modifier = Modifier.padding(vertical = 6.dp, horizontal = 4.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = "$count",
                color = color,
                fontSize = 14.sp,
                fontWeight = FontWeight.Bold,
                fontFamily = FontFamily.Monospace
            )
            Spacer(modifier = Modifier.height(2.dp))
            Text(
                text = label,
                color = HexnilSecondaryText,
                fontSize = 9.sp,
                maxLines = 1
            )
        }
    }
}
