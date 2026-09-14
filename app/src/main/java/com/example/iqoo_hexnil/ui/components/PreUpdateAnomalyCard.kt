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
import com.example.iqoo_hexnil.data.PreUpdateAnomaly
import com.example.iqoo_hexnil.data.SeverityLevel
import com.example.iqoo_hexnil.ui.theme.HexnilBorder
import com.example.iqoo_hexnil.ui.theme.HexnilBorderSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilCard
import com.example.iqoo_hexnil.ui.theme.HexnilError
import com.example.iqoo_hexnil.ui.theme.HexnilErrorSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilPreExisting
import com.example.iqoo_hexnil.ui.theme.HexnilPreExistingSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilPrimaryText
import com.example.iqoo_hexnil.ui.theme.HexnilRadius
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText

@Composable
fun PreUpdateAnomalyCard(
    anomaly: PreUpdateAnomaly,
    modifier: Modifier = Modifier
) {
    val severityColor = when (anomaly.severity) {
        SeverityLevel.CRITICAL, SeverityLevel.HIGH -> HexnilError
        SeverityLevel.MEDIUM -> HexnilPreExisting
        SeverityLevel.LOW -> HexnilSecondaryText
        SeverityLevel.NONE -> HexnilSecondaryText
    }

    val severityBg = when (anomaly.severity) {
        SeverityLevel.CRITICAL, SeverityLevel.HIGH -> HexnilErrorSubtle
        SeverityLevel.MEDIUM -> HexnilPreExistingSubtle
        else -> HexnilBorderSubtle
    }

    Surface(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(HexnilRadius.card))
            .border(BorderStroke(1.dp, HexnilBorder), RoundedCornerShape(HexnilRadius.card)),
        color = HexnilCard
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            // Header: Anomaly Tag + Severity Badge
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(text = "⚠️", fontSize = 12.sp)
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        text = "PRE-EXISTING ANOMALY (V0)",
                        color = HexnilPreExisting,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 0.5.sp
                    )
                }

                Surface(
                    shape = RoundedCornerShape(HexnilRadius.badge),
                    color = severityBg,
                    border = BorderStroke(1.dp, severityColor.copy(alpha = 0.6f))
                ) {
                    Text(
                        text = "${anomaly.severity.name} SEVERITY",
                        color = severityColor,
                        fontSize = 9.sp,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                    )
                }
            }

            Spacer(modifier = Modifier.height(6.dp))

            // Anomaly Type & Description
            Text(
                text = anomaly.anomalyType.label,
                color = HexnilPrimaryText,
                fontSize = 14.sp,
                fontWeight = FontWeight.Bold
            )

            Spacer(modifier = Modifier.height(4.dp))

            Text(
                text = anomaly.description,
                color = HexnilSecondaryText,
                fontSize = 12.sp,
                lineHeight = 16.sp
            )

            Spacer(modifier = Modifier.height(8.dp))

            // Z-score & Metric Context
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Metric: ${anomaly.metricName}",
                    color = HexnilSecondaryText,
                    fontSize = 10.sp,
                    fontFamily = FontFamily.Monospace
                )
                Text(
                    text = "Z-Score: ${anomaly.observedZScore}σ",
                    color = severityColor,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace
                )
            }
        }
    }
}
