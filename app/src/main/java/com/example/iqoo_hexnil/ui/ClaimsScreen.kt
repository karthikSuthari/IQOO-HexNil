package com.example.iqoo_hexnil.ui

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
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
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryCard
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSuccess
import com.example.iqoo_hexnil.ui.theme.HexnilWarning

@Composable
fun ClaimsScreen(
    claims: List<ReleaseClaim>,
    modifier: Modifier = Modifier
) {
    val scrollState = rememberScrollState()
    var selectedFilter by remember { mutableStateOf<String?>(null) }

    val filteredClaims = if (selectedFilter != null) {
        claims.filter { it.validationStatus.equals(selectedFilter, ignoreCase = true) }
    } else {
        claims
    }

    val unchangedCount = claims.count { it.validationStatus.equals("UNCHANGED", ignoreCase = true) }
    val inconclusiveCount = claims.count { it.validationStatus.equals("INCONCLUSIVE", ignoreCase = true) }

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(HexnilBackground)
            .padding(horizontal = 16.dp, vertical = 12.dp)
            .verticalScroll(scrollState),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        // Claim Intelligence Header Card
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(12.dp))
                .border(1.dp, HexnilBorder, RoundedCornerShape(12.dp)),
            color = HexnilCard
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
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

                Spacer(modifier = Modifier.height(6.dp))
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
                    fontSize = 12.sp,
                    lineHeight = 16.sp
                )
            }
        }

        // Status Filter Chips Row
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(6.dp)
        ) {
            ClaimFilterChip(
                label = "ALL (${claims.size})",
                isSelected = selectedFilter == null,
                color = HexnilMainAccent,
                onClick = { selectedFilter = null },
                modifier = Modifier.weight(1f)
            )
            ClaimFilterChip(
                label = "UNCHANGED ($unchangedCount)",
                isSelected = selectedFilter.equals("UNCHANGED", ignoreCase = true),
                color = HexnilSuccess,
                onClick = { selectedFilter = "UNCHANGED" },
                modifier = Modifier.weight(1f)
            )
            ClaimFilterChip(
                label = "INCONCL. ($inconclusiveCount)",
                isSelected = selectedFilter.equals("INCONCLUSIVE", ignoreCase = true),
                color = HexnilWarning,
                onClick = { selectedFilter = "INCONCLUSIVE" },
                modifier = Modifier.weight(1f)
            )
        }

        if (filteredClaims.isEmpty()) {
            EmptyState(
                title = "No Claims Matched Filter",
                message = "Select 'ALL' to inspect all 5 release claims."
            )
        } else {
            // List of Vertical Claim Cards
            filteredClaims.forEach { claim ->
                ClaimCard(claim = claim)
            }
        }

        Spacer(modifier = Modifier.height(16.dp))
    }
}

@Composable
private fun ClaimFilterChip(
    label: String,
    isSelected: Boolean,
    color: Color,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val bgColor = if (isSelected) HexnilAccentSubtle else HexnilSecondaryCard
    val borderColor = if (isSelected) color else HexnilBorder

    Surface(
        modifier = modifier.clickable { onClick() },
        shape = RoundedCornerShape(6.dp),
        color = bgColor,
        border = BorderStroke(1.dp, borderColor)
    ) {
        Text(
            text = label,
            color = if (isSelected) color else HexnilSecondaryText,
            fontSize = 10.sp,
            fontWeight = if (isSelected) FontWeight.Bold else FontWeight.SemiBold,
            modifier = Modifier.padding(vertical = 8.dp, horizontal = 4.dp),
            maxLines = 1
        )
    }
}
