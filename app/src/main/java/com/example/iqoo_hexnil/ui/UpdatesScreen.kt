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
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.iqoo_hexnil.data.HexnilRepository
import com.example.iqoo_hexnil.ui.components.HistoricalUpdateCard
import com.example.iqoo_hexnil.ui.components.SectionHeader
import com.example.iqoo_hexnil.ui.components.UpdateTransitionHero
import com.example.iqoo_hexnil.ui.theme.HexnilAccentGlow
import com.example.iqoo_hexnil.ui.theme.HexnilAccentSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilBackground
import com.example.iqoo_hexnil.ui.theme.HexnilBorder
import com.example.iqoo_hexnil.ui.theme.HexnilBorderSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilCard
import com.example.iqoo_hexnil.ui.theme.HexnilCyan
import com.example.iqoo_hexnil.ui.theme.HexnilFixed
import com.example.iqoo_hexnil.ui.theme.HexnilMainAccent
import com.example.iqoo_hexnil.ui.theme.HexnilPrimaryText
import com.example.iqoo_hexnil.ui.theme.HexnilRadius
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryCard
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSpacing

@Composable
fun UpdatesScreen(
    onNavigateToComparison: () -> Unit,
    onNavigateToAwaitingUpdate: () -> Unit,
    onNavigateToUpdateDetected: () -> Unit,
    modifier: Modifier = Modifier
) {
    val scrollState = rememberScrollState()
    val transition = remember { HexnilRepository.getUpdateTransition() }
    val history = remember { HexnilRepository.getHistoricalUpdates() }
    val osIdentity = remember { HexnilRepository.getDeviceOsIdentity() }

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(HexnilBackground)
            .padding(horizontal = HexnilSpacing.screenHorizontal, vertical = HexnilSpacing.screenVertical)
            .verticalScroll(scrollState),
        verticalArrangement = Arrangement.spacedBy(HexnilSpacing.sectionSpacing)
    ) {
        // 1. Current OS Installed State Banner
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(HexnilRadius.hero))
                .border(BorderStroke(1.dp, HexnilBorder), RoundedCornerShape(HexnilRadius.hero)),
            color = HexnilCard
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "CURRENT SYSTEM SOFTWARE",
                        color = HexnilSecondaryText,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 1.sp
                    )
                    Surface(
                        shape = RoundedCornerShape(HexnilRadius.badge),
                        color = HexnilAccentSubtle,
                        border = BorderStroke(1.dp, HexnilMainAccent.copy(alpha = 0.5f))
                    ) {
                        Text(
                            text = "LIVE OS",
                            color = HexnilAccentGlow,
                            fontSize = 9.sp,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                        )
                    }
                }

                Spacer(modifier = Modifier.height(8.dp))

                Text(
                    text = "Android ${osIdentity.androidVersion} (Build ${osIdentity.buildId})",
                    color = HexnilPrimaryText,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Bold
                )

                Spacer(modifier = Modifier.height(4.dp))

                Text(
                    text = "Security Patch Level: ${osIdentity.securityPatchLevel} • Kernel: ${osIdentity.kernelVersion}",
                    color = HexnilCyan,
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace
                )
            }
        }

        // 2. Latest OS Update Transition Hero
        SectionHeader(
            title = "LATEST DETECTED TRANSITION",
            actionLabel = "Compare V0 vs V1",
            onActionClick = onNavigateToComparison
        )

        UpdateTransitionHero(
            transition = transition,
            onClick = onNavigateToComparison
        )

        // 3. Update Verification Rules & State Shortcuts
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(HexnilRadius.card))
                .border(BorderStroke(1.dp, HexnilBorderSubtle), RoundedCornerShape(HexnilRadius.card)),
            color = HexnilSecondaryCard
        ) {
            Column(modifier = Modifier.padding(14.dp)) {
                Text(
                    text = "UPDATE VERIFICATION PRINCIPLE",
                    color = HexnilMainAccent,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = "Hexnil enforces strict scientific causality: without a genuine Android OS, firmware, or security patch bump verified via getprop and sys.boot_completed, V1 is never manufactured.",
                    color = HexnilSecondaryText,
                    fontSize = 11.sp,
                    lineHeight = 16.sp
                )

                Spacer(modifier = Modifier.height(10.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Surface(
                        modifier = Modifier
                            .weight(1f)
                            .clip(RoundedCornerShape(HexnilRadius.xs))
                            .border(BorderStroke(1.dp, HexnilBorder), RoundedCornerShape(HexnilRadius.xs))
                            .clickable { onNavigateToAwaitingUpdate() },
                        color = HexnilCard
                    ) {
                        Text(
                            text = "Awaiting State View",
                            color = HexnilPrimaryText,
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.padding(8.dp)
                        )
                    }

                    Surface(
                        modifier = Modifier
                            .weight(1f)
                            .clip(RoundedCornerShape(HexnilRadius.xs))
                            .border(BorderStroke(1.dp, HexnilBorder), RoundedCornerShape(HexnilRadius.xs))
                            .clickable { onNavigateToUpdateDetected() },
                        color = HexnilCard
                    ) {
                        Text(
                            text = "Detection Event View",
                            color = HexnilPrimaryText,
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.padding(8.dp)
                        )
                    }
                }
            }
        }

        // 4. Lifetime Device Update Memory / Historical Updates
        SectionHeader(
            title = "DEVICE UPDATE HISTORY (MEMORY)",
            actionLabel = "${history.size} Past Updates",
            onActionClick = {}
        )

        history.forEach { record ->
            HistoricalUpdateCard(record = record)
        }
    }
}
