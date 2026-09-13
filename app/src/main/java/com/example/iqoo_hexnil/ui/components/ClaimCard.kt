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
import com.example.iqoo_hexnil.data.ReleaseClaim
import com.example.iqoo_hexnil.ui.theme.HexnilAccentGlow
import com.example.iqoo_hexnil.ui.theme.HexnilBorder
import com.example.iqoo_hexnil.ui.theme.HexnilCard
import com.example.iqoo_hexnil.ui.theme.HexnilMainAccent
import com.example.iqoo_hexnil.ui.theme.HexnilPrimaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryCard
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText

@Composable
fun ClaimCard(
    claim: ReleaseClaim,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .border(1.dp, HexnilBorder, RoundedCornerShape(12.dp)),
        color = HexnilCard
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
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
                        fontSize = 11.sp,
                        fontFamily = FontFamily.Monospace,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        text = " · ${claim.subsystem}",
                        color = HexnilSecondaryText,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Medium
                    )
                }

                Row(
                    horizontalArrangement = Arrangement.spacedBy(4.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    PriorityChip(priority = claim.priority)
                    RiskChip(riskLevel = claim.riskLevel)
                }
            }

            Spacer(modifier = Modifier.height(6.dp))

            // Claim Title & Validation Status
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = claim.title,
                    color = HexnilPrimaryText,
                    fontSize = 15.sp,
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.weight(1f)
                )
                ValidationStatusChip(status = claim.validationStatus)
            }

            Spacer(modifier = Modifier.height(4.dp))

            // Claim Description
            Text(
                text = claim.description,
                color = HexnilSecondaryText,
                fontSize = 12.sp,
                lineHeight = 16.sp
            )

            Spacer(modifier = Modifier.height(10.dp))

            // Metadata Detail Table
            Surface(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(8.dp),
                color = HexnilSecondaryCard,
                border = androidx.compose.foundation.BorderStroke(1.dp, HexnilBorder)
            ) {
                Column(modifier = Modifier.padding(10.dp)) {
                    ClaimPropertyRow("Affected Subsystem", claim.subsystem)
                    ClaimPropertyRow("Expected Direction", claim.expectedDirection)
                    ClaimPropertyRow("Expected Metric", claim.targetMetric, isMonospace = true)
                    ClaimPropertyRow("Recommended Workload", claim.recommendedWorkload, isMonospace = true)
                    ClaimPropertyRow("Validation Status", claim.validationStatus)
                    ClaimPropertyRow("Provenance Source", claim.predictionSource)
                }
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
            fontSize = 11.sp
        )
        Text(
            text = value,
            color = if (isMonospace) HexnilAccentGlow else HexnilPrimaryText,
            fontSize = 11.sp,
            fontWeight = FontWeight.Medium,
            fontFamily = if (isMonospace) FontFamily.Monospace else FontFamily.Default
        )
    }
}
