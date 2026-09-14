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
import com.example.iqoo_hexnil.data.HistoricalUpdateRecord
import com.example.iqoo_hexnil.ui.theme.HexnilBorder
import com.example.iqoo_hexnil.ui.theme.HexnilBorderSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilCard
import com.example.iqoo_hexnil.ui.theme.HexnilCyan
import com.example.iqoo_hexnil.ui.theme.HexnilError
import com.example.iqoo_hexnil.ui.theme.HexnilFixed
import com.example.iqoo_hexnil.ui.theme.HexnilFixedSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilPrimaryText
import com.example.iqoo_hexnil.ui.theme.HexnilRadius
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryCard
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText
import com.example.iqoo_hexnil.ui.theme.HexnilWarning
import com.example.iqoo_hexnil.ui.theme.HexnilWarningSubtle

@Composable
fun HistoricalUpdateCard(
    record: HistoricalUpdateRecord,
    modifier: Modifier = Modifier
) {
    val verdictColor = when (record.verdict) {
        ExecutiveVerdict.SAFE_TO_ROLLOUT -> HexnilFixed
        ExecutiveVerdict.UPDATE_HAS_REGRESSIONS -> HexnilWarning
        ExecutiveVerdict.CRITICAL_REGRESSIONS -> HexnilError
        ExecutiveVerdict.INCONCLUSIVE -> HexnilWarning
    }

    val verdictBg = when (record.verdict) {
        ExecutiveVerdict.SAFE_TO_ROLLOUT -> HexnilFixedSubtle
        ExecutiveVerdict.UPDATE_HAS_REGRESSIONS -> HexnilWarningSubtle
        ExecutiveVerdict.CRITICAL_REGRESSIONS -> HexnilError.copy(alpha = 0.15f)
        ExecutiveVerdict.INCONCLUSIVE -> HexnilWarningSubtle
    }

    Surface(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(HexnilRadius.card))
            .border(BorderStroke(1.dp, HexnilBorder), RoundedCornerShape(HexnilRadius.card)),
        color = HexnilCard
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            // Header: Update ID & Transition Type
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = record.updateId,
                    color = HexnilSecondaryText,
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace
                )

                Surface(
                    shape = RoundedCornerShape(HexnilRadius.badge),
                    color = HexnilSecondaryCard,
                    border = BorderStroke(1.dp, HexnilBorderSubtle)
                ) {
                    Text(
                        text = record.transitionType.label,
                        color = HexnilCyan,
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                    )
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            // Build transition: From -> To
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = record.fromBuild,
                    color = HexnilSecondaryText,
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace,
                    modifier = Modifier.weight(1f)
                )
                Text(text = " ➔ ", color = HexnilSecondaryText, fontSize = 12.sp)
                Text(
                    text = record.toBuild,
                    color = HexnilPrimaryText,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace,
                    modifier = Modifier.weight(1f)
                )
            }

            Spacer(modifier = Modifier.height(10.dp))

            // Footer: Verdict & Stats Summary
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Surface(
                    shape = RoundedCornerShape(HexnilRadius.badge),
                    color = verdictBg,
                    border = BorderStroke(1.dp, verdictColor.copy(alpha = 0.5f))
                ) {
                    Text(
                        text = record.verdict.label,
                        color = verdictColor,
                        fontSize = 9.sp,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                    )
                }

                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = "Reg: ${record.regressionsCount} • Imp: ${record.improvementsCount} • Res: ${record.resolvedCount}",
                        color = HexnilSecondaryText,
                        fontSize = 10.sp,
                        fontFamily = FontFamily.Monospace
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        text = record.patchDate,
                        color = HexnilCyan,
                        fontSize = 10.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }
        }
    }
}
