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
import android.Manifest
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.PowerManager
import android.provider.Settings
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.clickable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.style.TextAlign
import com.example.iqoo_hexnil.data.DeviceHardwareInfo
import com.example.iqoo_hexnil.service.HexnilBackgroundService
import com.example.iqoo_hexnil.telemetry.CapabilityStatus
import com.example.iqoo_hexnil.telemetry.TelemetryRecord
import com.example.iqoo_hexnil.ui.components.BuildIdentityCard
import com.example.iqoo_hexnil.ui.components.DeviceCard
import com.example.iqoo_hexnil.ui.components.HexnilPrimaryButton
import com.example.iqoo_hexnil.ui.components.SectionHeader
import com.example.iqoo_hexnil.ui.theme.HexnilAccentGlow
import com.example.iqoo_hexnil.ui.theme.HexnilAccentSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilBackground
import com.example.iqoo_hexnil.ui.theme.HexnilBorder
import com.example.iqoo_hexnil.ui.theme.HexnilBorderSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilCard
import com.example.iqoo_hexnil.ui.theme.HexnilError
import com.example.iqoo_hexnil.ui.theme.HexnilMainAccent
import com.example.iqoo_hexnil.ui.theme.HexnilPrimaryText
import com.example.iqoo_hexnil.ui.theme.HexnilRadius
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryCard
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSpacing
import com.example.iqoo_hexnil.ui.theme.HexnilSuccess
import com.example.iqoo_hexnil.ui.theme.HexnilSuccessSubtle
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
            .padding(horizontal = HexnilSpacing.screenHorizontal, vertical = HexnilSpacing.screenVertical)
            .verticalScroll(scrollState),
        verticalArrangement = Arrangement.spacedBy(HexnilSpacing.sectionSpacing)
    ) {
        // Target Hardware State Card
        DeviceCard(device = device)

        // Background Execution Control Card
        BackgroundServiceControlCard()

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

        Spacer(modifier = Modifier.height(24.dp))
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
        Column(modifier = Modifier.padding(HexnilSpacing.cardPadding)) {
            Text(
                text = "CAPABILITY-AWARE TAXONOMY (PHASE 2)",
                color = HexnilMainAccent,
                fontSize = 12.sp,
                fontWeight = FontWeight.Bold,
                letterSpacing = 1.sp
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = "Subsystems strictly distinguish universal OS APIs from conditional device sensors without data fabrication.",
                color = HexnilSecondaryText,
                fontSize = 13.sp,
                lineHeight = 19.sp
            )
            Spacer(modifier = Modifier.height(14.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(10.dp)
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
            .clip(RoundedCornerShape(HexnilRadius.md))
            .border(1.dp, HexnilBorder, RoundedCornerShape(HexnilRadius.md)),
        color = HexnilSecondaryCard
    ) {
        Column(
            modifier = Modifier.padding(vertical = 12.dp, horizontal = 8.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(modifier = Modifier.size(8.dp).background(color, CircleShape))
                Spacer(modifier = Modifier.width(6.dp))
                Text(
                    text = "$count",
                    color = HexnilPrimaryText,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace
                )
            }
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = label,
                color = HexnilSecondaryText,
                fontSize = 11.sp,
                fontWeight = FontWeight.Bold
            )
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
        Column(modifier = Modifier.padding(HexnilSpacing.cardPadding)) {
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
            .padding(vertical = 7.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            val dotColor = when (capability) {
                CapabilityStatus.UNIVERSAL -> HexnilSuccess
                CapabilityStatus.CONDITIONAL -> HexnilWarning
                CapabilityStatus.UNSUPPORTED -> HexnilError
            }
            Box(modifier = Modifier.size(8.dp).background(dotColor, CircleShape))
            Spacer(modifier = Modifier.width(8.dp))
            Text(text = label, color = HexnilSecondaryText, fontSize = 13.sp)
        }

        Text(
            text = value,
            color = if (capability == CapabilityStatus.UNSUPPORTED) HexnilSecondaryText else HexnilPrimaryText,
            fontSize = 13.sp,
            fontWeight = FontWeight.Medium,
            fontFamily = FontFamily.Monospace
        )
    }
}

@Composable
private fun BackgroundServiceControlCard() {
    val context = LocalContext.current
    val isRunning = HexnilBackgroundService.isRunning.value
    val sampleCount = HexnilBackgroundService.sampleCount.value
    val lastTime = HexnilBackgroundService.lastSampleTime.value
    val lastBattery = HexnilBackgroundService.lastBatteryText.value
    val lastMemory = HexnilBackgroundService.lastMemoryText.value

    val permissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission()
    ) { isGranted ->
        if (isGranted) {
            HexnilBackgroundService.start(context)
        }
    }

    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(HexnilRadius.card))
            .border(
                1.dp,
                if (isRunning) HexnilSuccess.copy(alpha = 0.6f) else HexnilBorder,
                RoundedCornerShape(HexnilRadius.card)
            ),
        color = HexnilCard
    ) {
        Column(modifier = Modifier.padding(HexnilSpacing.cardPadding)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "BACKGROUND SERVICE (DAEMON)",
                    color = if (isRunning) HexnilSuccess else HexnilMainAccent,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp
                )
                Surface(
                    shape = RoundedCornerShape(HexnilRadius.pill),
                    color = if (isRunning) HexnilSuccessSubtle else HexnilSecondaryCard,
                    border = BorderStroke(1.dp, if (isRunning) HexnilSuccess else HexnilBorderSubtle)
                ) {
                    Row(
                        modifier = Modifier.padding(horizontal = 9.dp, vertical = 4.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(6.dp)
                    ) {
                        Box(
                            modifier = Modifier
                                .size(7.dp)
                                .clip(CircleShape)
                                .background(if (isRunning) HexnilSuccess else HexnilSecondaryText)
                        )
                        Text(
                            text = if (isRunning) "ACTIVE IN BG" else "STANDBY",
                            color = if (isRunning) HexnilSuccess else HexnilSecondaryText,
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                text = "Continuous Background Monitoring",
                color = HexnilPrimaryText,
                fontSize = 17.sp,
                fontWeight = FontWeight.Bold
            )

            Spacer(modifier = Modifier.height(4.dp))

            Text(
                text = "Samples physical hardware telemetry every 15s in the background so Hexnil keeps monitoring while you use other apps or turn the screen off.",
                color = HexnilSecondaryText,
                fontSize = 13.sp,
                lineHeight = 19.sp
            )

            Spacer(modifier = Modifier.height(14.dp))

            // Stats Sub-container
            Surface(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(HexnilRadius.md),
                color = HexnilSecondaryCard,
                border = BorderStroke(1.dp, HexnilBorderSubtle)
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 14.dp, vertical = 12.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column {
                        Text(
                            text = "SAMPLES COLLECTED",
                            color = HexnilSecondaryText,
                            fontSize = 10.sp,
                            fontWeight = FontWeight.Bold,
                            letterSpacing = 0.8.sp
                        )
                        Spacer(modifier = Modifier.height(3.dp))
                        Text(
                            text = "$sampleCount",
                            color = if (isRunning) HexnilSuccess else HexnilPrimaryText,
                            fontSize = 22.sp,
                            fontWeight = FontWeight.Black,
                            fontFamily = FontFamily.Monospace
                        )
                    }

                    Column(horizontalAlignment = Alignment.End) {
                        Text(
                            text = "LAST SAMPLE TIME",
                            color = HexnilSecondaryText,
                            fontSize = 10.sp,
                            fontWeight = FontWeight.Bold,
                            letterSpacing = 0.8.sp
                        )
                        Spacer(modifier = Modifier.height(3.dp))
                        Text(
                            text = lastTime ?: "Not Started",
                            color = if (lastTime != null) HexnilAccentGlow else HexnilSecondaryText,
                            fontSize = 14.sp,
                            fontFamily = FontFamily.Monospace,
                            fontWeight = FontWeight.SemiBold
                        )
                    }
                }
            }

            if (isRunning && lastBattery != null) {
                Spacer(modifier = Modifier.height(10.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(
                        text = "Battery: $lastBattery",
                        color = HexnilSecondaryText,
                        fontSize = 12.sp,
                        fontFamily = FontFamily.Monospace
                    )
                    Text(
                        text = "RAM: ${lastMemory ?: "N/A"}",
                        color = HexnilSecondaryText,
                        fontSize = 12.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }

            Spacer(modifier = Modifier.height(14.dp))

            // Action Button
            Surface(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(HexnilRadius.md))
                    .clickable {
                        if (isRunning) {
                            HexnilBackgroundService.stop(context)
                        } else {
                            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                                permissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
                            } else {
                                HexnilBackgroundService.start(context)
                            }
                        }
                    },
                color = if (isRunning) HexnilError.copy(alpha = 0.15f) else HexnilMainAccent,
                border = BorderStroke(1.dp, if (isRunning) HexnilError else HexnilMainAccent)
            ) {
                Text(
                    text = if (isRunning) "Stop Background Service" else "Enable Background Service ➔",
                    color = if (isRunning) HexnilError else HexnilPrimaryText,
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.padding(vertical = 12.dp),
                    textAlign = TextAlign.Center
                )
            }

            // Battery Optimization / OEM Whitelist Exemption Banner
            val powerManager = remember { context.getSystemService(Context.POWER_SERVICE) as? PowerManager }
            var isIgnoringBatteryOptimizations by remember {
                mutableStateOf(powerManager?.isIgnoringBatteryOptimizations(context.packageName) ?: false)
            }

            if (!isIgnoringBatteryOptimizations) {
                Spacer(modifier = Modifier.height(12.dp))
                Surface(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(HexnilRadius.md))
                        .clickable {
                            try {
                                val intent = Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS).apply {
                                    data = Uri.parse("package:${context.packageName}")
                                }
                                context.startActivity(intent)
                            } catch (e: Exception) {
                                try {
                                    val intent = Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS)
                                    context.startActivity(intent)
                                } catch (_: Exception) {}
                            }
                        },
                    shape = RoundedCornerShape(HexnilRadius.md),
                    color = HexnilWarning.copy(alpha = 0.10f),
                    border = BorderStroke(1.dp, HexnilWarning.copy(alpha = 0.40f))
                ) {
                    Row(
                        modifier = Modifier.padding(horizontal = 12.dp, vertical = 10.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Box(
                            modifier = Modifier
                                .size(8.dp)
                                .clip(CircleShape)
                                .background(HexnilWarning)
                        )
                        Spacer(modifier = Modifier.width(10.dp))
                        Column(modifier = Modifier.weight(1f)) {
                            Text(
                                text = "VIVO BATTERY RESTRICTION",
                                color = HexnilWarning,
                                fontSize = 10.sp,
                                fontWeight = FontWeight.Bold,
                                letterSpacing = 0.8.sp
                            )
                            Spacer(modifier = Modifier.height(2.dp))
                            Text(
                                text = "Exempt Hexnil so FuntouchOS never freezes the background daemon when the screen is locked.",
                                color = HexnilSecondaryText,
                                fontSize = 11.sp,
                                lineHeight = 15.sp
                            )
                        }
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = "EXEMPT ➔",
                            color = HexnilWarning,
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
            } else {
                Spacer(modifier = Modifier.height(10.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Box(modifier = Modifier.size(6.dp).clip(CircleShape).background(HexnilSuccess))
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        text = "Battery Optimization: Unrestricted (Will not be killed by OS)",
                        color = HexnilSuccess,
                        fontSize = 11.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }
        }
    }
}

