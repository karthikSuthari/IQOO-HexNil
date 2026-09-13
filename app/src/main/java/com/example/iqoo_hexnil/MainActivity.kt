package com.example.iqoo_hexnil

import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.os.SystemClock
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
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
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.iqoo_hexnil.telemetry.CapabilityStatus
import com.example.iqoo_hexnil.telemetry.TelemetryEngine
import com.example.iqoo_hexnil.telemetry.TelemetryRecord
import com.example.iqoo_hexnil.ui.theme.HexnilAccentGlow
import com.example.iqoo_hexnil.ui.theme.HexnilBackground
import com.example.iqoo_hexnil.ui.theme.HexnilBorder
import com.example.iqoo_hexnil.ui.theme.HexnilCard
import com.example.iqoo_hexnil.ui.theme.HexnilError
import com.example.iqoo_hexnil.ui.theme.HexnilMainAccent
import com.example.iqoo_hexnil.ui.theme.HexnilPrimaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryCard
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSuccess
import com.example.iqoo_hexnil.ui.theme.HexnilWarning
import com.example.iqoo_hexnil.ui.theme.IQOOHEXNILTheme

class MainActivity : ComponentActivity() {

    private val activityCreateTime = SystemClock.elapsedRealtime()
    private var pendingExperimentId: String? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        handleIncomingIntent(intent)

        setContent {
            IQOOHEXNILTheme {
                Scaffold(
                    modifier = Modifier.fillMaxSize(),
                    containerColor = HexnilBackground
                ) { innerPadding ->
                    HexnilCompanionScreen(
                        activityCreateTime = activityCreateTime,
                        initialExperimentId = pendingExperimentId,
                        onRunWorkload = { expId ->
                            TelemetryEngine.executeSession(
                                context = this@MainActivity,
                                experimentId = expId,
                                workloadId = "startup_basic"
                            )
                        },
                        modifier = Modifier.padding(innerPadding)
                    )
                }
            }
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        handleIncomingIntent(intent)
    }

    private fun handleIncomingIntent(intent: Intent?) {
        if (intent != null && intent.action == "com.example.iqoo_hexnil.ACTION_RUN_WORKLOAD") {
            pendingExperimentId = intent.getStringExtra("experiment_id")
            val workloadId = intent.getStringExtra("workload_id") ?: "startup_basic"
            val iteration = intent.getIntExtra("iteration", 1)
            val action = intent.getStringExtra("workload_action") ?: "compute_work"
            val operations = intent.getIntExtra("operations_count", 5000)
            val expId = pendingExperimentId ?: "EXP-LOCAL-001"
            TelemetryEngine.executeSession(
                context = this,
                experimentId = expId,
                workloadId = workloadId,
                iteration = iteration,
                action = action,
                operations = operations
            )
        }
    }
}

@Composable
fun HexnilCompanionScreen(
    activityCreateTime: Long,
    initialExperimentId: String?,
    onRunWorkload: (String) -> List<TelemetryRecord>,
    modifier: Modifier = Modifier
) {
    val scrollState = rememberScrollState()
    var currentExperimentId by remember {
        mutableStateOf(initialExperimentId ?: "EXP-READY-001")
    }
    var telemetryRecords by remember { mutableStateOf<List<TelemetryRecord>>(emptyList()) }
    var isRunning by remember { mutableStateOf(false) }

    // Measure startup time on first launch
    LaunchedEffect(Unit) {
        val startupDuration = SystemClock.elapsedRealtime() - activityCreateTime
        TelemetryEngine.lastStartupDurationMs = startupDuration
        // Run initial telemetry baseline
        telemetryRecords = onRunWorkload(currentExperimentId)
    }

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(HexnilBackground)
            .padding(horizontal = 20.dp, vertical = 16.dp)
            .verticalScroll(scrollState),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // App Header
        Row(
            verticalAlignment = Alignment.CenterVertically,
            modifier = Modifier.fillMaxWidth()
        ) {
            Image(
                painter = painterResource(id = R.drawable.hexnil_logo),
                contentDescription = "Hexnil Logo",
                modifier = Modifier
                    .size(46.dp)
                    .clip(RoundedCornerShape(10.dp))
                    .border(1.dp, HexnilBorder, RoundedCornerShape(10.dp))
            )
            Spacer(modifier = Modifier.width(12.dp))
            Column {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = "HEXNIL",
                        fontSize = 22.sp,
                        fontWeight = FontWeight.Black,
                        color = HexnilMainAccent,
                        letterSpacing = 2.sp
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Surface(
                        shape = RoundedCornerShape(4.dp),
                        color = HexnilSecondaryCard,
                        border = BorderStroke(1.dp, HexnilBorder)
                    ) {
                        Text(
                            text = "v1.1",
                            color = HexnilAccentGlow,
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                        )
                    }
                }
                Spacer(modifier = Modifier.height(2.dp))
                Text(
                    text = "Universal Telemetry Collection",
                    color = HexnilSecondaryText,
                    fontSize = 12.sp
                )
            }
        }

        // Status Card
        StatusCard(
            experimentId = currentExperimentId,
            recordsCount = telemetryRecords.size
        )

        // Telemetry Evidence Card
        TelemetryEvidenceCard(
            records = telemetryRecords,
            isRunning = isRunning,
            onExecuteWorkload = {
                isRunning = true
                val newRecords = onRunWorkload(currentExperimentId)
                telemetryRecords = newRecords
                isRunning = false
            }
        )

        // Device Properties Card
        DevicePropertiesCard()

        // Architecture Boundary Note Card
        ArchitectureCard()

        Spacer(modifier = Modifier.height(16.dp))
    }
}

@Composable
fun StatusCard(experimentId: String, recordsCount: Int) {
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
                    text = "Telemetry Engine Active",
                    color = HexnilPrimaryText,
                    fontSize = 15.sp,
                    fontWeight = FontWeight.SemiBold
                )
                Text(
                    text = "Session: $experimentId ($recordsCount records buffered)",
                    color = HexnilSecondaryText,
                    fontSize = 12.sp
                )
            }
        }
    }
}

@Composable
fun TelemetryEvidenceCard(
    records: List<TelemetryRecord>,
    isRunning: Boolean,
    onExecuteWorkload: () -> Unit
) {
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
                    text = "ON-DEVICE TELEMETRY EVIDENCE",
                    color = HexnilMainAccent,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp
                )

                // Capability counts
                val universal = records.count { it.capability == CapabilityStatus.UNIVERSAL }
                val conditional = records.count { it.capability == CapabilityStatus.CONDITIONAL }
                val unsupported = records.count { it.capability == CapabilityStatus.UNSUPPORTED }

                Text(
                    text = "${universal}U · ${conditional}C · ${unsupported}X",
                    color = HexnilSecondaryText,
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace
                )
            }

            Spacer(modifier = Modifier.height(14.dp))

            // Dynamic Metric Summaries extracted from real telemetry
            val batteryLevel = records.find { it.metric.name == "battery_level_percent" }?.metric?.value
            val batteryState = records.find { it.metric.name == "battery_charging_state" }?.metric?.value ?: "UNKNOWN"
            val appHeap = records.find { it.metric.name == "app_heap_allocated_mb" }?.metric?.value
            val devMemAvail = records.find { it.metric.name == "device_memory_available_mb" }?.metric?.value
            val thermalStatus = records.find { it.metric.name == "thermal_status_name" }?.metric?.value ?: "NORMAL"
            val workloadDuration = records.find { it.metric.name == "workload_duration_ms" }?.metric?.value
            val startupDuration = records.find { it.metric.name == "app_startup_duration_ms" }?.metric?.value

            TelemetryMetricRow(
                label = "Battery Proxy",
                value = if (batteryLevel != null) "${"%.1f".format(batteryLevel)}% ($batteryState)" else "Unavailable",
                capability = CapabilityStatus.UNIVERSAL
            )
            TelemetryMetricRow(
                label = "App Heap Memory",
                value = if (appHeap != null) "${"%.1f".format(appHeap)} MB" else "Unavailable",
                capability = CapabilityStatus.UNIVERSAL
            )
            TelemetryMetricRow(
                label = "Device Available RAM",
                value = if (devMemAvail != null) "${"%.0f".format(devMemAvail)} MB free" else "Unavailable",
                capability = CapabilityStatus.UNIVERSAL
            )
            TelemetryMetricRow(
                label = "Thermal Status",
                value = thermalStatus.toString(),
                capability = CapabilityStatus.UNIVERSAL
            )
            TelemetryMetricRow(
                label = "Workload Duration",
                value = if (workloadDuration != null) "$workloadDuration ms" else "Not executed",
                capability = CapabilityStatus.UNIVERSAL
            )
            TelemetryMetricRow(
                label = "App Startup Time",
                value = if (startupDuration != null) "$startupDuration ms" else "Baseline",
                capability = CapabilityStatus.CONDITIONAL
            )
            TelemetryMetricRow(
                label = "SoC Silicon Temp",
                value = "UNSUPPORTED",
                capability = CapabilityStatus.UNSUPPORTED
            )

            Spacer(modifier = Modifier.height(14.dp))

            // Workload Trigger Button
            Button(
                onClick = onExecuteWorkload,
                enabled = !isRunning,
                colors = ButtonDefaults.buttonColors(
                    containerColor = HexnilMainAccent,
                    contentColor = HexnilPrimaryText
                ),
                shape = RoundedCornerShape(8.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Text(
                    text = if (isRunning) "Executing Workload..." else "Execute Workload & Collect Telemetry",
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Bold
                )
            }
        }
    }
}

@Composable
fun TelemetryMetricRow(
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
            val badgeColor = when (capability) {
                CapabilityStatus.UNIVERSAL -> HexnilSuccess
                CapabilityStatus.CONDITIONAL -> HexnilWarning
                CapabilityStatus.UNSUPPORTED -> HexnilError
            }
            Box(
                modifier = Modifier
                    .size(6.dp)
                    .background(badgeColor, CircleShape)
            )
            Spacer(modifier = Modifier.width(8.dp))
            Text(
                text = label,
                color = HexnilSecondaryText,
                fontSize = 13.sp
            )
        }
        Text(
            text = value,
            color = if (capability == CapabilityStatus.UNSUPPORTED) HexnilSecondaryText else HexnilPrimaryText,
            fontSize = 13.sp,
            fontWeight = FontWeight.Medium,
            fontFamily = if (capability == CapabilityStatus.UNSUPPORTED) FontFamily.Monospace else FontFamily.Default
        )
    }
}

@Composable
fun DevicePropertiesCard() {
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

            PropertyRow("Manufacturer", Build.MANUFACTURER)
            PropertyRow("Model", Build.MODEL)
            PropertyRow("Device Codename", Build.DEVICE)
            PropertyRow("Android Release", Build.VERSION.RELEASE)
            PropertyRow("API / SDK Level", Build.VERSION.SDK_INT.toString())
            PropertyRow("Build ID", Build.ID)
            PropertyRow("ABI Architecture", Build.SUPPORTED_ABIS.firstOrNull() ?: "Unknown")

            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = "FINGERPRINT",
                color = HexnilSecondaryText,
                fontSize = 10.sp,
                fontWeight = FontWeight.Bold
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = Build.FINGERPRINT,
                color = HexnilPrimaryText,
                fontSize = 10.sp,
                fontFamily = FontFamily.Monospace,
                lineHeight = 14.sp,
                modifier = Modifier
                    .fillMaxWidth()
                    .background(HexnilSecondaryCard, RoundedCornerShape(6.dp))
                    .padding(8.dp)
            )
        }
    }
}

@Composable
fun PropertyRow(label: String, value: String) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 5.dp),
        horizontalArrangement = Arrangement.SpaceBetween
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
fun ArchitectureCard() {
    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .border(1.dp, HexnilBorder, RoundedCornerShape(12.dp)),
        color = HexnilSecondaryCard
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                text = "HOST-DEVICE ARCHITECTURE",
                color = HexnilSecondaryText,
                fontSize = 11.sp,
                fontWeight = FontWeight.Bold,
                letterSpacing = 1.sp
            )
            Spacer(modifier = Modifier.height(6.dp))
            Text(
                text = "ADB strictly belongs to the host controller machine. The on-device companion serves as the target runtime for later validation phases.",
                color = HexnilPrimaryText,
                fontSize = 12.sp,
                lineHeight = 18.sp
            )
        }
    }
}