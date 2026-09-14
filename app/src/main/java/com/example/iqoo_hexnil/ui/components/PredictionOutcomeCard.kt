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
import com.example.iqoo_hexnil.data.EvaluationHit
import com.example.iqoo_hexnil.data.PredictionOutcome
import com.example.iqoo_hexnil.ui.theme.HexnilBorder
import com.example.iqoo_hexnil.ui.theme.HexnilBorderSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilCard
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

@Composable
fun PredictionOutcomeCard(
    outcome: PredictionOutcome,
    modifier: Modifier = Modifier
) {
    val hitColor = when (outcome.hitType) {
        EvaluationHit.TRUE_POSITIVE -> HexnilFixed
        EvaluationHit.TRUE_NEGATIVE -> HexnilFixed
        EvaluationHit.FALSE_POSITIVE -> HexnilPreExisting
        EvaluationHit.FALSE_NEGATIVE -> HexnilError
    }

    val hitBg = when (outcome.hitType) {
        EvaluationHit.TRUE_POSITIVE -> HexnilFixedSubtle
        EvaluationHit.TRUE_NEGATIVE -> HexnilFixedSubtle
        EvaluationHit.FALSE_POSITIVE -> HexnilPreExistingSubtle
        EvaluationHit.FALSE_NEGATIVE -> HexnilErrorSubtle
    }

    Surface(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(HexnilRadius.card))
            .border(BorderStroke(1.dp, HexnilBorder), RoundedCornerShape(HexnilRadius.card)),
        color = HexnilCard
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            // Header: Claim ID + Hit Type Badge
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = outcome.claimId,
                    color = HexnilSecondaryText,
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace
                )

                Surface(
                    shape = RoundedCornerShape(HexnilRadius.badge),
                    color = hitBg,
                    border = BorderStroke(1.dp, hitColor.copy(alpha = 0.5f))
                ) {
                    Text(
                        text = outcome.hitType.label.uppercase(),
                        color = hitColor,
                        fontSize = 9.sp,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                    )
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            // Claim statement
            Text(
                text = "\"${outcome.claimText}\"",
                color = HexnilPrimaryText,
                fontSize = 13.sp,
                fontWeight = FontWeight.SemiBold
            )

            Spacer(modifier = Modifier.height(10.dp))

            // Side-by-side comparison: Predicted vs Actual
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                // Predicted Box
                Surface(
                    modifier = Modifier.weight(1f),
                    shape = RoundedCornerShape(HexnilRadius.xs),
                    color = HexnilSecondaryCard,
                    border = BorderStroke(1.dp, HexnilBorderSubtle)
                ) {
                    Column(modifier = Modifier.padding(8.dp)) {
                        Text(
                            text = "PREDICTED RISK",
                            color = HexnilSecondaryText,
                            fontSize = 9.sp,
                            fontWeight = FontWeight.Bold
                        )
                        Spacer(modifier = Modifier.height(2.dp))
                        Text(
                            text = outcome.predictedRisk.label.uppercase(),
                            color = HexnilPrimaryText,
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }

                // Actual Box
                Surface(
                    modifier = Modifier.weight(1f),
                    shape = RoundedCornerShape(HexnilRadius.xs),
                    color = HexnilSecondaryCard,
                    border = BorderStroke(1.dp, HexnilBorderSubtle)
                ) {
                    Column(modifier = Modifier.padding(8.dp)) {
                        Text(
                            text = "OBSERVED EVIDENCE",
                            color = HexnilSecondaryText,
                            fontSize = 9.sp,
                            fontWeight = FontWeight.Bold
                        )
                        Spacer(modifier = Modifier.height(2.dp))
                        Text(
                            text = outcome.actualVerdict.label,
                            color = hitColor,
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            // Evaluation Explanation
            Text(
                text = outcome.explanation,
                color = HexnilSecondaryText,
                fontSize = 11.sp,
                lineHeight = 15.sp
            )
        }
    }
}
