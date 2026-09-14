package com.example.iqoo_hexnil.ui

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
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
import androidx.compose.foundation.shape.CircleShape
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
import com.example.iqoo_hexnil.ui.components.PreUpdateAnomalyCard
import com.example.iqoo_hexnil.ui.components.SectionHeader
import com.example.iqoo_hexnil.ui.theme.HexnilAccentGlow
import com.example.iqoo_hexnil.ui.theme.HexnilAccentSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilBackground
import com.example.iqoo_hexnil.ui.theme.HexnilBorder
import com.example.iqoo_hexnil.ui.theme.HexnilBorderSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilCard
import com.example.iqoo_hexnil.ui.theme.HexnilCyan
import com.example.iqoo_hexnil.ui.theme.HexnilFixed
import com.example.iqoo_hexnil.ui.theme.HexnilFixedSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilMainAccent
import com.example.iqoo_hexnil.ui.theme.HexnilPrimaryText
import com.example.iqoo_hexnil.ui.theme.HexnilRadius
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryCard
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSpacing

@Composable
fun V0BaselineScreen(
    onNavigateToClaims: () -> Unit,
    modifier: Modifier = Modifier
) {
    val scrollState = rememberScrollState()
    val preState = remember { HexnilRepository.getPreUpdateOsIdentity() }
    val anomalies = remember { HexnilRepository.getPreUpdateAnomalies() }
    val claims = remember { HexnilRepository.getReleaseClaims() }

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(HexnilBackground)
            .padding(horizontal = HexnilSpacing.screenHorizontal, vertical = HexnilSpacing.screenVertical)
            .verticalScroll(scrollState),
        verticalArrangement = Arrangement.spacedBy(HexnilSpacing.sectionSpacing)
    ) {
        // 1. Immutable V0 Lock Header
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(HexnilRadius.hero))
                .border(BorderStroke(1.5.dp, HexnilFixed), RoundedCornerShape(HexnilRadius.hero)),
            color = HexnilCard
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(text = "🔒", fontSize = 14.sp)
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(
                            text = "PRE-UPDATE BASELINE (V0)",
                            color = HexnilFixed,
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Bold,
                            letterSpacing = 1.sp
                        )
                    }

                    Surface(
                        shape = RoundedCornerShape(HexnilRadius.badge),
                        color = HexnilFixedSubtle,
                        border = BorderStroke(1.dp, HexnilFixed.copy(alpha = 0.5f))
                    ) {
                        Text(
                            text = "V0 IMMUTABLE LOCK",
                            color = HexnilFixed,
                            fontSize = 9.sp,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                        )
                    }
                }

                Spacer(modifier = Modifier.height(10.dp))

                Text(
                    text = "${preState.manufacturer} ${preState.model} • Android ${preState.androidVersion}",
                    color = HexnilPrimaryText,
                    fontSize = 15.sp,
                    fontWeight = FontWeight.Bold
                )

                Spacer(modifier = Modifier.height(4.dp))

                Text(
                    text = "Build ID: ${preState.buildId}",
                    color = HexnilSecondaryText,
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace
                )
                Text(
                    text = "Security Patch: ${preState.securityPatchLevel} • Boot Count: ${preState.bootCount}",
                    color = HexnilCyan,
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace
                )
                Text(
                    text = "Fingerprint: ${preState.buildFingerprint.take(45)}...",
                    color = HexnilSecondaryText,
                    fontSize = 10.sp,
                    fontFamily = FontFamily.Monospace
                )
            }
        }

        // 2. Behavioral Baseline Measurements
        SectionHeader(
            title = "BEHAVIORAL BASELINE SIGNALS",
            actionLabel = "6 Subsystems",
            onActionClick = {}
        )

        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(HexnilRadius.card))
                .border(BorderStroke(1.dp, HexnilBorder), RoundedCornerShape(HexnilRadius.card)),
            color = HexnilCard
        ) {
            Column(modifier = Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                SignalRow("Standby Power Consumption", "12.4 mAh/hr", "Idle discharge slope")
                SignalRow("Ambient SoC Thermal", "32.0°C baseline", "Thermal equilibrium")
                SignalRow("Background Memory RSS", "148 MB resident", "Heap baseline")
                SignalRow("Cold App Launch Latency", "312.0 ms (±48ms)", "Preliminary jitter noted")
                SignalRow("CPU Thread Utilization", "1.8% average", "Core governor baseline")
                SignalRow("SurfaceFlinger Frame Jitter", "Restricted in sysfs", "Android 16 OEM node")
            }
        }

        // 3. Pre-existing Anomalies in V0
        SectionHeader(
            title = "PRE-EXISTING ANOMALIES",
            actionLabel = "${anomalies.size} Recorded",
            onActionClick = {}
        )

        anomalies.forEach { anomaly ->
            PreUpdateAnomalyCard(anomaly = anomaly)
        }

        // 4. Pre-Update Risk Forecast Preview
        SectionHeader(
            title = "ML PRE-UPDATE RISK FORECAST",
            actionLabel = "View Claims (${claims.size})",
            onActionClick = onNavigateToClaims
        )

        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(HexnilRadius.card))
                .border(BorderStroke(1.dp, HexnilBorderSubtle), RoundedCornerShape(HexnilRadius.card)),
            color = HexnilSecondaryCard
        ) {
            Column(modifier = Modifier.padding(14.dp)) {
                Text(
                    text = "CHANGELOG RISK BANDS",
                    color = HexnilMainAccent,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = "Claims extracted from OEM release notes are evaluated for prospective subsystem risk before the OS update is applied.",
                    color = HexnilSecondaryText,
                    fontSize = 11.sp,
                    lineHeight = 15.sp
                )
            }
        }
    }
}

@Composable
private fun SignalRow(label: String, value: String, note: String) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(text = label, color = HexnilPrimaryText, fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
            Text(text = note, color = HexnilSecondaryText, fontSize = 10.sp)
        }
        Text(text = value, color = HexnilCyan, fontSize = 11.sp, fontFamily = FontFamily.Monospace, fontWeight = FontWeight.Bold)
    }
}
