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
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
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
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.iqoo_hexnil.ui.theme.HexnilAccentGlow
import com.example.iqoo_hexnil.ui.theme.HexnilBackground
import com.example.iqoo_hexnil.ui.theme.HexnilBorder
import com.example.iqoo_hexnil.ui.theme.HexnilCard
import com.example.iqoo_hexnil.ui.theme.HexnilMainAccent
import com.example.iqoo_hexnil.ui.theme.HexnilPrimaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryCard
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSuccess

data class WorkloadItem(
    val id: String,
    val name: String,
    val description: String,
    val hash: String,
    val action: String,
    val lastDurationMs: Double? = null
)

@Composable
fun WorkloadsScreen(
    onRunWorkloadAction: (String, String) -> Unit,
    modifier: Modifier = Modifier
) {
    val scrollState = rememberScrollState()
    var runningWorkloadId by remember { mutableStateOf<String?>(null) }
    var workloadResults by remember {
        mutableStateOf(
            mapOf(
                "startup_01" to 7797.4,
                "cpu_01" to 9755.4,
                "memory_01" to 9347.7,
                "scroll_01" to 10549.1,
                "video_power_01" to 12733.5
            )
        )
    }

    val workloads = listOf(
        WorkloadItem(
            id = "startup_01",
            name = "App Startup Latency",
            description = "Cold application launch, component initialization & telemetry bootstrap.",
            hash = "2e7a9b1c",
            action = "launch_app",
            lastDurationMs = workloadResults["startup_01"]
        ),
        WorkloadItem(
            id = "cpu_01",
            name = "CPU Matrix Compute",
            description = "Deterministic integer matrix math stress and throughput benchmark.",
            hash = "5f8c3d2a",
            action = "compute_work",
            lastDurationMs = workloadResults["cpu_01"]
        ),
        WorkloadItem(
            id = "memory_01",
            name = "Memory Churn & GC Stress",
            description = "Sequential byte buffer allocation, heap expansion and garbage collection.",
            hash = "8b1a4e7f",
            action = "memory_work",
            lastDurationMs = workloadResults["memory_01"]
        ),
        WorkloadItem(
            id = "scroll_01",
            name = "UI Scroll & Frame Jank",
            description = "Continuous list fling scrolling, frame timing and rendering jank detection.",
            hash = "1c4d9e2a",
            action = "scroll",
            lastDurationMs = workloadResults["scroll_01"]
        ),
        WorkloadItem(
            id = "video_power_01",
            name = "Media Playback & Battery",
            description = "1080p hardware codec decoding and power discharge proxy measurement.",
            hash = "7a3b8c1d",
            action = "local_media_playback",
            lastDurationMs = workloadResults["video_power_01"]
        )
    )

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(HexnilBackground)
            .padding(horizontal = 20.dp, vertical = 12.dp)
            .verticalScroll(scrollState),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        // Header
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(12.dp))
                .border(1.dp, HexnilBorder, RoundedCornerShape(12.dp)),
            color = HexnilCard
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text(
                    text = "DETERMINISTIC WORKLOAD ENGINE",
                    color = HexnilMainAccent,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = "5 Locked declarative workloads enforcing reproducible release validation.",
                    color = HexnilSecondaryText,
                    fontSize = 12.sp
                )
            }
        }

        // Workload Cards
        workloads.forEach { item ->
            WorkloadCard(
                item = item,
                isRunning = runningWorkloadId == item.id,
                onRun = {
                    runningWorkloadId = item.id
                    onRunWorkloadAction(item.id, item.action)
                    // Update state simulation
                    workloadResults = workloadResults + (item.id to (item.lastDurationMs ?: 5000.0))
                    runningWorkloadId = null
                }
            )
        }

        Spacer(modifier = Modifier.height(16.dp))
    }
}

@Composable
fun WorkloadCard(
    item: WorkloadItem,
    isRunning: Boolean,
    onRun: () -> Unit
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
                    text = item.id,
                    color = HexnilMainAccent,
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace
                )
                Surface(
                    shape = RoundedCornerShape(4.dp),
                    color = HexnilSecondaryCard,
                    border = androidx.compose.foundation.BorderStroke(1.dp, HexnilBorder)
                ) {
                    Text(
                        text = "Hash: #${item.hash}",
                        color = HexnilAccentGlow,
                        fontSize = 10.sp,
                        fontFamily = FontFamily.Monospace,
                        modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                    )
                }
            }

            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = item.name,
                color = HexnilPrimaryText,
                fontSize = 14.sp,
                fontWeight = FontWeight.SemiBold
            )
            Spacer(modifier = Modifier.height(2.dp))
            Text(
                text = item.description,
                color = HexnilSecondaryText,
                fontSize = 12.sp,
                lineHeight = 16.sp
            )

            Spacer(modifier = Modifier.height(10.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(text = "LAST MEASURED", color = HexnilSecondaryText, fontSize = 9.sp, fontWeight = FontWeight.Bold)
                    Text(
                        text = if (item.lastDurationMs != null) "${"%.1f".format(item.lastDurationMs)} ms" else "Not Run",
                        color = HexnilSuccess,
                        fontSize = 13.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                }

                Button(
                    onClick = onRun,
                    enabled = !isRunning,
                    colors = ButtonDefaults.buttonColors(
                        containerColor = HexnilSecondaryCard,
                        contentColor = HexnilMainAccent
                    ),
                    border = androidx.compose.foundation.BorderStroke(1.dp, HexnilMainAccent),
                    shape = RoundedCornerShape(6.dp)
                ) {
                    Text(
                        text = if (isRunning) "Running..." else "Execute ➔",
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
            }
        }
    }
}
