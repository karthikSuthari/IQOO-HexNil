package com.example.iqoo_hexnil.ui

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.iqoo_hexnil.data.ClaimRiskLevel
import com.example.iqoo_hexnil.data.ReleaseClaim
import com.example.iqoo_hexnil.ui.components.ClaimCard
import com.example.iqoo_hexnil.ui.components.EmptyState
import com.example.iqoo_hexnil.ui.theme.HexnilAccentGlow
import com.example.iqoo_hexnil.ui.theme.HexnilAccentSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilBackground
import com.example.iqoo_hexnil.ui.theme.HexnilBorder
import com.example.iqoo_hexnil.ui.theme.HexnilCard
import com.example.iqoo_hexnil.ui.theme.HexnilMainAccent
import com.example.iqoo_hexnil.ui.theme.HexnilPrimaryText
import com.example.iqoo_hexnil.ui.theme.HexnilRadius
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryCard
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSpacing
import com.example.iqoo_hexnil.ui.theme.HexnilSuccess
import com.example.iqoo_hexnil.ui.theme.HexnilWarning

enum class ClaimFilterCategory(val label: String) {
    ALL("ALL"),
    HIGH_RISK("HIGH RISK"),
    MEDIUM_RISK("MEDIUM RISK"),
    UNCHANGED("UNCHANGED"),
    INCONCLUSIVE("INCONCLUSIVE")
}

@Composable
fun ClaimsScreen(
    claims: List<ReleaseClaim>,
    modifier: Modifier = Modifier
) {
    val scrollState = rememberScrollState()
    val filterScrollState = rememberScrollState()
    var selectedFilter by remember { mutableStateOf(ClaimFilterCategory.ALL) }

    val filteredClaims = when (selectedFilter) {
        ClaimFilterCategory.ALL -> claims
        ClaimFilterCategory.HIGH_RISK -> claims.filter { it.riskLevel == ClaimRiskLevel.HIGH }
        ClaimFilterCategory.MEDIUM_RISK -> claims.filter { it.riskLevel == ClaimRiskLevel.MODERATE }
        ClaimFilterCategory.UNCHANGED -> claims.filter { it.validationStatus.equals("UNCHANGED", ignoreCase = true) }
        ClaimFilterCategory.INCONCLUSIVE -> claims.filter { it.validationStatus.equals("INCONCLUSIVE", ignoreCase = true) }
    }

    val highRiskCount = claims.count { it.riskLevel == ClaimRiskLevel.HIGH }
    val medRiskCount = claims.count { it.riskLevel == ClaimRiskLevel.MODERATE }
    val unchangedCount = claims.count { it.validationStatus.equals("UNCHANGED", ignoreCase = true) }
    val inconclusiveCount = claims.count { it.validationStatus.equals("INCONCLUSIVE", ignoreCase = true) }

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(HexnilBackground)
            .padding(horizontal = HexnilSpacing.md, vertical = HexnilSpacing.sm)
            .verticalScroll(scrollState),
        verticalArrangement = Arrangement.spacedBy(HexnilSpacing.md)
    ) {
        // Claim Intelligence Header Card
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(HexnilRadius.card))
                .border(1.dp, HexnilBorder, RoundedCornerShape(HexnilRadius.card)),
            color = HexnilCard
        ) {
            Column(modifier = Modifier.padding(HexnilSpacing.md)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "RELEASE CLAIM INTELLIGENCE (PHASE 7)",
                        color = HexnilMainAccent,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 1.sp
                    )
                    Surface(
                        shape = RoundedCornerShape(4.dp),
                        color = HexnilSecondaryCard,
                        border = BorderStroke(1.dp, HexnilBorder)
                    ) {
                        Text(
                            text = "${claims.size} CLAIMS AUDITED",
                            color = HexnilAccentGlow,
                            fontSize = 9.sp,
                            fontWeight = FontWeight.Bold,
                            fontFamily = FontFamily.Monospace,
                            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                        )
                    }
                }

                Spacer(modifier = Modifier.height(HexnilSpacing.xs))
                Text(
                    text = "OEM Hypotheses vs Measured Validation",
                    color = HexnilPrimaryText,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = "Release claims extracted from changelogs, commits, and OEM telemetry map directly to deterministic benchmark workloads with explicit risk ratings and measured validation outcomes.",
                    color = HexnilSecondaryText,
                    fontSize = 11.sp,
                    lineHeight = 15.sp
                )
            }
        }

        // Section 8 Filter Chips Row (ALL, HIGH RISK, MEDIUM RISK, UNCHANGED, INCONCLUSIVE)
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .horizontalScroll(filterScrollState),
            horizontalArrangement = Arrangement.spacedBy(HexnilSpacing.xs)
        ) {
            ClaimFilterChip(
                label = "ALL (${claims.size})",
                isSelected = selectedFilter == ClaimFilterCategory.ALL,
                color = HexnilMainAccent,
                onClick = { selectedFilter = ClaimFilterCategory.ALL }
            )
            ClaimFilterChip(
                label = "HIGH RISK ($highRiskCount)",
                isSelected = selectedFilter == ClaimFilterCategory.HIGH_RISK,
                color = HexnilMainAccent,
                onClick = { selectedFilter = ClaimFilterCategory.HIGH_RISK }
            )
            ClaimFilterChip(
                label = "MEDIUM RISK ($medRiskCount)",
                isSelected = selectedFilter == ClaimFilterCategory.MEDIUM_RISK,
                color = HexnilWarning,
                onClick = { selectedFilter = ClaimFilterCategory.MEDIUM_RISK }
            )
            ClaimFilterChip(
                label = "UNCHANGED ($unchangedCount)",
                isSelected = selectedFilter == ClaimFilterCategory.UNCHANGED,
                color = HexnilSuccess,
                onClick = { selectedFilter = ClaimFilterCategory.UNCHANGED }
            )
            ClaimFilterChip(
                label = "INCONCLUSIVE ($inconclusiveCount)",
                isSelected = selectedFilter == ClaimFilterCategory.INCONCLUSIVE,
                color = HexnilWarning,
                onClick = { selectedFilter = ClaimFilterCategory.INCONCLUSIVE }
            )
        }

        // Claims List or Meaningful Empty State
        if (filteredClaims.isEmpty()) {
            EmptyState(
                title = "No Claims Match Filter",
                message = "Zero release claims match the selected filter category '${selectedFilter.label}'."
            )
        } else {
            Column(verticalArrangement = Arrangement.spacedBy(HexnilSpacing.sm)) {
                filteredClaims.forEach { claim ->
                    ClaimCard(claim = claim)
                }
            }
        }

        Spacer(modifier = Modifier.height(HexnilSpacing.xs))
    }
}

@Composable
private fun ClaimFilterChip(
    label: String,
    isSelected: Boolean,
    color: Color,
    onClick: () -> Unit
) {
    val bgColor = if (isSelected) HexnilAccentSubtle else HexnilSecondaryCard
    val borderColor = if (isSelected) color else HexnilBorder

    Surface(
        modifier = Modifier.clickable { onClick() },
        shape = RoundedCornerShape(HexnilRadius.metadata),
        color = bgColor,
        border = BorderStroke(1.dp, borderColor)
    ) {
        Text(
            text = label,
            color = if (isSelected) color else HexnilSecondaryText,
            fontSize = 11.sp,
            fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Medium,
            modifier = Modifier.padding(vertical = 6.dp, horizontal = 10.dp),
            maxLines = 1
        )
    }
}
