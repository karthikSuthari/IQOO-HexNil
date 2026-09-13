package com.example.iqoo_hexnil.ui

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
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.iqoo_hexnil.data.DeviceHardwareInfo
import com.example.iqoo_hexnil.telemetry.CapabilityStatus
import com.example.iqoo_hexnil.telemetry.TelemetryRecord
import com.example.iqoo_hexnil.ui.components.BuildIdentityCard
import com.example.iqoo_hexnil.ui.components.DeviceCard
import com.example.iqoo_hexnil.ui.components.HexnilPrimaryButton
import com.example.iqoo_hexnil.ui.components.SectionHeader
import com.example.iqoo_hexnil.ui.theme.HexnilBackground
import com.example.iqoo_hexnil.ui.theme.HexnilBorder
import com.example.iqoo_hexnil.ui.theme.HexnilCard
import com.example.iqoo_hexnil.ui.theme.HexnilError
import com.example.iqoo_hexnil.ui.theme.HexnilMainAccent
import com.example.iqoo_hexnil.ui.theme.HexnilPrimaryText
import com.example.iqoo_hexnil.ui.theme.HexnilRadius
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryCard
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSpacing
import com.example.iqoo_hexnil.ui.theme.HexnilSuccess
import com.example.iqoo_hexnil.ui.theme.HexnilWarning

@Composable
fun DeviceScreen(
    device: DeviceHardwareInfo,
    records: List<TelemetryRecord>,
    isRunning: Boolean,
    onCollectSnapshot: () -> Unit,
    modifier: Modifier = Modifier
) {
    val scrollState = rememberScrollState()

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(HexnilBackground)
            .padding(horizontal = HexnilSpacing.md, vertical = HexnilSpacing.sm)
            .verticalScroll(scrollState),
        verticalArrangement = Arrangement.spacedBy(HexnilSpacing.sm)
    ) {
        // Target Hardware State Card
        DeviceCard(device = device)

        // Capability Matrix Taxonomy Card
        CapabilityTaxonomyCard(
            universalCount = device.universalMetricsCount,
            conditionalCount = device.conditionalMetricsCount,
            unsupportedCount = device.unsupportedMetricsCount
        )

        // Live Telemetry Capture Signals
        SectionHeader(
            category = "LIVE PHYSICAL TELEMETRY SIGNALS",
            subtitle = "Direct capture from Android battery, memory, and thermal subsystems."
        )

        LiveTelemetrySignalsCard(records = records)

        // Snapshot Action Button
        HexnilPrimaryButton(
            text = if (isRunning) "Capturing Telemetry Snapshot..." else "Capture Live Telemetry Snapshot ➔",
            onClick = onCollectSnapshot,
            enabled = !isRunning
        )

        // System Fingerprint Card
        BuildIdentityCard(device = device)

        Spacer(modifier = Modifier.height(16.dp))
    }
}

@Composable
private fun CapabilityTaxonomyCard(
    universalCount: Int,
    conditionalCount: Int,
    unsupportedCount: Int
) {
    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(HexnilRadius.card))
            .border(1.dp, HexnilBorder, RoundedCornerShape(HexnilRadius.card)),
        color = HexnilCard
    ) {
        Column(modifier = Modifier.padding(HexnilSpacing.md)) {
            Text(
                text = "CAPABILITY-AWARE TAXONOMY (PHASE 2)",
                color = HexnilMainAccent,
                fontSize = 11.sp,
                fontWeight = FontWeight.Bold,
                letterSpacing = 1.sp
            )
            Spacer(modifier = Modifier.height(6.dp))
            Text(
                text = "Subsystems strictly distinguish universal OS APIs from conditional device sensors without data fabrication.",
                color = HexnilSecondaryText,
                fontSize = 12.sp,
                lineHeight = 16.sp
            )
            Spacer(modifier = Modifier.height(12.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                TaxonomyTile("UNIVERSAL", universalCount, HexnilSuccess, Modifier.weight(1f))
                TaxonomyTile("CONDITIONAL", conditionalCount, HexnilWarning, Modifier.weight(1f))
                TaxonomyTile("UNSUPPORTED", unsupportedCount, HexnilError, Modifier.weight(1f))
            }
        }
    }
}

@Composable
private fun TaxonomyTile(
    label: String,
    count: Int,
    color: androidx.compose.ui.graphics.Color,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier
            .clip(RoundedCornerShape(HexnilRadius.metadata))
            .border(1.dp, HexnilBorder, RoundedCornerShape(HexnilRadius.metadata)),
        color = HexnilSecondaryCard
    ) {
        Column(
            modifier = Modifier.padding(vertical = 8.dp, horizontal = 6.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(modifier = Modifier.size(6.dp).background(color, CircleShape))
                Spacer(modifier = Modifier.width(4.dp))
                Text(text = "$count", color = HexnilPrimaryText, fontSize = 14.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
            }
            Text(text = label, color = HexnilSecondaryText, fontSize = 9.sp, fontWeight = FontWeight.Bold)
        }
    }
}

@Composable
private fun LiveTelemetrySignalsCard(records: List<TelemetryRecord>) {
    val batteryLevel = records.find { it.metric.name == "battery_level_percent" }?.metric?.value
    val batteryState = records.find { it.metric.name == "battery_charging_state" }?.metric?.value
    val appHeap = records.find { it.metric.name == "app_heap_allocated_mb" }?.metric?.value
    val devMemAvail = records.find { it.metric.name == "device_memory_available_mb" }?.metric?.value
    val thermalStatus = records.find { it.metric.name == "thermal_status_name" }?.metric?.value
    val startupDuration = records.find { it.metric.name == "app_startup_duration_ms" }?.metric?.value

    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(HexnilRadius.card))
            .border(1.dp, HexnilBorder, RoundedCornerShape(HexnilRadius.card)),
        color = HexnilCard
    ) {
        Column(modifier = Modifier.padding(HexnilSpacing.md)) {
            val batteryText = if (batteryLevel != null) {
                val stateText = if (batteryState != null) " ($batteryState)" else ""
                "${"%.1f".format(batteryLevel)}%$stateText"
            } else {
                "No live telemetry (Capture snapshot)"
            }
            TelemetryRow(
                "Battery Level",
                batteryText,
                if (batteryLevel != null) CapabilityStatus.UNIVERSAL else CapabilityStatus.UNSUPPORTED
            )

            TelemetryRow(
                "JVM Heap Allocated",
                if (appHeap != null) "${"%.1f".format(appHeap)} MB" else "No live telemetry",
                if (appHeap != null) CapabilityStatus.UNIVERSAL else CapabilityStatus.UNSUPPORTED
            )

            TelemetryRow(
                "Device Available RAM",
                if (devMemAvail != null) "${"%.0f".format(devMemAvail)} MB free" else "No live telemetry",
                if (devMemAvail != null) CapabilityStatus.UNIVERSAL else CapabilityStatus.UNSUPPORTED
            )

            TelemetryRow(
                "Thermal Throttling State",
                thermalStatus?.toString() ?: "No live telemetry",
                if (thermalStatus != null) CapabilityStatus.UNIVERSAL else CapabilityStatus.UNSUPPORTED
            )

            TelemetryRow(
                "Cold Startup Latency",
                if (startupDuration != null) "$startupDuration ms" else "Awaiting workload run",
                if (startupDuration != null) CapabilityStatus.CONDITIONAL else CapabilityStatus.UNSUPPORTED
            )

            TelemetryRow("Raw SoC Silicon Temp", "UNSUPPORTED", CapabilityStatus.UNSUPPORTED)
        }
    }
}

@Composable
private fun TelemetryRow(
    label: String,
    value: String,
    capability: CapabilityStatus
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            val dotColor = when (capability) {
                CapabilityStatus.UNIVERSAL -> HexnilSuccess
                CapabilityStatus.CONDITIONAL -> HexnilWarning
                CapabilityStatus.UNSUPPORTED -> HexnilError
            }
            Box(modifier = Modifier.size(6.dp).background(dotColor, CircleShape))
            Spacer(modifier = Modifier.width(6.dp))
            Text(text = label, color = HexnilSecondaryText, fontSize = 12.sp)
        }

        Text(
            text = value,
            color = if (capability == CapabilityStatus.UNSUPPORTED) HexnilSecondaryText else HexnilPrimaryText,
            fontSize = 12.sp,
            fontWeight = FontWeight.Medium,
            fontFamily = FontFamily.Monospace
        )
    }
}
