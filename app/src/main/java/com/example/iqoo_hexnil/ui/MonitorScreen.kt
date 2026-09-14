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
import com.example.iqoo_hexnil.data.DeviceHardwareInfo
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
import com.example.iqoo_hexnil.ui.theme.HexnilPreExisting
import com.example.iqoo_hexnil.ui.theme.HexnilPreExistingSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilPrimaryText
import com.example.iqoo_hexnil.ui.theme.HexnilRadius
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryCard
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSpacing
import com.example.iqoo_hexnil.ui.theme.HexnilSuccess

@Composable
fun MonitorScreen(
    device: DeviceHardwareInfo,
    onNavigateToBaseline: () -> Unit,
    modifier: Modifier = Modifier
) {
    val scrollState = rememberScrollState()
    val anomalies = remember { HexnilRepository.getPreUpdateAnomalies() }
    val osIdentity = remember { HexnilRepository.getDeviceOsIdentity() }

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(HexnilBackground)
            .padding(horizontal = HexnilSpacing.screenHorizontal, vertical = HexnilSpacing.screenVertical)
            .verticalScroll(scrollState),
        verticalArrangement = Arrangement.spacedBy(HexnilSpacing.sectionSpacing)
    ) {
        // 1. Continuous Observation Active Card
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(HexnilRadius.hero))
                .border(BorderStroke(1.5.dp, HexnilFixed.copy(alpha = 0.8f)), RoundedCornerShape(HexnilRadius.hero)),
            color = HexnilCard
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Box(
                            modifier = Modifier
                                .size(10.dp)
                                .background(HexnilFixed, CircleShape)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = "MONITORING: ACTIVE",
                            color = HexnilFixed,
                            fontSize = 13.sp,
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
                            text = "POLLING INTERVAL: 10s",
                            color = HexnilFixed,
                            fontSize = 9.sp,
                            fontFamily = FontFamily.Monospace,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                        )
                    }
                }

                Spacer(modifier = Modifier.height(10.dp))

                Text(
                    text = "${osIdentity.model} • Android ${osIdentity.androidVersion} (SDK ${osIdentity.sdkInt})",
                    color = HexnilPrimaryText,
                    fontSize = 15.sp,
                    fontWeight = FontWeight.Bold
                )

                Spacer(modifier = Modifier.height(4.dp))

                Text(
                    text = "Build: ${osIdentity.buildId} • Patch: ${osIdentity.securityPatchLevel}",
                    color = HexnilSecondaryText,
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace
                )

                Spacer(modifier = Modifier.height(12.dp))

                // Monitoring Metrics Row
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    MetricCounterBox("SAMPLES", "1,420", HexnilPrimaryText, Modifier.weight(1f))
                    MetricCounterBox("DURATION", "4h 15m", HexnilCyan, Modifier.weight(1f))
                    MetricCounterBox("LAST CHECK", "Just now", HexnilSuccess, Modifier.weight(1f))
                    MetricCounterBox("ANOMALIES", "${anomalies.size}", if (anomalies.isNotEmpty()) HexnilPreExisting else HexnilSecondaryText, Modifier.weight(1f))
                }
            }
        }

        // 2. Behavioral Baseline Health Indicators
        SectionHeader(
            title = "BEHAVIORAL BASELINE HEALTH",
            actionLabel = "V0 Baseline Detail",
            onActionClick = onNavigateToBaseline
        )

        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(HexnilRadius.card))
                .border(BorderStroke(1.dp, HexnilBorder), RoundedCornerShape(HexnilRadius.card)),
            color = HexnilCard
        ) {
            Column(modifier = Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                HealthStatusRow(label = "Battery Standby Drain", status = "NORMAL", color = HexnilFixed)
                HealthStatusRow(label = "Idle Device Thermal", status = "WATCH (38.5°C)", color = HexnilPreExisting)
                HealthStatusRow(label = "Background CPU Utilization", status = "NORMAL (<2.5%)", color = HexnilFixed)
                HealthStatusRow(label = "Memory Heap Allocation", status = "NORMAL", color = HexnilFixed)
                HealthStatusRow(label = "Cold Startup Latency", status = "ANOMALY (CV > 15%)", color = HexnilPreExisting)
                HealthStatusRow(label = "UI Rendering (120Hz Pacing)", status = "NORMAL", color = HexnilFixed)
            }
        }

        // 3. Pre-Update Anomalies Section (Clearly demarcated as PRE-EXISTING)
        SectionHeader(
            title = "PRE-UPDATE ANOMALIES (V0)",
            actionLabel = "${anomalies.size} Detected",
            onActionClick = {}
        )

        anomalies.forEach { anomaly ->
            PreUpdateAnomalyCard(anomaly = anomaly)
        }

        // 4. Fundamental distinction note
        Surface(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(HexnilRadius.sm),
            color = HexnilPreExistingSubtle,
            border = BorderStroke(1.dp, HexnilPreExisting.copy(alpha = 0.4f))
        ) {
            Row(modifier = Modifier.padding(12.dp), verticalAlignment = Alignment.Top) {
                Text(text = "🛡️", fontSize = 14.sp)
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = "Hexnil Rule: Pre-existing anomalies detected during V0 baseline observation are NEVER blamed on the post-update OS. They are isolated as PRE-EXISTING ISSUES.",
                    color = HexnilPreExisting,
                    fontSize = 11.sp,
                    lineHeight = 16.sp
                )
            }
        }
    }
}

@Composable
private fun MetricCounterBox(
    label: String,
    value: String,
    color: androidx.compose.ui.graphics.Color,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(HexnilRadius.xs),
        color = HexnilSecondaryCard,
        border = BorderStroke(1.dp, HexnilBorderSubtle)
    ) {
        Column(
            modifier = Modifier.padding(vertical = 8.dp, horizontal = 4.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = value,
                color = color,
                fontSize = 12.sp,
                fontWeight = FontWeight.Bold,
                fontFamily = FontFamily.Monospace,
                maxLines = 1
            )
            Spacer(modifier = Modifier.height(2.dp))
            Text(
                text = label,
                color = HexnilSecondaryText,
                fontSize = 8.sp,
                maxLines = 1
            )
        }
    }
}

@Composable
private fun HealthStatusRow(
    label: String,
    status: String,
    color: androidx.compose.ui.graphics.Color
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = label,
            color = HexnilPrimaryText,
            fontSize = 13.sp
        )

        Surface(
            shape = RoundedCornerShape(4.dp),
            color = color.copy(alpha = 0.15f),
            border = BorderStroke(1.dp, color.copy(alpha = 0.5f))
        ) {
            Text(
                text = status,
                color = color,
                fontSize = 10.sp,
                fontWeight = FontWeight.Bold,
                fontFamily = FontFamily.Monospace,
                modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
            )
        }
    }
}
