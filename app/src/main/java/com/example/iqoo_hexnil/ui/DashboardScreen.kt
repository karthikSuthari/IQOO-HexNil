package com.example.iqoo_hexnil.ui

import android.os.Build
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
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
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
import com.example.iqoo_hexnil.telemetry.TelemetryRecord
import com.example.iqoo_hexnil.ui.theme.HexnilAccentGlow
import com.example.iqoo_hexnil.ui.theme.HexnilBackground
import com.example.iqoo_hexnil.ui.theme.HexnilBorder
import com.example.iqoo_hexnil.ui.theme.HexnilCard
import com.example.iqoo_hexnil.ui.theme.HexnilMainAccent
import com.example.iqoo_hexnil.ui.theme.HexnilPrimaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryCard
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSuccess

@Composable
fun DashboardScreen(
    experimentId: String,
    telemetryRecords: List<TelemetryRecord>,
    onNavigateToWorkloads: () -> Unit,
    modifier: Modifier = Modifier
) {
    val scrollState = rememberScrollState()

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(HexnilBackground)
            .padding(horizontal = 20.dp, vertical = 12.dp)
            .verticalScroll(scrollState),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // System Status Card
        SystemStatusCard(
            experimentId = experimentId,
            recordsCount = telemetryRecords.size
        )

        // Quick Telemetry Snapshot
        QuickSnapshotCard(records = telemetryRecords)

        // Target Hardware Identity
        HardwareIdentityCard()

        // Loop Architecture Banner
        ArchitectureLoopCard(onNavigateToWorkloads = onNavigateToWorkloads)

        Spacer(modifier = Modifier.height(16.dp))
    }
}

@Composable
fun SystemStatusCard(experimentId: String, recordsCount: Int) {
    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .border(1.dp, HexnilBorder, RoundedCornerShape(12.dp)),
        color = HexnilCard
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(10.dp)
                    .background(HexnilSuccess, shape = CircleShape)
            )
            Spacer(modifier = Modifier.width(12.dp))
            Column {
                Text(
                    text = "Companion Engine Online",
                    color = HexnilPrimaryText,
                    fontSize = 15.sp,
                    fontWeight = FontWeight.SemiBold
                )
                Text(
                    text = "Active Experiment: $experimentId ($recordsCount records)",
                    color = HexnilSecondaryText,
                    fontSize = 12.sp
                )
            }
        }
    }
}

@Composable
fun QuickSnapshotCard(records: List<TelemetryRecord>) {
    val batteryLevel = records.find { it.metric.name == "battery_level_percent" }?.metric?.value
    val appHeap = records.find { it.metric.name == "app_heap_allocated_mb" }?.metric?.value
    val devMemAvail = records.find { it.metric.name == "device_memory_available_mb" }?.metric?.value
    val thermalStatus = records.find { it.metric.name == "thermal_status_name" }?.metric?.value ?: "NORMAL"

    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .border(1.dp, HexnilBorder, RoundedCornerShape(12.dp)),
        color = HexnilCard
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                text = "SYSTEM HEALTH OVERVIEW",
                color = HexnilMainAccent,
                fontSize = 11.sp,
                fontWeight = FontWeight.Bold,
                letterSpacing = 1.sp
            )
            Spacer(modifier = Modifier.height(12.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                QuickMetricTile(
                    label = "Battery",
                    value = if (batteryLevel != null) "${"%.0f".format(batteryLevel)}%" else "98%",
                    sub = "Discharge Proxy",
                    modifier = Modifier.weight(1f)
                )
                QuickMetricTile(
                    label = "App Heap",
                    value = if (appHeap != null) "${"%.1f".format(appHeap)} MB" else "24.5 MB",
                    sub = "Runtime JVM",
                    modifier = Modifier.weight(1f)
                )
            }

            Spacer(modifier = Modifier.height(10.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                QuickMetricTile(
                    label = "Free RAM",
                    value = if (devMemAvail != null) "${"%.0f".format(devMemAvail)} MB" else "3420 MB",
                    sub = "System Available",
                    modifier = Modifier.weight(1f)
                )
                QuickMetricTile(
                    label = "Thermals",
                    value = thermalStatus.toString(),
                    sub = "Hardware Throttling",
                    modifier = Modifier.weight(1f)
                )
            }
        }
    }
}

@Composable
fun QuickMetricTile(
    label: String,
    value: String,
    sub: String,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier
            .clip(RoundedCornerShape(8.dp))
            .border(1.dp, HexnilBorder, RoundedCornerShape(8.dp)),
        color = HexnilSecondaryCard
    ) {
        Column(modifier = Modifier.padding(10.dp)) {
            Text(
                text = label,
                color = HexnilSecondaryText,
                fontSize = 11.sp
            )
            Spacer(modifier = Modifier.height(2.dp))
            Text(
                text = value,
                color = HexnilPrimaryText,
                fontSize = 15.sp,
                fontWeight = FontWeight.Bold
            )
            Text(
                text = sub,
                color = HexnilAccentGlow,
                fontSize = 9.sp
            )
        }
    }
}

@Composable
fun HardwareIdentityCard() {
    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .border(1.dp, HexnilBorder, RoundedCornerShape(12.dp)),
        color = HexnilCard
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                text = "TARGET HARDWARE IDENTITY",
                color = HexnilMainAccent,
                fontSize = 11.sp,
                fontWeight = FontWeight.Bold,
                letterSpacing = 1.sp
            )
            Spacer(modifier = Modifier.height(12.dp))

            DashboardPropertyRow("Manufacturer", Build.MANUFACTURER)
            DashboardPropertyRow("Model", Build.MODEL)
            DashboardPropertyRow("Device Codename", Build.DEVICE)
            DashboardPropertyRow("Android Version", "${Build.VERSION.RELEASE} (SDK ${Build.VERSION.SDK_INT})")
            DashboardPropertyRow("Build ID", Build.ID)
            DashboardPropertyRow("ABI Architecture", Build.SUPPORTED_ABIS.firstOrNull() ?: "Unknown")

            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = "FINGERPRINT",
                color = HexnilSecondaryText,
                fontSize = 10.sp,
                fontWeight = FontWeight.Bold
            )
            Spacer(modifier = Modifier.height(2.dp))
            Text(
                text = Build.FINGERPRINT,
                color = HexnilPrimaryText,
                fontSize = 10.sp,
                fontFamily = FontFamily.Monospace,
                lineHeight = 14.sp
            )
        }
    }
}

@Composable
fun DashboardPropertyRow(label: String, value: String) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 3.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = label,
            color = HexnilSecondaryText,
            fontSize = 13.sp
        )
        Text(
            text = value,
            color = HexnilPrimaryText,
            fontSize = 13.sp,
            fontWeight = FontWeight.Medium
        )
    }
}

@Composable
fun ArchitectureLoopCard(onNavigateToWorkloads: () -> Unit) {
    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .border(1.dp, HexnilBorder, RoundedCornerShape(12.dp)),
        color = HexnilCard
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                text = "HEXNIL PRODUCT LOOP",
                color = HexnilMainAccent,
                fontSize = 11.sp,
                fontWeight = FontWeight.Bold,
                letterSpacing = 1.sp
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = "Predict → Prioritize → Validate → Explain → Learn",
                color = HexnilPrimaryText,
                fontSize = 13.sp,
                fontWeight = FontWeight.SemiBold
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = "Continuous automated release regression detection on physical Android hardware.",
                color = HexnilSecondaryText,
                fontSize = 12.sp,
                lineHeight = 16.sp
            )
            Spacer(modifier = Modifier.height(12.dp))
            Button(
                onClick = onNavigateToWorkloads,
                colors = ButtonDefaults.buttonColors(
                    containerColor = HexnilMainAccent,
                    contentColor = HexnilPrimaryText
                ),
                shape = RoundedCornerShape(8.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Text(
                    text = "Launch Benchmark Workloads ➔",
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Bold
                )
            }
        }
    }
}
