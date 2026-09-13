package com.example.iqoo_hexnil.ui.components

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
import com.example.iqoo_hexnil.data.ReleaseClaim
import com.example.iqoo_hexnil.ui.theme.HexnilAccentGlow
import com.example.iqoo_hexnil.ui.theme.HexnilBorder
import com.example.iqoo_hexnil.ui.theme.HexnilCard
import com.example.iqoo_hexnil.ui.theme.HexnilMainAccent
import com.example.iqoo_hexnil.ui.theme.HexnilPrimaryText
import com.example.iqoo_hexnil.ui.theme.HexnilRadius
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryCard
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSpacing

@Composable
fun ClaimCard(
    claim: ReleaseClaim,
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
            // Top row: ID, Subsystem & Status Chips
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = claim.id,
                        color = HexnilMainAccent,
                        fontSize = 12.sp,
                        fontFamily = FontFamily.Monospace,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        text = " · ${claim.subsystem}",
                        color = HexnilSecondaryText,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Medium
                    )
                }

                Row(
                    horizontalArrangement = Arrangement.spacedBy(6.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    PriorityChip(priority = claim.priority)
                    RiskChip(riskLevel = claim.riskLevel)
                }
            }

            Spacer(modifier = Modifier.height(10.dp))

            // Claim Title & Validation Status
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = claim.title,
                    color = HexnilPrimaryText,
                    fontSize = 17.sp,
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.weight(1f).padding(end = 8.dp)
                )
                ValidationStatusChip(status = claim.validationStatus)
            }

            Spacer(modifier = Modifier.height(6.dp))

            // Claim Statement / Description
            Text(
                text = claim.description,
                color = HexnilSecondaryText,
                fontSize = 14.sp,
                lineHeight = 21.sp
            )

            Spacer(modifier = Modifier.height(14.dp))

            // Clean Metadata Details (Subtle background, no heavy nested border)
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(HexnilSecondaryCard, RoundedCornerShape(HexnilRadius.md))
                    .padding(horizontal = 14.dp, vertical = 10.dp),
                verticalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                ClaimPropertyRow("Affected Subsystem", claim.subsystem)
                ClaimPropertyRow("Expected Direction", claim.expectedDirection)
                ClaimPropertyRow("Expected Metric", claim.targetMetric, isMonospace = true)
                ClaimPropertyRow("Recommended Workload", claim.recommendedWorkload, isMonospace = true)
                ClaimPropertyRow("Validation Status", claim.validationStatus)
                ClaimPropertyRow("Evidence Availability", if (claim.validationStatus == "INCONCLUSIVE") "Inconclusive (Needs >3 runs)" else "Available (Direct telemetry)")
                ClaimPropertyRow("Provenance Source", claim.predictionSource)
            }
        }
    }
}

@Composable
private fun ClaimPropertyRow(
    label: String,
    value: String,
    isMonospace: Boolean = false
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 2.dp),
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
            color = if (isMonospace) HexnilAccentGlow else HexnilPrimaryText,
            fontSize = 12.sp,
            fontWeight = FontWeight.Medium,
            fontFamily = if (isMonospace) FontFamily.Monospace else FontFamily.Default
        )
    }
}

